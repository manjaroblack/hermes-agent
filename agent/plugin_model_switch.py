"""Host-owned application of pre-LLM plugin model-switch directives."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional


def _valid_directive(value: Any) -> Optional[dict[str, Any]]:
    if not isinstance(value, Mapping):
        return None
    model_switch = value.get("model_switch")
    if not isinstance(model_switch, Mapping):
        return None
    model = model_switch.get("model")
    provider = model_switch.get("provider")
    allow_cache_break = model_switch.get("allow_cache_break")
    if (not isinstance(model, str) or not model.strip()
            or not isinstance(provider, str) or not provider.strip()
            or not isinstance(allow_cache_break, bool)):
        return None
    return {
        "model": model.strip(),
        "provider": provider.strip(),
        "allow_cache_break": allow_cache_break,
    }


def _distinct_destinations(directives: Iterable[dict[str, Any]]) -> Optional[dict[str, Any]]:
    selected: Optional[dict[str, Any]] = None
    for directive in directives:
        if selected is None:
            selected = directive
            continue
        if (directive["model"].casefold(), directive["provider"].casefold()) != (
            selected["model"].casefold(), selected["provider"].casefold()
        ):
            return None
        # The first valid directive owns cache-break permission as well as the
        # destination; later duplicates cannot widen it.
        continue
    return selected


def _resolve_destination(agent: Any, directive: Mapping[str, Any]):
    from hermes_cli.config import load_config
    from hermes_cli.model_switch import switch_model

    config = load_config() or {}
    user_providers = config.get("providers") if isinstance(config, Mapping) else None
    custom_providers = config.get("custom_providers") if isinstance(config, Mapping) else None
    return switch_model(
        directive["model"],
        getattr(agent, "provider", "") or "",
        getattr(agent, "model", "") or "",
        current_base_url=getattr(agent, "base_url", "") or "",
        current_api_key=getattr(agent, "api_key", "") or "",
        explicit_provider=directive["provider"],
        user_providers=user_providers if isinstance(user_providers, dict) else {},
        custom_providers=custom_providers if isinstance(custom_providers, list) else None,
    )


def apply_pre_llm_model_switch(
    agent: Any,
    hook_results: Iterable[Any],
    *,
    is_first_turn: bool,
    registration_generation_before: int,
    registration_generation_after: int,
) -> bool:
    """Apply one unambiguous host-owned model switch, returning whether it was applied.

    The callback thread only produces data. This function is called by the owning turn
    thread after the bounded hook dispatch and before the first model request.
    """
    # A plugin route is only safe on a fully initialized turn owner. In
    # particular, a partial test/dry-run object without the frozen prompt or
    # tool-wire fields must not be mutated speculatively.
    if (
        not callable(getattr(agent, "switch_model", None))
        or not hasattr(agent, "_cached_system_prompt")
        or not hasattr(agent, "valid_tool_names")
        or not hasattr(agent, "api_mode")
    ):
        return False
    if registration_generation_before != registration_generation_after:
        return False
    try:
        from hermes_cli.plugins import get_hook_registration_generation
        if get_hook_registration_generation("pre_llm_call") != registration_generation_after:
            return False
    except Exception:
        return False
    directives = [directive for result in hook_results if (directive := _valid_directive(result)) is not None]
    selected = _distinct_destinations(directives)
    if selected is None:
        return False
    if is_first_turn:
        if selected["allow_cache_break"]:
            return False
    elif not selected["allow_cache_break"]:
        return False
    if (selected["model"].casefold(), selected["provider"].casefold()) == (
        str(getattr(agent, "model", "") or "").casefold(),
        str(getattr(agent, "provider", "") or "").casefold(),
    ):
        return False
    try:
        resolved = _resolve_destination(agent, selected)
    except Exception:
        return False
    if not getattr(resolved, "success", False):
        return False
    try:
        agent.switch_model(
            resolved.new_model,
            resolved.target_provider,
            resolved.api_key,
            resolved.base_url,
            resolved.api_mode,
            resolved.capabilities,
            # ``allow_cache_break`` controls provider transport cache reuse; it
            # must never rebuild Hermes' frozen prompt/history prefix.
            preserve_frozen_prompt=True,
            request_overrides=resolved.request_overrides,
            runtime_capabilities=resolved.runtime_capabilities,
        )
    except Exception:
        return False
    return True
