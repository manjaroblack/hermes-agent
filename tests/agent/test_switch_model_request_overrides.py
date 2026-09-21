"""Regression tests for the in-place /model switch (CLI/TUI) carrying a custom
provider's request_overrides (extra_body) — _apply_switched_provider_request_overrides.

Before the fix, agent_runtime_helpers.switch_model() swapped model/provider/
base_url/api_key in place but never touched request_overrides, so a /model
switch to a thinking-enabled custom provider in the TUI/CLI kept the old
provider's extra_body.

The switched-to entry is matched by provider key + base_url + model (the same
condition agent_init._merge_custom_provider_extra_body uses at build time), so a
*different* model selected at the same named endpoint does not inherit an
extra_body configured for another model.
"""

from typing import Any

import pytest

import agent.agent_runtime_helpers as arh
from agent.plugin_model_switch_reasoning import apply_effort_override_state, restore_effort_override_state


class _Agent:
    model: str
    base_url: str
    provider: str
    request_overrides: Any
    _custom_providers: list[dict[str, Any]]


# Two entries share the same named endpoint / base_url but pin different models —
# the exact case a name-only match got wrong.
CUSTOM_PROVIDERS = [
    {
        "name": "main-think",
        "base_url": "http://10.0.0.1:8000/v1",
        "model": "think-model",
        "extra_body": {"chat_template_kwargs": {"enable_thinking": True}},
    },
    {
        "name": "main-plain",
        "base_url": "http://10.0.0.1:8000/v1",
        "model": "plain-model",
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    },
]


def _agent(*, model, base_url, request_overrides, custom_providers=CUSTOM_PROVIDERS):
    a = _Agent()
    # switch_model() sets these on the live agent before calling the helper.
    a.model = model
    a.base_url = base_url
    a.provider = "custom"
    a.request_overrides = request_overrides
    a._custom_providers = custom_providers  # init-time cache the helper reads
    return a


def test_switch_applies_matched_provider_extra_body():
    """Switching to the matching provider+model applies its extra_body and
    preserves non-provider overrides (service_tier/speed from /fast)."""
    a = _agent(
        model="think-model",
        base_url="http://10.0.0.1:8000/v1",
        request_overrides={"service_tier": "priority"},
    )
    arh._apply_switched_provider_request_overrides(a, "custom:main-think")
    assert a.request_overrides["extra_body"] == {"chat_template_kwargs": {"enable_thinking": True}}
    assert a.request_overrides["service_tier"] == "priority"  # preserved


def test_switch_to_noncustom_clears_stale_extra_body():
    """Switching to a built-in provider clears the previous provider's extra_body."""
    a = _agent(
        model="claude-x",
        base_url="https://api.anthropic.com",
        request_overrides={
            "extra_body": {"chat_template_kwargs": {"enable_thinking": True}},
            "service_tier": "priority",
        },
    )
    arh._apply_switched_provider_request_overrides(a, "anthropic")
    assert "extra_body" not in a.request_overrides  # stale extra_body cleared
    assert a.request_overrides["service_tier"] == "priority"  # preserved


def test_switch_from_none_overrides():
    """A None request_overrides is handled and gets the matched extra_body."""
    a = _agent(
        model="plain-model",
        base_url="http://10.0.0.1:8000/v1",
        request_overrides=None,
    )
    arh._apply_switched_provider_request_overrides(a, "custom:main-plain")
    assert a.request_overrides == {"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}}


def test_switch_to_different_model_same_endpoint_does_not_inherit():
    """Review regression: selecting a *different* model while naming a custom
    provider must NOT inherit that provider's extra_body when the models differ.

    'main-think' pins 'think-model'. Selecting 'plain-model' under
    custom:main-think must not carry enable_thinking=True — the model-aware
    matcher rejects the mismatch and the stale extra_body is cleared. (A
    name-only match would have wrongly carried it over.)
    """
    a = _agent(
        model="plain-model",  # differs from main-think's pinned 'think-model'
        base_url="http://10.0.0.1:8000/v1",
        request_overrides={"extra_body": {"chat_template_kwargs": {"enable_thinking": True}}},
    )
    arh._apply_switched_provider_request_overrides(a, "custom:main-think")
    assert "extra_body" not in a.request_overrides  # not inherited; stale cleared


def test_switch_endpoint_mismatch_does_not_inherit():
    """A matching provider *name* but a different base_url must not match either
    (endpoint identity is part of the condition)."""
    a = _agent(
        model="think-model",
        base_url="http://10.9.9.9:8000/v1",  # different endpoint than the entry
        request_overrides={"extra_body": {"chat_template_kwargs": {"enable_thinking": True}}},
    )
    arh._apply_switched_provider_request_overrides(a, "custom:main-think")
    assert "extra_body" not in a.request_overrides  # base_url mismatch -> cleared


class _EffortOnlyAgent:
    model = "grok-4.6"
    provider = "xai-oauth"
    requested_provider = "xai-oauth"
    base_url = "https://api.x.ai/v1"
    api_mode = "codex_responses"
    api_key = "test-key"  # pragma: allowlist secret
    _client_kwargs = {
        "api_key": "test-key",  # pragma: allowlist secret
        "base_url": "https://api.x.ai/v1",
    }
    _use_prompt_caching = True
    _use_native_cache_layout = False
    _reasoning_echo_flag = False
    _cached_system_prompt = "frozen"
    runtime_capabilities = {"native_compaction": False}
    context_compressor = None

    def __init__(self, *, model=None, provider=None, old_effort="high"):
        self.model = model or type(self).model
        self.provider = provider or type(self).provider
        self.reasoning_config = {"enabled": True, "effort": old_effort}
        self.request_overrides: dict[str, Any] = {
            "service_tier": "priority",
            "reasoning": {"effort": old_effort, "summary": "auto"},
            "thinking": {"type": "enabled", "budget_tokens": 256},
            "extra_body": {"reasoning": {"effort": old_effort, "marker": "keep"}},
        }
        self._primary_runtime = {"effort": old_effort}
        self._reasoning_effort_override_state = None


@pytest.mark.parametrize(
    ("model", "provider", "old_effort", "new_effort"),
    [
        ("grok-4.6", "xai-oauth", "high", "medium"),
        ("gpt-5.6-luna", "openai-codex", "medium", "high"),
    ],
)
def test_same_identity_effort_only_updates_runtime_without_rebuilding_client(
    model, provider, old_effort, new_effort
):
    agent = _EffortOnlyAgent(model=model, provider=provider, old_effort=old_effort)

    result = arh.switch_model(agent, model, provider, reasoning_effort=new_effort)

    assert result is True
    assert agent.model == model
    assert agent.provider == provider
    assert agent.reasoning_config == {"enabled": True, "effort": new_effort}
    assert agent.request_overrides["service_tier"] == "priority"
    assert agent.request_overrides["reasoning"]["effort"] == new_effort
    assert agent.request_overrides["reasoning"]["summary"] == "auto"
    assert agent.request_overrides["thinking"] == {"type": "enabled", "budget_tokens": 256}
    assert agent.request_overrides["extra_body"]["reasoning"]["effort"] == new_effort
    assert agent.request_overrides["extra_body"]["reasoning"]["marker"] == "keep"
    assert agent._primary_runtime["reasoning_config"] == {
        "enabled": True,
        "effort": new_effort,
    }


def test_effort_override_is_restored_before_identity_switch():
    agent = _EffortOnlyAgent()
    original_overrides = {
        key: value.copy() if isinstance(value, dict) else value
        for key, value in agent.request_overrides.items()
    }

    apply_effort_override_state(agent, "grok-4.6", "xai-oauth", "medium")
    assert agent.request_overrides["reasoning"]["effort"] == "medium"

    restore_effort_override_state(agent)

    assert agent.request_overrides == original_overrides
    assert agent._reasoning_effort_override_state is None


def test_same_identity_effort_only_rolls_back_runtime_on_snapshot_failure(monkeypatch):
    agent = _EffortOnlyAgent()
    original_reasoning = dict(agent.reasoning_config)
    original_overrides = {key: value.copy() if isinstance(value, dict) else value
                          for key, value in agent.request_overrides.items()}
    original_primary = dict(agent._primary_runtime)
    monkeypatch.setattr(arh, "_build_primary_runtime_snapshot", lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")))

    try:
        arh.switch_model(agent, "grok-4.6", "xai-oauth", reasoning_effort="medium")
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("snapshot failure should propagate")

    assert agent.reasoning_config == original_reasoning
    assert agent.request_overrides == original_overrides
    assert agent._primary_runtime == original_primary


def _patch_cross_identity_switch(monkeypatch, agent):
    monkeypatch.setattr(
        arh,
        "_resolve_switch_destination",
        lambda _agent, _model, _provider, base_url, api_mode, *_args: (
            api_mode,
            base_url,
            {},
        ),
    )

    def swap_runtime(target, new_model, new_provider, api_key, base_url, api_mode, *_args):
        target.model = new_model
        target.provider = target.requested_provider = new_provider
        target.base_url = base_url
        target.api_mode = api_mode
        target.api_key = api_key
        target._client_kwargs = {
            "api_key": api_key,
            "base_url": target.base_url,
        }

    def finish_switch(target, *_args):
        if target.provider == "openai-codex":
            target.request_overrides = {
                "service_tier": "destination",
                "extra_body": {"reasoning": {"effort": "high", "destination": True}},
            }
        else:
            target.request_overrides = {
                "service_tier": "flash",
                "extra_body": {"route": "keep"},
            }

    monkeypatch.setattr(arh, "_swap_switch_runtime", swap_runtime)
    monkeypatch.setattr(arh, "_resolve_switch_context_length", lambda *_args: ([], None))
    monkeypatch.setattr(arh, "_finish_switch", finish_switch)
    monkeypatch.setattr("agent.chat_completion_helpers._reset_stale_streak", lambda *_args: None)
    monkeypatch.setattr(agent, "_read_reasoning_echo_from_config", lambda: False, raising=False)
    monkeypatch.setattr(agent, "_anthropic_prompt_cache_policy", lambda **_kwargs: (True, False), raising=False)
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: {})
    monkeypatch.setattr(
        "hermes_constants.resolve_reasoning_config",
        lambda _config, model, *_args: (
            None if model == "z-ai/glm-5.3-flash" else {"enabled": True, "effort": "high"}
        ),
    )


def test_cross_identity_effort_sanitizes_rederived_destination_overrides(monkeypatch):
    """Destination provider overrides cannot replace the selected effort or its snapshot."""
    agent = _EffortOnlyAgent()
    _patch_cross_identity_switch(monkeypatch, agent)

    result = arh.switch_model(
        agent,
        "gpt-5.6-luna",
        "openai-codex",
        api_key="new-key",  # pragma: allowlist secret
        base_url="https://api.openai.com/v1",
        api_mode="codex_responses",
        capabilities={},
        reasoning_effort="medium",
    )

    assert result is True
    assert agent.request_overrides["service_tier"] == "destination"
    assert agent.request_overrides["extra_body"]["reasoning"]["effort"] == "medium"
    assert agent.request_overrides["extra_body"]["reasoning"]["destination"] is True
    assert agent._primary_runtime["request_overrides"] == agent.request_overrides


def test_grok_to_luna_effort_then_flash_model_only_does_not_leak_jev_override(monkeypatch):
    agent = _EffortOnlyAgent()
    _patch_cross_identity_switch(monkeypatch, agent)

    assert arh.switch_model(
        agent,
        "gpt-5.6-luna",
        "openai-codex",
        api_key="luna-test-key",  # pragma: allowlist secret
        base_url="https://api.openai.com/v1",
        api_mode="codex_responses",
        capabilities={},
        reasoning_effort="medium",
    ) is True
    assert agent.request_overrides["extra_body"]["reasoning"]["effort"] == "medium"

    assert arh.switch_model(
        agent,
        "z-ai/glm-5.3-flash",
        "openrouter",
        api_key="flash-test-key",  # pragma: allowlist secret
        base_url="https://openrouter.ai/api/v1",
        api_mode="chat_completions",
        capabilities={},
    ) is True

    assert agent.model == "z-ai/glm-5.3-flash"
    assert agent.provider == "openrouter"
    assert agent.reasoning_config is None
    assert agent._reasoning_effort_override_state is None
    assert agent.request_overrides == {
        "service_tier": "flash",
        "extra_body": {"route": "keep"},
    }
