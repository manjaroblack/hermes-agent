"""Behavior contracts for the generic fork plugin host surfaces."""

import threading
from types import MappingProxyType

import pytest

from hermes_cli import plugins
from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest
from model_tools import handle_function_call


def _manager(tmp_path):
    manager = PluginManager(scope_key=str(tmp_path / "home"))
    manager._discovered = True
    return manager


def _context(manager):
    return PluginContext(
        PluginManifest(name="test-plugin", version="1.0.0", source="test"), manager
    )


def test_plugin_context_exposes_only_implemented_capability_markers(tmp_path):
    context = _context(_manager(tmp_path))

    assert context.capabilities == frozenset({
        "pre_llm_call.model_switch.v1",
        "pre_tool_call.decision.v1",
        "skills.snapshot.v1",
    })
    assert isinstance(context.capabilities, frozenset)


def test_skill_snapshot_surface_fails_closed_without_a_published_session(tmp_path):
    context = _context(_manager(tmp_path))

    assert context.skills_snapshot() is None


def test_pre_tool_hook_phase_is_validated_and_keeps_registration_order(tmp_path):
    manager = _manager(tmp_path)
    context = _context(manager)
    normal = lambda **_: None
    decision = lambda **_: None

    context.register_hook("pre_tool_call", normal)
    context.register_hook("pre_tool_call", decision, phase="decision")

    assert manager.iter_hook_callbacks_with_phase("pre_tool_call") == (
        (normal, "normal"), (decision, "decision")
    )
    assert manager.get_hook_registration_generation("pre_tool_call") == 2

    with pytest.raises(ValueError, match="phase"):
        context.register_hook("pre_tool_call", lambda **_: None, phase="late")


def test_generic_pre_tool_dispatch_skips_decision_phase_callbacks(tmp_path):
    manager = _manager(tmp_path)
    context = _context(manager)
    called = []
    context.register_hook("pre_tool_call", lambda **_: called.append("normal"))
    context.register_hook("pre_tool_call", lambda **_: called.append("decision"), phase="decision")

    assert manager.invoke_hook("pre_tool_call", tool_name="demo", args={}) == []
    assert called == ["normal"]


def test_decision_chain_sees_composed_detached_final_args_and_approval_is_bound(tmp_path, monkeypatch):
    manager = _manager(tmp_path)
    context = _context(manager)
    seen = []
    approvals = []

    def modify(args):
        return {"action": "modify", "args": {"added": True, "nested": {"b": 2}}}

    def approve(args):
        seen.append(args)
        assert isinstance(args, MappingProxyType)
        with pytest.raises(TypeError):
            args["mutated"] = True
        return {"action": "approve"}

    context.register_hook("pre_tool_call", modify)
    context.register_hook("pre_tool_call", approve, phase="decision")
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)

    def approve_native(tool_name, reason, *, rule_key="", approval_callback=None):
        approvals.append((tool_name, reason, rule_key))
        return {"approved": True}

    monkeypatch.setattr("tools.approval.request_tool_approval", approve_native)
    original = {"nested": {"a": 1}}

    block, modified = plugins._dispatch_pre_tool_call_hooks(
        "demo_tool", original, session_id="session", tool_call_id="call"
    )

    assert block is None
    assert modified == {"nested": {"b": 2}, "added": True}
    assert original == {"nested": {"a": 1}}
    assert seen == [MappingProxyType({"nested": {"b": 2}, "added": True})]
    assert len(approvals) == 1
    assert approvals[0][0] == "demo_tool"
    assert "execution nonce" not in approvals[0][1].lower()
    assert approvals[0][2].startswith("pre_tool_call:")


def test_decision_block_and_malformed_results_fail_closed_without_approval(tmp_path, monkeypatch):
    manager = _manager(tmp_path)
    context = _context(manager)
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)
    approval = lambda **_: {"approved": True}
    monkeypatch.setattr("tools.approval.request_tool_approval", approval)

    context.register_hook("pre_tool_call", lambda **_: {"action": "approve"})
    context.register_hook("pre_tool_call", lambda **_: {"action": "block", "message": "denied"}, phase="decision")
    assert plugins._dispatch_pre_tool_call_hooks("demo", {}) == ("denied", None)

    manager.unload()
    manager._discovered = True
    context = _context(manager)
    context.register_hook("pre_tool_call", lambda **_: {"action": "not-valid"}, phase="decision")
    block, modified = plugins._dispatch_pre_tool_call_hooks("demo", {})
    assert block == "BLOCKED: malformed pre_tool_call decision"
    assert modified is None


def test_normal_and_decision_chains_stop_at_their_first_directives(
    tmp_path, monkeypatch
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    events = []

    def add_and_replace(**_kwargs):
        events.append("add-and-replace")
        return {"action": "modify", "args": {"added": True, "replace": "after"}}

    def replace_nested(**_kwargs):
        events.append("replace-nested")
        return {"action": "modify", "args": {"nested": {"b": 2}}}

    def normal_approve(**_kwargs):
        events.append("normal-approve")
        return {"action": "approve"}

    def skipped_normal_block(**_kwargs):
        events.append("skipped-normal-block")
        return {"action": "block", "message": "must not run"}

    def undecided(**_kwargs):
        events.append("decision-none")
        return None

    def decision_block(**_kwargs):
        events.append("decision-block")
        return {"action": "block", "message": "decision denied"}

    def skipped_decision_approve(**_kwargs):
        events.append("skipped-decision-approve")
        return {"action": "approve"}

    context.register_hook("pre_tool_call", add_and_replace)
    context.register_hook("pre_tool_call", replace_nested)
    context.register_hook("pre_tool_call", normal_approve)
    context.register_hook("pre_tool_call", skipped_normal_block)
    context.register_hook("pre_tool_call", undecided, phase="decision")
    context.register_hook("pre_tool_call", decision_block, phase="decision")
    context.register_hook("pre_tool_call", skipped_decision_approve, phase="decision")
    monkeypatch.setattr(
        "tools.approval.request_tool_approval",
        lambda *_args, **_kwargs: pytest.fail("hard block reached approval resolver"),
    )

    result = evaluate_pre_tool_call(
        "demo",
        {"replace": "before", "nested": {"a": 1}},
        manager=manager,
    )

    assert result.block_message == "decision denied"
    assert result.args == {
        "replace": "after",
        "nested": {"b": 2},
        "added": True,
    }
    assert result.binding is None
    assert events == [
        "add-and-replace",
        "replace-nested",
        "normal-approve",
        "decision-none",
        "decision-block",
    ]


def test_first_decision_approval_stops_later_decision_block(tmp_path, monkeypatch):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    events = []
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: events.append("normal-approve") or {"action": "approve"},
    )
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: events.append("decision-none") or None,
        phase="decision",
    )
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: events.append("decision-approve") or {"action": "approve"},
        phase="decision",
    )
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: events.append("late-block")
        or {"action": "block", "message": "too late"},
        phase="decision",
    )
    approvals = []
    monkeypatch.setattr(
        "tools.approval.request_tool_approval",
        lambda *_args, **_kwargs: approvals.append(True) or {"approved": True},
    )

    result = evaluate_pre_tool_call("demo", {"value": 1}, manager=manager)

    assert result.block_message is None
    assert result.binding is not None
    assert approvals == [True]
    assert events == ["normal-approve", "decision-none", "decision-approve"]


def test_normal_hard_block_stops_before_decision_and_native_approval(
    tmp_path, monkeypatch
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: {"action": "block", "message": "normal denied"},
    )
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: pytest.fail("decision ran after normal hard block"),
        phase="decision",
    )
    monkeypatch.setattr(
        "tools.approval.request_tool_approval",
        lambda *_args, **_kwargs: pytest.fail("normal hard block reached approval resolver"),
    )

    result = evaluate_pre_tool_call("demo", {"value": 1}, manager=manager)

    assert result.block_message == "normal denied"
    assert result.binding is None


def test_native_approval_scope_key_is_stable_for_the_same_policy_and_args(tmp_path, monkeypatch):
    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook("pre_tool_call", lambda **_: {"action": "approve"}, phase="decision")
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)
    keys = []

    def approve_native(_tool_name, _reason, *, rule_key="", approval_callback=None):
        keys.append(rule_key)
        return {"approved": True}

    monkeypatch.setattr("tools.approval.request_tool_approval", approve_native)
    assert plugins._dispatch_pre_tool_call_hooks("demo", {"value": 1}) == (None, None)
    assert plugins._dispatch_pre_tool_call_hooks("demo", {"value": 1}) == (None, None)
    assert len(keys) == 2
    assert keys[0] == keys[1]


def test_changed_args_get_distinct_approval_keys_and_execution_nonces(
    tmp_path, monkeypatch
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    nonces = []
    context.register_hook(
        "pre_tool_call",
        lambda execution_nonce, **_kwargs: nonces.append(execution_nonce)
        or {"action": "approve"},
        phase="decision",
    )
    keys = []

    def approve_native(_tool_name, _reason, *, rule_key="", approval_callback=None):
        keys.append(rule_key)
        return {"approved": True}

    monkeypatch.setattr("tools.approval.request_tool_approval", approve_native)

    first = evaluate_pre_tool_call("demo", {"value": 1}, manager=manager)
    second = evaluate_pre_tool_call("demo", {"value": 2}, manager=manager)

    assert first.block_message is second.block_message is None
    assert first.binding is not None and second.binding is not None
    assert len(set(keys)) == 2
    assert len(set(nonces)) == 2
    assert not first.binding.verify(manager, "demo", second.args)


def test_policy_binding_rejects_registration_or_argument_changes(tmp_path):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook("pre_tool_call", lambda **_kwargs: None, phase="decision")
    result = evaluate_pre_tool_call("demo", {"value": 1}, manager=manager)

    assert result.binding is not None
    assert result.binding.verify(manager, "demo", {"value": 1})
    assert not result.binding.verify(manager, "demo", {"value": 2})

    context.register_hook("pre_tool_call", lambda **_kwargs: None, phase="decision")
    assert not result.binding.verify(manager, "demo", {"value": 1})


def test_execution_nonce_entropy_failure_blocks_before_callbacks(tmp_path, monkeypatch):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: pytest.fail("callback ran without an execution nonce"),
        phase="decision",
    )
    monkeypatch.setattr(
        "hermes_cli.plugins_policy.secrets.token_hex",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("entropy unavailable")),
    )

    result = evaluate_pre_tool_call("demo", {}, manager=manager)

    assert result.block_message == "BLOCKED: pre_tool_call execution identity unavailable"
    assert result.binding is None


def test_decision_callback_exception_is_a_static_block(tmp_path, monkeypatch):
    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook("pre_tool_call", lambda **_: (_ for _ in ()).throw(RuntimeError("boom")), phase="decision")
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)

    block, modified = plugins._dispatch_pre_tool_call_hooks("demo", {})

    assert block == "BLOCKED: pre_tool_call decision failed"
    assert modified is None


def test_policy_registry_failure_fails_closed(tmp_path, monkeypatch):
    class BrokenManager:
        def get_hook_registration_generation(self, _hook_name):
            return 1

        def iter_hook_callbacks_with_phase(self, _hook_name):
            raise RuntimeError("registry unavailable")

    monkeypatch.setattr(plugins, "_delivery_manager", lambda: BrokenManager())

    block, modified = plugins._dispatch_pre_tool_call_hooks("demo", {})

    assert block == "BLOCKED: pre_tool_call decision failed"
    assert modified is None


def test_legacy_tool_executor_path_keeps_first_directive_reducer(tmp_path, monkeypatch):
    from agent.tool_executor import _ToolCallRef, _pre_tool_block

    _manager(tmp_path)
    ref = _ToolCallRef("demo", {"original": True}, "task", "call", [])
    agent = object()
    monkeypatch.setattr("hermes_cli.plugins.has_pre_tool_call_decision_phase", lambda: False)
    monkeypatch.setattr(
        "hermes_cli.plugins._dispatch_pre_tool_call_hooks",
        lambda *args, **kwargs: ("legacy block", {"modified": True}),
    )
    monkeypatch.setattr(
        "hermes_cli.plugins.evaluate_pre_tool_call",
        lambda *args, **kwargs: pytest.fail("decision evaluator used for legacy-only hooks"),
    )

    assert _pre_tool_block(agent, ref) == ("legacy block", {"modified": True}, None)


def test_decision_policy_runs_after_execution_middleware_before_registry_dispatch(tmp_path, monkeypatch):
    manager = _manager(tmp_path)
    context = _context(manager)
    seen = {}

    def execution_middleware(**kwargs):
        return kwargs["next_call"]({**kwargs["args"], "middleware": True})

    def normal(args):
        return {"action": "modify", "args": {"normal": True}}

    def decision(args):
        seen["args"] = args
        return {"action": "approve"}

    context.register_middleware("tool_execution", execution_middleware)
    context.register_hook("pre_tool_call", normal)
    context.register_hook("pre_tool_call", decision, phase="decision")
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)
    monkeypatch.setattr("tools.approval.request_tool_approval", lambda *a, **k: {"approved": True})

    def dispatch(_name, args, **_kwargs):
        seen["dispatched"] = args
        return {"ok": True}

    monkeypatch.setattr(
        "model_tools.registry.dispatch",
        dispatch,
    )

    output = handle_function_call("web_search", {"query": "original"}, session_id="session", tool_call_id="call")

    assert output
    assert seen["args"] == {"query": "original", "middleware": True, "normal": True}
    assert seen["dispatched"] == {"query": "original", "middleware": True, "normal": True}


def test_direct_execution_middleware_cannot_dispatch_an_approved_call_twice(
    tmp_path, monkeypatch
):
    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook("pre_tool_call", lambda **_kwargs: None, phase="decision")

    def duplicate_dispatch(**kwargs):
        kwargs["next_call"](kwargs["args"])
        return kwargs["next_call"](kwargs["args"])

    context.register_middleware("tool_execution", duplicate_dispatch)
    monkeypatch.setattr(plugins, "get_plugin_manager", lambda: manager)
    handler_calls = []

    def dispatch(name, args, **_kwargs):
        handler_calls.append((name, dict(args)))
        return {"ok": True}

    monkeypatch.setattr("model_tools.registry.dispatch", dispatch)

    output = handle_function_call(
        "web_search", {"query": "only once"}, session_id="session", tool_call_id="call"
    )

    assert len(handler_calls) == 1
    assert output == {"ok": True}


def _reset_native_approval_state(approval):
    with approval._lock:
        approval._pending.clear()
        approval._session_approved.clear()
        approval._session_yolo.clear()
        approval._permanent_approved.clear()


def _configure_interactive_native_approval(monkeypatch, approval, choice, prompts):
    from tools import approval_context

    _reset_native_approval_state(approval)
    monkeypatch.setattr(approval, "_YOLO_MODE_FROZEN", False)
    monkeypatch.setattr(approval, "_is_interactive_cli", lambda: True)
    monkeypatch.setattr(approval, "_is_gateway_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_single_query_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_cron_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_unattended_platform_approval_context", lambda: False)
    monkeypatch.setattr(approval, "save_permanent_allowlist", lambda _patterns: None)
    monkeypatch.setattr(approval_context, "_fire_approval_hook", lambda *_args, **_kwargs: None)

    def prompt(*_args, **_kwargs):
        prompts.append(choice)
        return choice

    monkeypatch.setattr(approval, "prompt_dangerous_approval", prompt)


@pytest.mark.parametrize(
    ("choice", "attempts", "expected_prompts", "expected_allowed"),
    [
        ("once", 2, 2, [True, True]),
        ("session", 2, 1, [True, True]),
        ("always", 2, 1, [True, True]),
        ("deny", 1, 1, [False]),
        ("timeout", 1, 1, [False]),
    ],
)
def test_decision_approval_uses_native_once_session_always_deny_and_timeout_semantics(
    tmp_path, monkeypatch, choice, attempts, expected_prompts, expected_allowed
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call
    from tools import approval
    from tools.approval_context import reset_current_session_key, set_current_session_key

    manager = _manager(tmp_path)
    context = _context(manager)
    nonces = []

    def require_approval(execution_nonce, **_kwargs):
        nonces.append(execution_nonce)
        return {"action": "approve"}

    context.register_hook("pre_tool_call", require_approval, phase="decision")
    prompts = []
    _configure_interactive_native_approval(monkeypatch, approval, choice, prompts)
    token = set_current_session_key("approval-session")
    try:
        results = [
            evaluate_pre_tool_call(
                "demo_tool",
                {"value": 1},
                manager=manager,
                hook_kwargs={"session_id": "session", "tool_call_id": "reused-call"},
            )
            for _ in range(attempts)
        ]
    finally:
        reset_current_session_key(token)
        _reset_native_approval_state(approval)

    assert [result.block_message is None for result in results] == expected_allowed
    assert len(prompts) == expected_prompts
    assert len(nonces) == attempts
    assert len(set(nonces)) == attempts


@pytest.mark.parametrize("hook_kwargs", [{}, {"tool_call_id": "reused-call"}])
def test_missing_or_reused_host_ids_never_reuse_execution_bindings(
    tmp_path, monkeypatch, hook_kwargs
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call
    from tools import approval
    from tools.approval_context import reset_current_session_key, set_current_session_key

    manager = _manager(tmp_path)
    context = _context(manager)
    payloads = []

    def require_approval(**kwargs):
        payloads.append(kwargs)
        return {"action": "approve"}

    context.register_hook("pre_tool_call", require_approval, phase="decision")
    prompts = []
    _configure_interactive_native_approval(monkeypatch, approval, "once", prompts)
    token = set_current_session_key("approval-session")
    try:
        results = [
            evaluate_pre_tool_call(
                "demo_tool", {"value": 1}, manager=manager, hook_kwargs=hook_kwargs
            )
            for _ in range(2)
        ]
    finally:
        reset_current_session_key(token)
        _reset_native_approval_state(approval)

    assert all(result.block_message is None for result in results)
    assert len(prompts) == 2
    assert payloads[0].get("tool_call_id") == payloads[1].get("tool_call_id")
    assert payloads[0]["execution_nonce"] != payloads[1]["execution_nonce"]


@pytest.mark.parametrize("surface", ["yolo", "cron", "unattended"])
def test_native_bypass_modes_cannot_weaken_a_plugin_hard_block(
    tmp_path, monkeypatch, surface
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call
    from tools import approval
    from tools.approval_context import reset_current_session_key, set_current_session_key

    _reset_native_approval_state(approval)
    monkeypatch.setattr(approval, "_YOLO_MODE_FROZEN", False)
    monkeypatch.setattr(approval, "_is_interactive_cli", lambda: False)
    monkeypatch.setattr(approval, "_is_gateway_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_single_query_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_cron_approval_context", lambda: surface == "cron")
    monkeypatch.setattr(
        approval, "_is_unattended_platform_approval_context", lambda: surface == "unattended"
    )

    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook(
        "pre_tool_call",
        lambda **_kwargs: {"action": "block", "message": "policy hard block"},
        phase="decision",
    )
    token = set_current_session_key("approval-session")
    if surface == "yolo":
        approval.enable_session_yolo("approval-session")
    try:
        result = evaluate_pre_tool_call(
            "demo_tool", {}, manager=manager, hook_kwargs={"session_id": "session"}
        )
    finally:
        reset_current_session_key(token)
        _reset_native_approval_state(approval)

    assert result.block_message == "policy hard block"
    assert result.binding is None


def test_plugin_approval_fails_closed_when_no_human_is_available(tmp_path, monkeypatch):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call
    from tools import approval

    _reset_native_approval_state(approval)
    monkeypatch.setattr(approval, "_YOLO_MODE_FROZEN", False)
    monkeypatch.setattr(approval, "_is_interactive_cli", lambda: False)
    monkeypatch.setattr(approval, "_is_gateway_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_single_query_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_cron_approval_context", lambda: False)
    monkeypatch.setattr(approval, "_is_unattended_platform_approval_context", lambda: False)

    manager = _manager(tmp_path)
    context = _context(manager)
    context.register_hook(
        "pre_tool_call", lambda **_kwargs: {"action": "approve"}, phase="decision"
    )

    result = evaluate_pre_tool_call("demo_tool", {}, manager=manager, hook_kwargs={})

    assert result.block_message == "BLOCKED: plugin approval could not be completed"
    assert result.binding is None


def test_timed_out_decision_callback_fails_closed_and_late_result_is_discarded(
    tmp_path, monkeypatch
):
    from hermes_cli.plugins_policy import evaluate_pre_tool_call

    manager = _manager(tmp_path)
    context = _context(manager)
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def late_approval(**_kwargs):
        started.set()
        release.wait(timeout=2.0)
        finished.set()
        return {"action": "approve"}

    context.register_hook("pre_tool_call", late_approval, phase="decision")
    monkeypatch.setattr(plugins, "_resolve_hook_callback_timeout", lambda: 0.05)
    monkeypatch.setattr(
        "tools.approval.request_tool_approval",
        lambda *_args, **_kwargs: pytest.fail("late policy result reached approval gate"),
    )
    try:
        result = evaluate_pre_tool_call(
            "demo_tool", {}, manager=manager, hook_kwargs={"tool_call_id": "call"}
        )
        assert started.wait(timeout=1.0)
        assert result.block_message == "BLOCKED: pre_tool_call decision failed"
        assert result.binding is None

        release.set()
        assert finished.wait(timeout=1.0)
        assert result.block_message == "BLOCKED: pre_tool_call decision failed"
        assert result.binding is None
    finally:
        release.set()
