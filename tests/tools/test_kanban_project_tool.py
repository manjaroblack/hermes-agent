"""Kanban tool project/board routing contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import projects_db as pdb
from tools import kanban_tools


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(home))
    monkeypatch.delenv("HERMES_KANBAN_DB", raising=False)
    monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb._INITIALIZED_PATHS.clear()
    return home


def _project(root):
    repo = root / "repo"
    repo.mkdir()
    with pdb.connect_closing() as conn:
        return pdb.create_project(conn, name="Widget", primary_path=str(repo))


def test_gateway_create_requires_explicit_board_and_writes_requested_board(
    isolated_home, monkeypatch
):
    project_id = _project(isolated_home)
    kb.create_board("scoped", project_id=project_id)
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "discord")

    missing = json.loads(
        kanban_tools._handle_create({"title": "missing board", "assignee": "worker"})
    )
    assert "ok" in missing
    assert missing["ok"] is False
    assert "error" in missing
    assert "explicit board" in missing["error"]

    created = json.loads(
        kanban_tools._handle_create(
            {"title": "scoped task", "assignee": "worker", "board": "scoped"}
        )
    )
    assert created["ok"] is True
    with kb.connect(board="scoped") as conn:
        assert kb.get_task(conn, created["task_id"]) is not None
    with kb.connect(board="default") as conn:
        assert kb.get_task(conn, created["task_id"]) is None


def test_gateway_thread_binding_resolves_board_without_current_pointer(
    isolated_home, monkeypatch
):
    project_id = _project(isolated_home)
    kb.create_board("scoped", project_id=project_id)
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "discord")
    monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "guild-1")
    monkeypatch.setenv("HERMES_SESSION_THREAD_ID", "thread-9")

    seeded = json.loads(
        kanban_tools._handle_create(
            {"title": "seed thread binding", "assignee": "worker", "board": "scoped"}
        )
    )
    assert seeded["ok"] is True

    monkeypatch.setenv("HERMES_KANBAN_BOARD", "default")
    resolved = json.loads(
        kanban_tools._handle_create({"title": "thread child", "assignee": "worker"})
    )
    assert resolved["ok"] is True
    assert resolved["board"] == "scoped"
    with kb.connect(board="scoped") as conn:
        assert kb.get_task(conn, resolved["task_id"]) is not None


@pytest.mark.parametrize(
    "domain_board",
    ["infra", "coding", "security", "lifeos", "home", "personal"],
)
def test_gateway_create_rejects_shared_domain_board_without_project(
    isolated_home, monkeypatch, domain_board
):
    kb.create_board(domain_board, legacy_unscoped=True)
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "discord")

    result = json.loads(
        kanban_tools._handle_create(
            {"title": "new project work", "assignee": "worker", "board": domain_board}
        )
    )

    assert "ok" in result
    assert result["ok"] is False
    assert "error" in result
    assert domain_board in result["error"]
    assert "project board" in result["error"]


def test_gateway_default_assignee_does_not_infer_current_domain_board(
    isolated_home, monkeypatch
):
    kb.create_board("infra", legacy_unscoped=True)
    kb.set_current_board("infra")
    monkeypatch.delenv("HERMES_SESSION_PLATFORM", raising=False)
    monkeypatch.setenv("HERMES_SESSION_SOURCE", "discord")
    monkeypatch.setattr(
        kanban_tools,
        "load_config",
        lambda: {"kanban": {"default_assignee": "hermes-coding"}},
    )

    result = json.loads(
        kanban_tools._handle_create(
            {"title": "ambiguous durable work", "assignee": "hermes-coding"}
        )
    )

    assert "ok" in result
    assert result["ok"] is False
    assert "error" in result
    assert "explicit board/project board" in result["error"]


def test_gateway_create_schema_documents_legacy_escape():
    properties = kanban_tools.KANBAN_CREATE_SCHEMA["parameters"]["properties"]
    assert properties["legacy_unscoped"]["type"] == "boolean"
    assert "Gateway-created tasks" in properties["board"]["description"]
