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
