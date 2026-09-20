"""Fail-closed pre-tool policy composition for the fork hook contract."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional

from hermes_cli.plugins_dispatch import _HOOK_SKIPPED, _hook_uses_callback_timeout

logger = logging.getLogger("hermes_cli.plugins")

_POLICY_MALFORMED = "BLOCKED: malformed pre_tool_call decision"
_POLICY_FAILED = "BLOCKED: pre_tool_call decision failed"
_POLICY_STALE = "BLOCKED: stale pre_tool_call policy result"
_POLICY_NONCE = "BLOCKED: pre_tool_call execution identity unavailable"
_POLICY_ARGS = "BLOCKED: pre_tool_call arguments were not valid JSON"
_POLICY_APPROVAL = "BLOCKED: plugin approval could not be completed"


@dataclass(frozen=True, slots=True)
class ToolPolicyBinding:
    """Host-owned identity of the exact call approved by the policy chain."""

    tool_name: str
    args_digest: str
    execution_nonce: str
    registration_generation: int

    def verify(self, manager: Any, tool_name: str, args: Mapping[str, Any]) -> bool:
        if tool_name != self.tool_name:
            return False
        if manager.get_hook_registration_generation("pre_tool_call") != self.registration_generation:
            return False
        digest = canonical_args_digest(args)
        return digest is not None and digest == self.args_digest


@dataclass(frozen=True, slots=True)
class ToolPolicyResult:
    block_message: Optional[str]
    args: dict[str, Any]
    binding: Optional[ToolPolicyBinding]


def canonical_args_digest(args: Mapping[str, Any]) -> Optional[str]:
    try:
        encoded = json.dumps(
            args, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _static_message(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()[:500]
    return fallback


def _phase_callbacks(manager: Any) -> tuple[tuple[Callable, str], ...]:
    method = getattr(manager, "iter_hook_callbacks_with_phase", None)
    if not callable(method):
        return ()
    result = method("pre_tool_call")
    if not isinstance(result, (list, tuple)):
        raise TypeError("pre_tool_call phase registry returned a non-sequence")
    return tuple(result)


def has_decision_phase(manager: Any) -> bool:
    try:
        return any(phase == "decision" for _callback, phase in _phase_callbacks(manager))
    except Exception:
        # An unavailable policy registry must take the fail-closed path.
        return True


def _thread_whitelist_block(plugins_module: Any, tool_name: str) -> Optional[str]:
    whitelist = getattr(plugins_module, "_thread_tool_whitelist", None)
    allowed = getattr(whitelist, "allowed", None)
    if allowed is None or tool_name in allowed:
        return None
    fmt = getattr(whitelist, "fmt", "Tool '{tool_name}' denied")
    try:
        return _static_message(fmt.format(tool_name=tool_name), f"Tool '{tool_name}' denied")
    except Exception:
        return f"Tool '{tool_name}' denied"


def _invoke_policy_callback(manager: Any, callback: Callable, payload: dict[str, Any]) -> tuple[Any, str]:
    """Return ``(value, status)`` where status is ``ok``, ``timeout`` or ``error``."""
    try:
        from hermes_cli import plugins as plugins_module
        timeout = plugins_module._resolve_hook_callback_timeout()
        if _hook_uses_callback_timeout("pre_tool_call", timeout):
            value = manager._run_hook_callback_bounded("pre_tool_call", callback, payload, timeout)
            if value is _HOOK_SKIPPED:
                return None, "timeout"
        else:
            value = manager._invoke_hook_callback(callback, payload)
        return value, "ok"
    except Exception:
        return None, "error"


def _approval(
    tool_name: str, *, binding: ToolPolicyBinding, hook_kwargs: Mapping[str, Any]
) -> Optional[str]:
    """Resolve native approval once; all local binding material stays out of the reason text."""
    try:
        from tools.approval import request_tool_approval
        from tools.approval_context import (
            reset_current_observability_context, set_current_observability_context,
        )
        tokens = None
        try:
            tokens = set_current_observability_context(
                turn_id=str(hook_kwargs.get("turn_id") or ""),
                tool_call_id=str(hook_kwargs.get("tool_call_id") or ""),
                session_id=str(hook_kwargs.get("session_id") or ""),
            )
            # Native ``session`` / ``always`` choices persist for this exact
            # policy generation + argument digest.  The per-execution nonce
            # remains on ``ToolPolicyBinding`` so the dispatch authorization is
            # always fresh; including it here would silently degrade every
            # persistent owner choice into ``once``.
            rule_key = (
                f"pre_tool_call:{binding.tool_name}:{binding.registration_generation}:"
                f"{binding.args_digest}"
            )
            result = request_tool_approval(
                tool_name,
                "Plugin requested approval for this tool call",
                rule_key=rule_key,
            )
        finally:
            if tokens is not None:
                reset_current_observability_context(tokens)
    except Exception:
        return _POLICY_APPROVAL
    if not isinstance(result, dict) or result.get("approved") is not True:
        return _POLICY_APPROVAL
    return None


def evaluate_pre_tool_call(
    tool_name: str,
    args: Mapping[str, Any] | None,
    *,
    manager: Any,
    hook_kwargs: Optional[Mapping[str, Any]] = None,
) -> ToolPolicyResult:
    """Evaluate normal + decision phases and return a dispatch binding.

    This function is used at the final execution-middleware boundary. It never
    raises policy failures into a downstream handler.
    """
    from hermes_cli import plugins as plugins_module

    hook_kwargs = dict(hook_kwargs or {})
    invalid_args = not isinstance(args, Mapping)
    original = dict(args) if isinstance(args, Mapping) else {}
    whitelist_block = _thread_whitelist_block(plugins_module, tool_name)
    if whitelist_block is not None:
        return ToolPolicyResult(whitelist_block, original, None)
    try:
        nonce = secrets.token_hex(16)
    except Exception:
        return ToolPolicyResult(_POLICY_NONCE, original, None)

    try:
        generation = manager.get_hook_registration_generation("pre_tool_call")
    except Exception:
        return ToolPolicyResult(_POLICY_FAILED, original, None)
    try:
        callbacks = _phase_callbacks(manager)
    except Exception:
        return ToolPolicyResult(_POLICY_FAILED, original, None)
    try:
        normal = [callback for callback, phase in callbacks if phase == "normal"]
        decisions = [callback for callback, phase in callbacks if phase == "decision"]
    except Exception:
        return ToolPolicyResult(_POLICY_FAILED, original, None)
    if invalid_args and decisions:
        return ToolPolicyResult(_POLICY_ARGS, original, None)
    try:
        composed = copy.deepcopy(original)
    except Exception:
        return ToolPolicyResult(_POLICY_ARGS, original, None)
    pending_approval = False

    base_payload = dict(hook_kwargs)
    base_payload.update({"tool_name": tool_name})
    for callback in normal:
        payload = dict(base_payload)
        payload["middleware_trace"] = list(hook_kwargs.get("middleware_trace") or [])
        payload["args"] = copy.deepcopy(composed)
        value, status = _invoke_policy_callback(manager, callback, payload)
        if status != "ok":
            if decisions:
                return ToolPolicyResult(_POLICY_FAILED, composed, None)
            continue
        if value is None:
            continue
        if not isinstance(value, dict):
            if decisions:
                return ToolPolicyResult(_POLICY_MALFORMED, composed, None)
            continue
        action = value.get("action")
        if action == "modify":
            partial = value.get("args")
            if not isinstance(partial, dict):
                if decisions:
                    return ToolPolicyResult(_POLICY_MALFORMED, composed, None)
                continue
            composed = {**composed, **copy.deepcopy(partial)}
            continue
        if action == "block":
            message = value.get("message")
            if not isinstance(message, str) or not message.strip():
                if decisions:
                    return ToolPolicyResult(_POLICY_MALFORMED, composed, None)
                continue
            return ToolPolicyResult(_static_message(message, "BLOCKED: tool call denied by plugin policy"), composed, None)
        if action == "approve":
            pending_approval = True
            break
        if decisions:
            return ToolPolicyResult(_POLICY_MALFORMED, composed, None)

    digest = canonical_args_digest(composed)
    if digest is None:
        return ToolPolicyResult(_POLICY_ARGS, composed, None) if decisions else ToolPolicyResult(None, composed, None)
    binding = ToolPolicyBinding(tool_name, digest, nonce, generation)
    frozen_args = _freeze(copy.deepcopy(composed))

    selected: Optional[str] = None
    for callback in decisions:
        payload = dict(base_payload)
        payload["middleware_trace"] = list(hook_kwargs.get("middleware_trace") or [])
        payload["args"] = frozen_args
        payload["execution_nonce"] = nonce
        payload["registration_generation"] = generation
        value, status = _invoke_policy_callback(manager, callback, payload)
        if status != "ok":
            return ToolPolicyResult(_POLICY_FAILED, composed, None)
        if value is None:
            continue
        if not isinstance(value, dict):
            return ToolPolicyResult(_POLICY_MALFORMED, composed, None)
        action = value.get("action")
        if action == "block":
            message = value.get("message")
            if not isinstance(message, str) or not message.strip():
                return ToolPolicyResult(_POLICY_MALFORMED, composed, None)
            selected = _static_message(message, "BLOCKED: tool call denied by plugin policy")
            break
        if action == "approve":
            selected = "approve"
            break
        return ToolPolicyResult(_POLICY_MALFORMED, composed, None)

    try:
        current_generation = manager.get_hook_registration_generation("pre_tool_call")
    except Exception:
        return ToolPolicyResult(_POLICY_FAILED, composed, None)
    if current_generation != generation:
        return ToolPolicyResult(_POLICY_STALE, composed, None)
    if selected != "approve" and selected is not None:
        return ToolPolicyResult(selected, composed, None)
    if selected == "approve" or pending_approval:
        block = _approval(tool_name, binding=binding, hook_kwargs=hook_kwargs)
        if block is not None:
            return ToolPolicyResult(block, composed, None)
    return ToolPolicyResult(None, composed, binding)
