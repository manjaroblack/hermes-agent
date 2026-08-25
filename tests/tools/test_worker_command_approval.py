"""Bounded worker command approval contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    "command",
    [
        "env -u HERMES_KANBAN_TASK gh api repos/example/project/pulls/7/merge --method PUT",
        "gh api repos/example/project/pulls/7/merge --method PUT",
        "hermes kanban delivery merge --task t_worker",
        "hermes kanban delivery controller --task t_worker --once",
        "hermes kanban delivery authorize-cutover t_worker --confirm",
    ],
)
def test_worker_blocks_delivery_and_environment_evasion_commands(
    monkeypatch, tmp_path: Path, command: str
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_worker")
    monkeypatch.setenv("HERMES_KANBAN_WORKSPACE", str(workspace))

    result = check_all_command_guards(command, "local", cwd=str(workspace))

    assert result["approved"] is False
    assert result["worker_scope"] == "high_risk"
