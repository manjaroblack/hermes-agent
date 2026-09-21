"""Reasoning-effort validation and override hygiene for plugin model switches."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Optional

from agent.reasoning_effort import (
    EFFORT_LADDER,
    XAI_GROK46_EFFORTS,
    XAI_LEGACY_EFFORTS,
    codex_supported_efforts,
)


_CODEX_PROVIDERS = frozenset({"openai-codex"})
_XAI_PROVIDERS = frozenset({"xai", "xai-oauth"})


def supported_reasoning_efforts(model: str, provider: str) -> tuple[str, ...]:
    """Return the cached effort vocabulary for a known destination family.

    ``()`` means the model/provider pair is not a supported Jev effort family;
    callers must omit a proposed override rather than infer a provider default.
    """
    normalized_provider = str(provider or "").strip().lower()
    if normalized_provider in _CODEX_PROVIDERS:
        return codex_supported_efforts(model)
    if normalized_provider in _XAI_PROVIDERS:
        from agent.model_metadata import grok_supports_reasoning_effort, is_grok_46_family

        if not grok_supports_reasoning_effort(model):
            return ()
        return XAI_GROK46_EFFORTS if is_grok_46_family(model) else XAI_LEGACY_EFFORTS
    return ()


def normalize_reasoning_effort(model: str, provider: str, effort: Any) -> Optional[str]:
    """Return an exact supported token, or ``None`` without clamping/remapping."""
    if not isinstance(effort, str) or effort not in EFFORT_LADDER:
        return None
    supported = supported_reasoning_efforts(model, provider)
    return effort if effort in supported else None


def reasoning_config_for_directive(model: str, provider: str, effort: Any) -> Optional[dict[str, Any]]:
    """Parse a valid destination-family token into canonical runtime config."""
    normalized = normalize_reasoning_effort(model, provider, effort)
    if normalized is None:
        return None
    from hermes_constants import parse_reasoning_effort

    return parse_reasoning_effort(normalized)


def effective_reasoning_effort(reasoning_config: Any) -> Optional[str]:
    """Return the runtime's exact selected effort, or ``None`` when disabled/absent."""
    if not isinstance(reasoning_config, Mapping) or reasoning_config.get("enabled") is False:
        return None
    effort = reasoning_config.get("effort")
    return effort if isinstance(effort, str) and effort in EFFORT_LADDER else None


def _sanitize_reasoning_container(value: Any, effort: str) -> Any:
    if not isinstance(value, Mapping):
        return None
    result = dict(value)
    for key in ("reasoning_effort", "reasoning_config"):
        result.pop(key, None)
    reasoning = result.get("reasoning")
    if isinstance(reasoning, Mapping):
        result["reasoning"] = {**dict(reasoning), "effort": effort}
    elif "reasoning" in result:
        result.pop("reasoning", None)
    for key in ("thinking", "thinking_config"):
        if key not in result:
            continue
        thinking = result[key]
        if isinstance(thinking, Mapping) and "effort" in thinking:
            result[key] = {**dict(thinking), "effort": effort}
        elif not isinstance(thinking, Mapping):
            # A malformed transport override could defeat the selected effort; drop only
            # that conflicting value. Preserve valid thinking fields unrelated to effort.
            result.pop(key, None)
    nested = result.get("extra_body")
    if isinstance(nested, Mapping):
        result["extra_body"] = _sanitize_reasoning_container(nested, effort)
    return result


def sanitize_request_overrides(overrides: Any, effort: str) -> dict[str, Any]:
    """Make a selected effort authoritative while retaining unrelated overrides."""
    if not isinstance(overrides, Mapping):
        return {}
    sanitized = _sanitize_reasoning_container(deepcopy(dict(overrides)), effort)
    return sanitized if isinstance(sanitized, dict) else {}


def _same_identity(state: Any, model: str, provider: str) -> bool:
    return (
        isinstance(state, Mapping)
        and str(state.get("model") or "").strip().casefold() == str(model or "").strip().casefold()
        and str(state.get("provider") or "").strip().lower() == str(provider or "").strip().lower()
    )


def restore_effort_override_state(agent: Any) -> None:
    """Restore pre-effort request overrides before changing runtime identity."""
    state = getattr(agent, "_reasoning_effort_override_state", None)
    if not isinstance(state, Mapping):
        return
    if not _same_identity(state, getattr(agent, "model", ""), getattr(agent, "provider", "")):
        agent._reasoning_effort_override_state = None
        return
    state_map = state
    base_overrides = state_map.get("base_request_overrides")
    agent.request_overrides = deepcopy(base_overrides) if isinstance(base_overrides, Mapping) else {}
    agent._reasoning_effort_override_state = None


def apply_effort_override_state(agent: Any, model: str, provider: str, effort: str) -> None:
    """Record and apply a selected effort without making the override leak to another identity."""
    state = getattr(agent, "_reasoning_effort_override_state", None)
    if _same_identity(state, model, provider):
        state_map = state if isinstance(state, Mapping) else {}
        base_overrides = state_map.get("base_request_overrides")
    else:
        base_overrides = getattr(agent, "request_overrides", {})
    base_overrides = deepcopy(base_overrides) if isinstance(base_overrides, Mapping) else {}
    agent._reasoning_effort_override_state = {
        "model": model,
        "provider": provider,
        "effort": effort,
        "base_request_overrides": base_overrides,
    }
    agent.request_overrides = sanitize_request_overrides(base_overrides, effort)
