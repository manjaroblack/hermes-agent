"""Regression tests for durable validation of complex Kanban graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.config import DEFAULT_CONFIG
from hermes_cli.kanban_graph import validate_complex_graph



def _node(
    node_id: str,
    *,
    title: str | None = None,
    assignee: str | None = "worker",
    metadata: dict[str, Any] | None = None,
    body: str | None = None,
    status: str = "todo",
) -> dict[str, Any]:
    return {
        "id": node_id,
        "title": title or node_id,
        "body": body,
        "assignee": assignee,
        "status": status,
        "workspace_kind": "scratch",
        "metadata": metadata or {},
    }



def _config(*, max_implementation_nodes: int = 4) -> dict[str, Any]:
    return {
        "kanban": {
            "graph_validation": {
                "enabled": True,
                "required_stages": ["inventory_design", "release_acceptance"],
                "max_implementation_nodes": max_implementation_nodes,
                "security_triggers": ["permission", "safety boundary"],
            }
        }
    }



def _valid_graph(*, same_card: bool = False, security: bool = False):
    root_metadata = {"requires_orchestrator": True}
    if security:
        root_metadata["touches_security"] = True
    root = _node("root", metadata=root_metadata, status="triage")
    inventory = _node(
        "inventory",
        title="Inventory and design",
        assignee="hermes-review",
        metadata={"role": "inventory_design", "read_only": True},
    )
    implementation_metadata: dict[str, Any] = {"code_bearing": True}
    if same_card:
        implementation_metadata.update(
            {"reviewer": "hermes-review", "review_model": "same_card"}
        )
    implementation = _node(
        "implementation",
        title="Implement the change",
        assignee="hermes-coding",
        metadata=implementation_metadata,
    )
    release = _node(
        "release",
        title="Release acceptance and human merge-deploy gate",
        assignee="hermes-review",
        metadata={"role": "release_acceptance", "human_gate": True, "read_only": True},
    )
    nodes = [root, inventory, implementation, release]
    edges = [("root", "inventory"), ("root", "implementation"), ("root", "release")]
    if security:
        security_node = _node(
            "security",
            title="Security audit",
            assignee="hermes-security-audit",
            metadata={"role": "security_audit", "read_only": True},
        )
        nodes.append(security_node)
        edges.append(("root", "security"))
    if not same_card:
        review = _node(
            "review",
            title="Independent code review",
            assignee="hermes-review",
            metadata={
                "role": "independent_review",
                "review_model": "review-model-v1",
                "read_only": True,
            },
        )
        nodes.append(review)
        edges.append(("implementation", "review"))
    return root, nodes, edges



def test_default_config_declares_graph_validation_contract():
    gate = DEFAULT_CONFIG["kanban"]["graph_validation"]

    assert gate["enabled"] is True
    assert {"inventory_design", "release_acceptance"} <= set(gate["required_stages"])
    assert gate["max_implementation_nodes"] >= 1
    assert gate["security_triggers"]



def test_original_failure_rejects_complex_graph_without_inventory_review_release_edges():
    root = _node("root", metadata={"requires_orchestrator": True}, status="triage")
    implementation = _node("implementation", metadata={"code_bearing": True})

    result = validate_complex_graph(
        root,
        [root, implementation],
        [("root", "implementation")],
        config=_config(),
    )

    assert result.valid is False
    assert "inventory_design" in result.missing_stages
    assert "release_acceptance" in result.missing_stages
    assert result.repairable



def test_prose_only_review_is_not_a_review_edge():
    root, nodes, edges = _valid_graph(same_card=True)
    implementation = next(node for node in nodes if node["id"] == "implementation")
    implementation["metadata"] = {"code_bearing": True}
    implementation["body"] = "Stop for hermes-review before merge."

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert any("review" in reason for reason in result.invalid_reasons)



def test_valid_same_card_review_is_accepted():
    root, nodes, edges = _valid_graph(same_card=True)

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is True
    assert result.invalid_reasons == ()



def test_valid_downstream_review_is_accepted():
    root, nodes, edges = _valid_graph(same_card=False)

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is True
    assert result.invalid_reasons == ()


def test_hyphenated_assignees_classify_multiple_implementations():
    root, nodes, edges = _valid_graph(same_card=True)
    implementation = next(node for node in nodes if node["id"] == "implementation")
    implementation["metadata"].pop("code_bearing")
    second = _node(
        "implementation-2",
        title="Implement the second subsystem",
        assignee="hermes-coding",
        metadata={
            "reviewer": "hermes-review",
            "review_model": "same_card",
        },
    )
    nodes.append(second)
    edges.append(("root", "implementation-2"))

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is True
    assert result.implementation_ids == ("implementation", "implementation-2")


def test_role_and_assignee_stage_nodes_do_not_require_read_only_flag():
    root, nodes, edges = _valid_graph(same_card=True)
    for node_id in ("inventory", "release"):
        stage = next(node for node in nodes if node["id"] == node_id)
        stage["assignee"] = "stage-owner"
        stage["metadata"].pop("read_only")

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is True


def test_valid_chained_project_graph_accepts_reachable_stage_and_code_nodes():
    root = _node("root", metadata={"requires_orchestrator": True}, status="triage")
    inventory = _node(
        "inventory",
        assignee="inventory-owner",
        metadata={"role": "inventory_design"},
    )
    first_implementation = _node(
        "implementation-1",
        assignee="hermes-coding",
        metadata={
            "role": "implementation",
            "reviewer": "hermes-review",
            "review_model": "same_card",
        },
    )
    second_implementation = _node(
        "implementation-2",
        assignee="hermes-coding",
        metadata={
            "role": "implementation",
            "reviewer": "hermes-review",
            "review_model": "same_card",
        },
    )
    release = _node(
        "release",
        assignee="release-owner",
        metadata={"role": "release_acceptance", "human_gate": True},
    )
    nodes = [root, inventory, first_implementation, second_implementation, release]
    edges = [
        ("root", "inventory"),
        ("inventory", "implementation-1"),
        ("implementation-1", "implementation-2"),
        ("implementation-2", "release"),
    ]

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is True
    assert result.implementation_ids == ("implementation-1", "implementation-2")


def test_rollback_prose_does_not_require_incident_lane():
    root, nodes, edges = _valid_graph(same_card=True)
    root["body"] = "Document rollback and recovery steps for the release."
    config = _config()
    config["kanban"]["graph_validation"]["incident_triggers"] = [
        "rollback",
        "recovery",
    ]

    result = validate_complex_graph(root, nodes, edges, config=config)

    assert result.valid is True
    assert "incident_response" not in result.missing_stages


def test_downstream_review_requires_declared_model():
    root, nodes, edges = _valid_graph(same_card=False)
    review = next(node for node in nodes if node["id"] == "review")
    review["metadata"].pop("review_model")

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert any("no independent review model" in reason for reason in result.invalid_reasons)



def test_duplicate_review_models_are_rejected():
    root, nodes, edges = _valid_graph(same_card=False)
    second_review = _node(
        "review-2",
        title="Second independent review",
        assignee="hermes-review",
        metadata={
            "role": "independent_review",
            "review_model": "review-model-v2",
            "read_only": True,
        },
    )
    nodes.append(second_review)
    edges.append(("implementation", "review-2"))

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert any("exactly one" in reason for reason in result.invalid_reasons)



def test_same_card_plus_downstream_review_is_rejected():
    root, nodes, edges = _valid_graph(same_card=True)
    review = _node(
        "review",
        title="Independent code review",
        assignee="hermes-review",
        metadata={
            "role": "independent_review",
            "review_model": "review-model-v1",
            "read_only": True,
        },
    )
    nodes.append(review)
    edges.append(("implementation", "review"))

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert any("exactly one" in reason for reason in result.invalid_reasons)



def test_security_boundary_requires_security_audit_node():
    root, nodes, edges = _valid_graph(same_card=True, security=True)
    nodes = [node for node in nodes if node["id"] != "security"]
    edges = [edge for edge in edges if edge[1] != "security"]

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert "security_audit" in result.missing_stages


def test_incident_trigger_requires_incident_response_lane():
    root, nodes, edges = _valid_graph(same_card=True)
    root["metadata"]["incident_required"] = True

    result = validate_complex_graph(root, nodes, edges, config=_config())

    assert result.valid is False
    assert "incident_response" in result.missing_stages

    incident = _node(
        "incident",
        title="Incident response",
        assignee="hermes-incident",
        metadata={"role": "incident_response", "read_only": True},
    )
    repaired = validate_complex_graph(
        root,
        [*nodes, incident],
        [*edges, ("root", "incident")],
        config=_config(),
    )
    assert repaired.valid is True



def test_implementation_count_is_bounded_by_config():
    root, nodes, edges = _valid_graph(same_card=True)
    for index in range(4):
        node_id = f"implementation-{index}"
        nodes.append(
            _node(node_id, metadata={"code_bearing": True, "reviewer": "hermes-review", "review_model": "same_card"})
        )
        edges.append(("root", node_id))

    result = validate_complex_graph(root, nodes, edges, config=_config(max_implementation_nodes=2))

    assert result.valid is False
    assert any("bounded" in reason for reason in result.invalid_reasons)



def test_simple_one_card_fast_path_skips_validation():
    root = _node("root", metadata={"requires_orchestrator": False}, status="ready")

    result = validate_complex_graph(root, [root], [], config=_config())

    assert result.valid is True
    assert result.skipped is True


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb._INITIALIZED_PATHS.clear()
    kb.init_db()
    return home



def _events(conn, task_id: str, kind: str):
    rows = conn.execute(
        "SELECT payload FROM task_events WHERE task_id = ? AND kind = ? ORDER BY id",
        (task_id, kind),
    ).fetchall()
    return [json.loads(row["payload"]) if row["payload"] else {} for row in rows]



def test_invalid_decomposition_stays_in_triage_with_repairable_event(kanban_home):
    with kb.connect_closing() as conn:
        root_id = kb.create_task(
            conn,
            title="Complex graph",
            assignee="hermes-orchestrator",
            triage=True,
            metadata={"requires_orchestrator": True},
        )
        child_ids = kb.decompose_triage_task(
            conn,
            root_id,
            root_assignee="hermes-orchestrator",
            children=[
                {
                    "title": "Implement code",
                    "assignee": "worker",
                    "metadata": {"code_bearing": True},
                }
            ],
        )

        assert child_ids is None
        assert kb.get_task(conn, root_id).status == "triage"
        assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
        rejected = _events(conn, root_id, "graph_validation_rejected")
        assert len(rejected) == 1
        assert rejected[0]["repairable"]
        retry = kb.decompose_triage_task(
            conn,
            root_id,
            root_assignee="hermes-orchestrator",
            children=[
                {
                    "title": "Implement code",
                    "assignee": "worker",
                    "metadata": {"code_bearing": True},
                }
            ],
        )
        assert retry is None
        assert len(_events(conn, root_id, "graph_validation_rejected")) == 1



def test_decomposer_retry_is_idempotent_after_valid_graph(kanban_home):
    root, nodes, edges = _valid_graph(same_card=True)
    child_by_id = {node["id"]: node for node in nodes if node["id"] != "root"}
    children = []
    for node_id in ("inventory", "implementation", "release"):
        node = child_by_id[node_id]
        children.append(
            {
                "title": node["title"],
                "assignee": node["assignee"],
                "metadata": node["metadata"],
            }
        )

    with kb.connect_closing() as conn:
        root_id = kb.create_task(
            conn,
            title="Complex graph",
            assignee="hermes-orchestrator",
            triage=True,
            metadata={"requires_orchestrator": True},
        )
        first = kb.decompose_triage_task(
            conn,
            root_id,
            root_assignee="hermes-orchestrator",
            children=children,
        )
        count_after_first = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        second = kb.decompose_triage_task(
            conn,
            root_id,
            root_assignee="hermes-orchestrator",
            children=children,
        )
        count_after_second = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        assert first and len(first) == 3
        assert second is None
        assert count_after_second == count_after_first



def test_reclaim_to_ready_cannot_skip_graph_validation(kanban_home):
    with kb.connect_closing() as conn:
        root_id = kb.create_task(
            conn,
            title="Complex graph",
            assignee="hermes-orchestrator",
            triage=True,
            metadata={"requires_orchestrator": True},
        )
        child_id = kb.create_task(
            conn,
            title="Implement code",
            assignee="worker",
            metadata={"code_bearing": True, "graph_root_id": root_id},
        )
        conn.execute(
            "UPDATE tasks SET status = 'ready' WHERE id = ?",
            (child_id,),
        )

        assert kb.claim_task(conn, child_id, claimer="reclaim-test") is None
        assert kb.get_task(conn, root_id).status == "triage"
        assert kb.get_task(conn, child_id).status == "triage"
        rejected = _events(conn, root_id, "graph_validation_rejected")
        assert len(rejected) == 1


def test_stale_reclaim_parks_invalid_code_in_triage(kanban_home):
    with kb.connect_closing() as conn:
        root_id = kb.create_task(
            conn,
            title="Complex graph",
            assignee="hermes-orchestrator",
            triage=True,
            metadata={"requires_orchestrator": True},
        )
        child_id = kb.create_task(
            conn,
            title="Implement code",
            assignee="worker",
            metadata={"code_bearing": True, "graph_root_id": root_id},
        )
        conn.execute(
            "UPDATE tasks SET status = 'running', claim_lock = ?, "
            "claim_expires = 0 WHERE id = ?",
            ("stale-test", child_id),
        )

        assert kb.release_stale_claims(conn, signal_fn=lambda *_args: None) == 1
        child = kb.get_task(conn, child_id)
        assert child is not None and child.status == "triage"
        rejection = _events(conn, root_id, "graph_validation_rejected")
        assert rejection[-1]["phase"] == "reclaim"


def test_dispatch_does_not_spawn_invalid_graph(kanban_home):
    with kb.connect_closing() as conn:
        root_id = kb.create_task(
            conn,
            title="Complex graph",
            assignee="hermes-orchestrator",
            metadata={"requires_orchestrator": True},
            triage=True,
        )
        child_id = kb.create_task(
            conn,
            title="Implement code",
            assignee="worker",
            metadata={"code_bearing": True},
            parents=[root_id],
        )
        conn.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (root_id,))
        conn.commit()
        spawned = []

        result = kb.dispatch_once(
            conn,
            spawn_fn=lambda *args, **kwargs: spawned.append(args),
        )

        assert result.spawned == []
        assert spawned == []
        child = kb.get_task(conn, child_id)
        assert child is not None
        assert child.status == "triage"


def test_create_rejects_non_object_metadata_with_ok_false():
    from tools.kanban_tools import _handle_create

    result = json.loads(
        _handle_create(
            {
                "title": "Invalid metadata",
                "assignee": "worker",
                "metadata": ["not", "an", "object"],
            }
        )
    )

    assert result["ok"] is False
    assert "metadata must be an object" in result["error"]
