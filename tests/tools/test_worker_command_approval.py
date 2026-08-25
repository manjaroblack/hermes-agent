"""Bounded worker command approval contract tests."""

from __future__ import annotations

from pathlib import Path

from tools.approval import check_all_command_guards


def test_worker_auto_approves_safe_command_inside_declared_workspace(
    monkeypatch, tmp_path: Path
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_worker")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(workspace))
    monkeypatch.delenv("HERMES_DELEGATED_CHILD_CONTEXT", raising=False)

    result = check_all_command_guards(
        "git status --short",
        "local",
        cwd=str(workspace),
    )

    assert result["approved"] is True
    assert result["worker_scope"] == "bounded"


def test_worker_blocks_commands_outside_declared_workspace(
    monkeypatch, tmp_path: Path
):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_worker")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(workspace))

    result = check_all_command_guards(
        "git status --short",
        "local",
        cwd=str(outside),
    )

    assert result["approved"] is False
    assert "workspace" in result["message"].lower()


def test_worker_stops_high_risk_remote_mutation_even_inside_workspace(
    monkeypatch, tmp_path: Path
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_worker")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(workspace))

    result = check_all_command_guards(
        "git push origin main",
        "local",
        cwd=str(workspace),
    )

    assert result["approved"] is False
    assert "worker" in result["message"].lower() or "push" in result["message"].lower()
