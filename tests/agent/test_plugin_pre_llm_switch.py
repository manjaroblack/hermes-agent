"""Behavior contracts for host-owned pre_llm model-switch directives."""

import copy
import json
import threading
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from agent.turn_context import _collect_pre_llm_call_context


def _tool_definitions():
    return [{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search without mutating state.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }]


class _Agent:
    _persist_disabled = False
    session_id = "session"
    platform = "test"
    _parent_session_id = ""
    _user_id = ""
    model = "old-model"
    provider = "old-provider"
    api_mode = "chat_completions"
    valid_tool_names = []
    _cached_system_prompt = "frozen system prompt"
    reasoning_config: Any = None

    def __init__(self):
        self.switch_calls = []

    def switch_model(self, *args, **kwargs):
        if args:
            names = ("new_model", "new_provider", "api_key", "base_url", "api_mode", "capabilities")
            kwargs.update(dict(zip(names, args)))
        self.switch_calls.append(kwargs)
        self.model = kwargs["new_model"]
        self.provider = kwargs["new_provider"]
        # The production switch engine invalidates this by default. The plugin
        # path must opt into preservation explicitly.
        if not kwargs.get("preserve_frozen_prompt"):
            self._cached_system_prompt = None


def _resolved(model="new-model", provider="new-provider"):
    return SimpleNamespace(
        success=True,
        new_model=model,
        target_provider=provider,
        api_key="resolved-key",
        base_url="https://provider.example/v1",
        api_mode="chat_completions",
        capabilities={"native_compaction": False},
        runtime_capabilities={},
        request_overrides={},
    )


def _run(monkeypatch, agent, results, history):
    seen = {}

    def invoke(_hook, **kwargs):
        seen.update(kwargs)
        return results

    monkeypatch.setattr("hermes_cli.lifecycle.invoke_hook", invoke)
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: 7)
    monkeypatch.setattr("hermes_cli.model_switch.switch_model", lambda *_args, **_kwargs: _resolved())
    context = _collect_pre_llm_call_context(
        agent,
        effective_task_id="task",
        turn_id="turn",
        original_user_message="hello",
        messages=[],
        conversation_history=history,
    )
    return seen, context


def test_first_turn_switches_on_owner_thread_and_preserves_frozen_prompt(monkeypatch):
    agent = _Agent()
    seen, _ = _run(
        monkeypatch,
        agent,
        [{"model_switch": {"model": "new-model", "provider": "new-provider", "allow_cache_break": False}}],
        [],
    )

    assert seen["provider"] == "old-provider"
    assert seen["is_first_turn"] is True
    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["preserve_frozen_prompt"] is True
    assert agent._cached_system_prompt == "frozen system prompt"


def test_later_turn_requires_explicit_cache_break_permission(monkeypatch):
    agent = _Agent()
    _run(
        monkeypatch,
        agent,
        [{"model_switch": {"model": "new-model", "provider": "new-provider", "allow_cache_break": False}}],
        [{"role": "user", "content": "previous"}],
    )
    assert agent.switch_calls == []

    agent = _Agent()
    _run(
        monkeypatch,
        agent,
        [{"model_switch": {"model": "new-model", "provider": "new-provider", "allow_cache_break": True}}],
        [{"role": "user", "content": "previous"}],
    )
    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["preserve_frozen_prompt"] is True
    assert agent._cached_system_prompt == "frozen system prompt"


def test_pre_llm_payload_is_detached_from_live_message_objects(monkeypatch):
    agent = _Agent()
    original_user_message = {"content": "hello"}
    original_messages = [{"role": "user", "content": {"nested": "value"}}]

    def invoke(_hook, **kwargs):
        kwargs["user_message"]["content"] = "plugin mutation"
        kwargs["conversation_history"][0]["content"]["nested"] = "plugin mutation"
        return []

    monkeypatch.setattr("hermes_cli.lifecycle.invoke_hook", invoke)
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: 7)
    _collect_pre_llm_call_context(
        agent,
        effective_task_id="task",
        turn_id="turn",
        original_user_message=original_user_message,
        messages=original_messages,
        conversation_history=[],
    )

    assert original_user_message == {"content": "hello"}
    assert original_messages == [{"role": "user", "content": {"nested": "value"}}]


def test_pre_llm_hook_does_not_cold_build_skill_snapshot(monkeypatch):
    agent = _Agent()
    monkeypatch.setattr("hermes_cli.lifecycle.invoke_hook", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: 7)
    monkeypatch.setattr(
        "hermes_cli.plugins._delivery_manager",
        lambda: pytest.fail("pre_llm hook path performed cold snapshot publication"),
    )

    assert _collect_pre_llm_call_context(
        agent,
        effective_task_id="task",
        turn_id="turn",
        original_user_message="hello",
        messages=[],
        conversation_history=[],
    ) == ""


def test_conflicting_valid_directives_are_rejected_without_speculative_switch(monkeypatch):
    agent = _Agent()
    _run(
        monkeypatch,
        agent,
        [
            {"model_switch": {"model": "first", "provider": "provider-a", "allow_cache_break": False}},
            {"model_switch": {"model": "second", "provider": "provider-b", "allow_cache_break": False}},
        ],
        [],
    )
    assert agent.switch_calls == []
    assert agent.model == "old-model"


def test_malformed_and_stale_directives_are_ignored(monkeypatch):
    agent = _Agent()
    generations = iter([3, 4])
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: next(generations))
    monkeypatch.setattr("hermes_cli.lifecycle.invoke_hook", lambda *_args, **_kwargs: [
        {"model_switch": {"model": "new", "provider": "p", "allow_cache_break": "yes"}}
    ])
    _collect_pre_llm_call_context(
        agent, effective_task_id="task", turn_id="turn", original_user_message="hello",
        messages=[], conversation_history=[],
    )
    assert agent.switch_calls == []


@pytest.mark.parametrize(
    ("history", "allow_cache_break", "expected_model", "expected_provider", "expected_rebuilds"),
    [
        ([], False, "routed-model", "openrouter", 1),
        (
            [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "earlier answer"}],
            True,
            "routed-model",
            "openrouter",
            1,
        ),
        (
            [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "earlier answer"}],
            False,
            "old-model",
            "custom",
            0,
        ),
    ],
)
def test_run_conversation_routes_the_next_real_sdk_request_without_mutating_frozen_prefix(
    tmp_path,
    monkeypatch,
    history,
    allow_cache_break,
    expected_model,
    expected_provider,
    expected_rebuilds,
):
    """The plugin result crosses the real turn + switch engines before the SDK call."""
    from hermes_cli import plugins
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
    from run_agent import AIAgent
    from tests.run_agent.test_run_agent import _mock_response

    with (
        patch("model_tools.get_tool_definitions", return_value=_tool_definitions()),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI"),
    ):
        agent = AIAgent(
            api_key="old-test-key",
            base_url="https://old.example.invalid/v1",
            provider="custom",
            model="old-model",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            save_trajectories=False,
        )
    agent_any = cast(Any, agent)

    manager = PluginManager(scope_key=str(tmp_path / "home"))
    manager._discovered = True
    context = PluginContext(
        PluginManifest(name="route-plugin", version="1.0.0", source="test"), manager
    )
    hook_inputs = []

    def route_hook(**kwargs):
        hook_inputs.append((kwargs["model"], kwargs["provider"], kwargs["is_first_turn"]))
        return {
            "model_switch": {
                "model": "routed-model",
                "provider": "openrouter",
                "allow_cache_break": allow_cache_break,
            }
        }

    context.register_hook("pre_llm_call", route_hook)
    monkeypatch.setattr(plugins, "_plugin_manager", manager)
    monkeypatch.setattr(plugins, "_plugin_managers_by_home", {})
    monkeypatch.setattr("hermes_cli.lifecycle._observe", lambda *_args, **_kwargs: None)

    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda **_kwargs: {
            "provider": "openrouter",
            "api_key": "routed-test-key",
            "base_url": "https://openrouter.ai/api/v1",
            "api_mode": "chat_completions",
        },
    )
    monkeypatch.setattr(
        "hermes_cli.models_validate.validate_requested_model",
        lambda *_args, **_kwargs: {
            "accepted": True,
            "persist": True,
            "recognized": True,
            "message": None,
        },
    )
    monkeypatch.setattr("hermes_cli.model_switch.get_model_capabilities", lambda *_a, **_k: {})
    monkeypatch.setattr("hermes_cli.model_switch.get_model_info", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "agent.native_compaction.resolve_native_compaction_capabilities",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr("agent.credential_pool.load_pool", lambda _provider: None)
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: {})
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: {})

    captured_requests = []
    client_rebuilds = []
    sdk_client = MagicMock(name="CapturedSDKClient")

    def sdk_create(**kwargs):
        captured_requests.append({
            "model": kwargs.get("model"),
            "provider": agent_any.provider,
            "messages": copy.deepcopy(kwargs.get("messages")),
            "tools": copy.deepcopy(kwargs.get("tools")),
        })
        return _mock_response(content="routed response", finish_reason="stop")

    sdk_client.chat.completions.create.side_effect = sdk_create

    def build_sdk_client(client_kwargs, **_kwargs):
        client_rebuilds.append(dict(client_kwargs))
        return sdk_client

    agent.client = sdk_client
    monkeypatch.setattr(agent, "_create_openai_client", build_sdk_client)
    monkeypatch.setattr(agent, "_try_refresh_env_client_credentials", lambda: False)
    monkeypatch.setattr(agent, "_ensure_db_session", lambda: None)
    monkeypatch.setattr(agent, "_persist_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent, "_save_trajectory", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_any, "_cleanup_task_resources", lambda *_args, **_kwargs: None)
    agent_any._session_db = None
    agent_any.context_compressor = None
    agent_any.compression_enabled = False
    agent_any._disable_streaming = True
    agent_any._cached_system_prompt = "frozen system prompt"

    history_before = copy.deepcopy(history)
    tools_before = json.dumps(agent_any.tools, sort_keys=True, separators=(",", ":"))
    prompt_before = agent_any._cached_system_prompt

    result = agent_any.run_conversation("current question", conversation_history=history)

    assert result["final_response"] == "routed response"
    assert hook_inputs == [("old-model", "custom", not bool(history_before))]
    assert len(client_rebuilds) == expected_rebuilds
    assert len(captured_requests) == 1
    request = captured_requests[0]
    assert (request["model"], request["provider"]) == (expected_model, expected_provider)
    assert request["messages"][0] == {"role": "system", "content": prompt_before}
    assert request["messages"][1:1 + len(history_before)] == history_before
    assert json.dumps(request["tools"], sort_keys=True, separators=(",", ":")) == tools_before
    assert agent_any._cached_system_prompt == prompt_before
    assert history == history_before


def test_late_timed_out_pre_llm_result_cannot_mutate_owner_thread_state(
    tmp_path, monkeypatch
):
    from hermes_cli import plugins
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest

    manager = PluginManager(scope_key=str(tmp_path / "home"))
    manager._discovered = True
    context = PluginContext(
        PluginManifest(name="late-route-plugin", version="1.0.0", source="test"), manager
    )
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def late_route(**_kwargs):
        started.set()
        release.wait(timeout=2.0)
        finished.set()
        return {
            "model_switch": {
                "model": "too-late",
                "provider": "too-late",
                "allow_cache_break": False,
            }
        }

    context.register_hook("pre_llm_call", late_route)
    monkeypatch.setattr(plugins, "_plugin_manager", manager)
    monkeypatch.setattr(plugins, "_plugin_managers_by_home", {})
    monkeypatch.setattr(plugins, "_resolve_hook_callback_timeout", lambda: 0.05)
    monkeypatch.setattr("hermes_cli.lifecycle._observe", lambda *_args, **_kwargs: None)

    agent = _Agent()
    try:
        assert _collect_pre_llm_call_context(
            agent,
            effective_task_id="task",
            turn_id="turn",
            original_user_message="hello",
            messages=[],
            conversation_history=[],
        ) == ""
        assert started.wait(timeout=1.0)
        assert agent.switch_calls == []
        assert agent.model == "old-model"

        release.set()
        assert finished.wait(timeout=1.0)
        assert agent.switch_calls == []
        assert agent.model == "old-model"
    finally:
        release.set()


def test_same_identity_effort_only_switch_uses_first_turn_permission(monkeypatch):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        [],
    )

    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["new_model"] == "grok-4.6"
    assert agent.switch_calls[0]["new_provider"] == "xai-oauth"
    assert agent.switch_calls[0]["reasoning_effort"] == "medium"


def test_same_identity_effort_only_avoids_destination_or_credential_resolution(monkeypatch):
    import agent.plugin_model_switch as plugin_model_switch

    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}
    monkeypatch.setattr(
        plugin_model_switch,
        "_resolve_destination",
        lambda *_args, **_kwargs: pytest.fail(
            "same-identity effort switch performed destination/credential resolution"
        ),
    )
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: 7)

    assert plugin_model_switch.apply_pre_llm_model_switch(
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        is_first_turn=True,
        registration_generation_before=7,
        registration_generation_after=7,
    ) is True

    assert agent.switch_calls[0]["reasoning_effort"] == "medium"


@pytest.mark.parametrize(
    ("history", "allow_cache_break", "expected_calls"),
    [([], True, 0), ([{"role": "user", "content": "previous"}], False, 0)],
)
def test_same_identity_effort_only_rejects_wrong_cache_permission(
    monkeypatch, history, allow_cache_break, expected_calls
):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": allow_cache_break,
            "reasoning_effort": "medium",
        }}],
        history,
    )

    assert len(agent.switch_calls) == expected_calls


def test_later_same_identity_effort_only_switch_accepts_cache_break(monkeypatch):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": True,
            "reasoning_effort": "medium",
        }}],
        [{"role": "user", "content": "previous"}],
    )

    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["reasoning_effort"] == "medium"


def test_cross_identity_valid_effort_reaches_host_switch(monkeypatch):
    agent = _Agent()

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        [],
    )

    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["reasoning_effort"] == "medium"


@pytest.mark.parametrize("effort", [True, {}, "unknown", "max", "ultra", " MEDIUM "])
def test_invalid_or_unsupported_effort_keeps_model_switch_without_override(monkeypatch, effort):
    agent = _Agent()

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": effort,
        }}],
        [],
    )

    assert len(agent.switch_calls) == 1
    assert "reasoning_effort" not in agent.switch_calls[0]


def test_unknown_destination_family_keeps_model_switch_without_effort(monkeypatch):
    agent = _Agent()

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "opaque-model",
            "provider": "custom",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        [],
    )

    assert len(agent.switch_calls) == 1
    assert "reasoning_effort" not in agent.switch_calls[0]


def test_same_identity_effort_only_noops_when_effective_effort_is_unchanged(monkeypatch):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "medium"}

    _run(
        monkeypatch,
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        [],
    )

    assert agent.switch_calls == []


@pytest.mark.parametrize("effort", [None, True, {}, "unknown", "max"])
def test_same_identity_absent_invalid_or_unsupported_effort_is_a_noop(monkeypatch, effort):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}
    directive = {
        "model": "grok-4.6",
        "provider": "xai-oauth",
        "allow_cache_break": False,
    }
    if effort is not None:
        directive["reasoning_effort"] = effort

    _run(monkeypatch, agent, [{"model_switch": directive}], [])

    assert agent.switch_calls == []


def test_same_identity_effort_only_propagates_host_noop_result(monkeypatch):
    from agent.plugin_model_switch import apply_pre_llm_model_switch

    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}
    monkeypatch.setattr(agent, "switch_model", lambda *_args, **_kwargs: False)
    monkeypatch.setattr("hermes_cli.plugins.get_hook_registration_generation", lambda *_: 7)

    assert apply_pre_llm_model_switch(
        agent,
        [{"model_switch": {
            "model": "grok-4.6",
            "provider": "xai-oauth",
            "allow_cache_break": False,
            "reasoning_effort": "medium",
        }}],
        is_first_turn=True,
        registration_generation_before=7,
        registration_generation_after=7,
    ) is False


def test_same_identity_duplicate_directives_first_owner_controls_effort_and_permission(monkeypatch):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}

    _run(
        monkeypatch,
        agent,
        [
            {"model_switch": {
                "model": "grok-4.6",
                "provider": "xai-oauth",
                "allow_cache_break": False,
                "reasoning_effort": "medium",
            }},
            {"model_switch": {
                "model": "grok-4.6",
                "provider": "xai-oauth",
                "allow_cache_break": True,
                "reasoning_effort": "low",
            }},
        ],
        [],
    )

    assert len(agent.switch_calls) == 1
    assert agent.switch_calls[0]["reasoning_effort"] == "medium"
    assert "allow_cache_break" not in agent.switch_calls[0]


def test_same_identity_duplicate_cannot_fill_first_directives_missing_effort(monkeypatch):
    agent = _Agent()
    agent.model = "grok-4.6"
    agent.provider = "xai-oauth"
    agent.reasoning_config = {"enabled": True, "effort": "high"}

    _run(
        monkeypatch,
        agent,
        [
            {"model_switch": {
                "model": "grok-4.6",
                "provider": "xai-oauth",
                "allow_cache_break": False,
            }},
            {"model_switch": {
                "model": "grok-4.6",
                "provider": "xai-oauth",
                "allow_cache_break": False,
                "reasoning_effort": "medium",
            }},
        ],
        [],
    )

    assert agent.switch_calls == []


@pytest.mark.parametrize(
    (
        "start_model",
        "start_provider",
        "start_base_url",
        "start_effort",
        "target_model",
        "target_provider",
        "target_base_url",
        "target_effort",
        "history",
        "allow_cache_break",
    ),
    [
        (
            "grok-4.6",
            "xai-oauth",
            "https://api.x.ai/v1",
            "high",
            "grok-4.6",
            "xai-oauth",
            "https://api.x.ai/v1",
            "medium",
            [],
            False,
        ),
        (
            "gpt-5.6-luna",
            "openai-codex",
            "https://chatgpt.com/backend-api/codex",
            "medium",
            "gpt-5.6-luna",
            "openai-codex",
            "https://chatgpt.com/backend-api/codex",
            "high",
            [{"role": "user", "content": "earlier"}, {"role": "assistant", "content": "answer"}],
            True,
        ),
        (
            "grok-4.6",
            "xai-oauth",
            "https://api.x.ai/v1",
            "high",
            "gpt-5.6-luna",
            "openai-codex",
            "https://chatgpt.com/backend-api/codex",
            "medium",
            [],
            False,
        ),
    ],
    ids=("grok-effort-only-first", "luna-effort-only-later", "grok-to-luna-with-effort"),
)
def test_registered_effort_switch_reaches_next_real_codex_request_without_rebuilding_prefix(
    tmp_path,
    monkeypatch,
    start_model,
    start_provider,
    start_base_url,
    start_effort,
    target_model,
    target_provider,
    target_base_url,
    target_effort,
    history,
    allow_cache_break,
):
    from hermes_cli import plugins
    from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
    from run_agent import AIAgent

    with (
        patch("model_tools.get_tool_definitions", return_value=_tool_definitions()),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI"),
    ):
        agent = AIAgent(
            api_key="old-test-key",
            base_url=start_base_url,
            provider=start_provider,
            model=start_model,
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            save_trajectories=False,
        )
    agent_any = cast(Any, agent)

    manager = PluginManager(scope_key=str(tmp_path / "home"))
    manager._discovered = True
    context = PluginContext(
        PluginManifest(name="effort-route-plugin", version="1.0.0", source="test"), manager
    )

    def route_hook(**kwargs):
        assert kwargs["model"] == start_model
        assert kwargs["provider"] == start_provider
        assert kwargs["is_first_turn"] is (not history)
        return {"model_switch": {
            "model": target_model,
            "provider": target_provider,
            "allow_cache_break": allow_cache_break,
            "reasoning_effort": target_effort,
        }}

    context.register_hook("pre_llm_call", route_hook)
    monkeypatch.setattr(plugins, "_plugin_manager", manager)
    monkeypatch.setattr(plugins, "_plugin_managers_by_home", {})
    monkeypatch.setattr("hermes_cli.lifecycle._observe", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda **_kwargs: {
            "provider": target_provider,
            "api_key": "routed-test-key",
            "base_url": target_base_url,
            "api_mode": "codex_responses",
        },
    )
    monkeypatch.setattr(
        "hermes_cli.models_validate.validate_requested_model",
        lambda *_args, **_kwargs: {
            "accepted": True,
            "persist": True,
            "recognized": True,
            "message": None,
        },
    )
    monkeypatch.setattr("hermes_cli.model_switch.get_model_capabilities", lambda *_a, **_k: {})
    monkeypatch.setattr("hermes_cli.model_switch.get_model_info", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "agent.native_compaction.resolve_native_compaction_capabilities",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr("agent.credential_pool.load_pool", lambda _provider: None)
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: {})
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: {})

    agent_any.reasoning_config = {"enabled": True, "effort": start_effort}
    agent_any._cached_system_prompt = "frozen system prompt"
    agent_any._session_db = None
    agent_any.context_compressor = None
    agent_any.compression_enabled = False
    agent_any._disable_streaming = True
    monkeypatch.setattr(agent, "_try_refresh_env_client_credentials", lambda: False)
    monkeypatch.setattr(agent, "_ensure_db_session", lambda: None)
    monkeypatch.setattr(agent, "_persist_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent, "_save_trajectory", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_any, "_cleanup_task_resources", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_any, "_create_openai_client", lambda *_args, **_kwargs: MagicMock())
    monkeypatch.setattr(agent_any, "_create_request_openai_client", lambda *_args, **_kwargs: MagicMock())
    monkeypatch.setattr(agent_any, "_close_request_openai_client", lambda *_args, **_kwargs: None)

    captured = {}

    def fake_codex_request(kwargs, **_request_kwargs):
        captured.update(copy.deepcopy(kwargs))
        return SimpleNamespace(
            status="completed",
            incomplete_details=None,
            output=[SimpleNamespace(
                type="message",
                status="completed",
                content=[SimpleNamespace(type="output_text", text="routed response")],
            )],
            output_text="routed response",
            model=target_model,
            usage=None,
        )

    monkeypatch.setattr(agent_any, "_run_codex_stream", fake_codex_request)
    history_before = copy.deepcopy(history)
    tools_before = copy.deepcopy(agent_any.tools)
    result = agent_any.run_conversation("hello", conversation_history=history)

    assert result["final_response"] == "routed response"
    assert captured["model"] == target_model
    assert captured["instructions"] == "frozen system prompt"
    assert captured["reasoning"]["effort"] == target_effort
    if target_provider == "openai-codex":
        assert captured["reasoning"]["summary"] == "auto"
    assert agent_any.reasoning_config == {"enabled": True, "effort": target_effort}
    assert agent_any._cached_system_prompt == "frozen system prompt"
    assert history == history_before
    assert agent_any.tools == tools_before
    assert agent_any._primary_runtime["reasoning_config"] == {
        "enabled": True,
        "effort": target_effort,
    }
