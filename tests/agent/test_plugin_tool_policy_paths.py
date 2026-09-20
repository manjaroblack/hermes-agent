"""Execution-path contracts for host-owned pre-tool policy decisions."""

import copy
import json
from types import MappingProxyType, SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest


def _tool_definitions():
    return [{
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search.",
            "parameters": {"type": "object", "properties": {}},
        },
    }]


@pytest.fixture
def runtime_agent(monkeypatch):
    from run_agent import AIAgent

    with (
        patch("model_tools.get_tool_definitions", return_value=_tool_definitions()),
        patch("model_tools.check_toolset_requirements", return_value={}),
        patch("agent.process_bootstrap.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key",
            base_url="https://example.invalid/v1",
            provider="custom",
            model="test-model",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            save_trajectories=False,
        )

    agent_any = cast(Any, agent)
    agent_any._session_db = None
    agent_any._flush_messages_to_session_db = lambda _messages: True
    agent_any._append_guardrail_observation = (
        lambda _name, _args, result, **_kwargs: result
    )
    agent_any._record_file_mutation_result = lambda *_args, **_kwargs: None
    agent_any._tool_guardrails = SimpleNamespace(
        before_call=lambda _name, _args: SimpleNamespace(allows_execution=True),
        record_persisted_result=lambda *_args, **_kwargs: None,
    )
    agent_any._checkpoint_mgr = SimpleNamespace(enabled=False)
    agent_any._subdirectory_hints = SimpleNamespace(
        check_tool_call=lambda _name, _args: ""
    )
    agent_any._touch_activity = lambda *_args, **_kwargs: None
    agent_any._should_emit_quiet_tool_messages = lambda: False
    agent_any._should_start_quiet_spinner = lambda: False
    agent_any._apply_pending_steer_to_tool_results = lambda *_args, **_kwargs: None
    agent_any.tool_progress_callback = None
    agent_any.tool_start_callback = None
    agent_any.tool_complete_callback = None
    agent_any.tool_progress_mode = "off"
    agent_any._current_turn_id = "turn"
    agent_any._current_api_request_id = "request"
    return agent_any


def _activate_policy(tmp_path, monkeypatch, *, blocked):
    from hermes_cli import plugins

    manager = PluginManager(scope_key=str(tmp_path / "home"))
    manager._discovered = True
    context = PluginContext(
        PluginManifest(name="path-policy", version="1.0.0", source="test"), manager
    )
    seen = {"normal": [], "decision": []}

    def modify(args, **_kwargs):
        seen["normal"].append(copy.deepcopy(args))
        return {"action": "modify", "args": {"policy_value": "modified"}}

    def decide(args, **_kwargs):
        assert isinstance(args, MappingProxyType)
        seen["decision"].append(dict(args))
        if blocked:
            return {"action": "block", "message": "blocked by path policy"}
        return None

    context.register_hook("pre_tool_call", modify)
    context.register_hook("pre_tool_call", decide, phase="decision")
    monkeypatch.setattr(plugins, "_delivery_manager", lambda: manager)
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)
    return seen


def _run_path(path, runtime_agent, monkeypatch, handler):
    from tests.run_agent.test_run_agent import _mock_assistant_msg, _mock_tool_call

    original = {"value": "original"}
    tool_name = "web_search"

    if path == "direct_registry":
        monkeypatch.setattr(
            "model_tools.registry.dispatch",
            lambda name, args, **_kwargs: handler(name, args),
        )
        from model_tools import handle_function_call

        handle_function_call(
            tool_name,
            copy.deepcopy(original),
            task_id="task",
            session_id="session",
            turn_id="turn",
            tool_call_id="call",
        )
        return original

    if path == "direct_connector":
        tool_name = "connectors__gmail__SEND_EMAIL"
        monkeypatch.setattr(
            "model_tools._select_tool_names",
            lambda *_args, **_kwargs: ["manage_connections"],
        )
        monkeypatch.setattr(
            "model_tools_connectors.dispatch_connector_call",
            lambda name, args, _call_id: handler(name, args),
        )
        from model_tools import handle_function_call

        handle_function_call(
            tool_name,
            copy.deepcopy(original),
            task_id="task",
            session_id="session",
            turn_id="turn",
            tool_call_id="call",
        )
        return original

    if path == "sequential_inline":
        tool_name = "todo_list"
        from agent.inline_tool_executors import INLINE_TOOL_EXECUTORS

        monkeypatch.setitem(
            INLINE_TOOL_EXECUTORS,
            tool_name,
            lambda _agent, args, _ctx: handler(tool_name, args),
        )
    else:
        monkeypatch.setattr(
            "model_tools.handle_function_call",
            lambda name, args, *_pos, **_kwargs: handler(name, args),
        )

    call = _mock_tool_call(
        name=tool_name, arguments=json.dumps(original), call_id="call"
    )
    message = _mock_assistant_msg(content="", tool_calls=[call])
    messages = []
    if path in {"sequential_registry", "sequential_inline"}:
        runtime_agent._execute_tool_calls_sequential(message, messages, "task")
    elif path == "concurrent_registry":
        runtime_agent._execute_tool_calls_concurrent(message, messages, "task")
    else:
        raise AssertionError(f"unknown test path: {path}")
    return original


@pytest.mark.parametrize(
    "path",
    [
        "direct_registry",
        "direct_connector",
        "sequential_registry",
        "concurrent_registry",
        "sequential_inline",
    ],
)
@pytest.mark.parametrize("blocked", [False, True])
def test_policy_runs_once_and_dispatches_exact_final_args_on_every_execution_path(
    tmp_path, monkeypatch, runtime_agent, path, blocked
):
    seen = _activate_policy(tmp_path, monkeypatch, blocked=blocked)
    handler_calls = []

    def handler(name, args):
        handler_calls.append((name, copy.deepcopy(args)))
        return json.dumps({"ok": True})

    original = _run_path(path, runtime_agent, monkeypatch, handler)

    assert original == {"value": "original"}
    assert seen["normal"] == [{"value": "original"}]
    assert seen["decision"] == [
        {"value": "original", "policy_value": "modified"}
    ]
    if blocked:
        assert handler_calls == []
    else:
        assert len(handler_calls) == 1
        assert handler_calls[0][1] == {
            "value": "original",
            "policy_value": "modified",
        }
