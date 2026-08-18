"""Project/board CLI lifecycle regressions."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from hermes_cli import kanban_db as kb
from hermes_cli import projects_cmd
from hermes_cli import projects_db as pdb


def test_project_create_with_board_is_reciprocal(tmp_path, monkeypatch):
    root = tmp_path / "hermes"
    root.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(root))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb._INITIALIZED_PATHS.clear()
    repo = tmp_path / "repo"
    repo.mkdir()

    rc = projects_cmd._cmd_create(
        Namespace(
            name="Widget",
            slug=None,
            folders=[str(repo)],
            primary=None,
            description=None,
            icon=None,
            color=None,
            board="widget",
            use=False,
        )
    )

    assert rc == 0
    with pdb.connect_closing() as conn:
        project = next(p for p in pdb.list_projects(conn) if p.slug == "widget")
        assert project.board_slug == "widget"
    board = kb.read_board_metadata("widget")
    assert board["project_id"] == project.id
    assert board["project_slug"] == "widget"
    assert board["project_primary_path"] == str(repo.resolve())


def test_project_bind_board_updates_board_snapshot(tmp_path, monkeypatch):
    root = tmp_path / "hermes"
    root.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(root))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb._INITIALIZED_PATHS.clear()
    repo = tmp_path / "repo"
    repo.mkdir()
    with pdb.connect_closing() as conn:
        pid = pdb.create_project(conn, name="Widget", folders=[str(repo)])
    kb.create_board("widget", legacy_unscoped=True)

    rc = projects_cmd._cmd_bind_board(
        Namespace(project=pid, board="widget"),
    )

    assert rc == 0
    assert kb.read_board_metadata("widget")["project_id"] == pid
