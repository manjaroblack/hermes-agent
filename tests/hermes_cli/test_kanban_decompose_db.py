"""Tests for kb.decompose_triage_task — the DB-layer atomic fan-out
from the triage column. LLM-free by design.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import projects_db as pdb


def _isolate_kanban_env(tmp_path, monkeypatch, home: Path) -> None:
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    for key in tuple(os.environ):
        if key.startswith("HERMES_KANBAN_"):
            monkeypatch.delenv(key, raising=False)
    try:
        import hermes_constants

        hermes_constants._default_hermes_root_memo = None
    except Exception:
        pass
    kb._INITIALIZED_PATHS.clear()


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    _isolate_kanban_env(tmp_path, monkeypatch, home)
    assert kb.kanban_home().resolve().is_relative_to(home.resolve())
    kb.init_db()
    return home


def _create_triage(conn, title="rough idea", body=None, assignee=None, tenant=None):
    return kb.create_task(
        conn,
        title=title,
        body=body,
        assignee=assignee,
        tenant=tenant,
        triage=True,
    )


def test_decompose_creates_children_and_promotes_root(kanban_home):
    with kb.connect() as conn:
        tid = _create_triage(conn, title="ship a feature")
        assert kb.get_task(conn, tid).status == "triage"

    children = [
        {"title": "research", "body": "look at prior art", "assignee": "researcher", "parents": []},
        {"title": "build it", "body": "write code", "assignee": "engineer", "parents": [0]},
    ]
    with kb.connect() as conn:
        child_ids = kb.decompose_triage_task(
            conn,
            tid,
            root_assignee="orchestrator",
            children=children,
            author="decomposer",
        )
    assert child_ids is not None
    assert len(child_ids) == 2

    with kb.connect() as conn:
        root = kb.get_task(conn, tid)
        c0 = kb.get_task(conn, child_ids[0])
        c1 = kb.get_task(conn, child_ids[1])

    # Root flipped to todo with orchestrator assignee, gated by children.
    assert root.status == "todo"
    assert root.assignee == "orchestrator"
    # First child has no internal parents → ready on recompute_ready.
    assert c0.status == "ready"
    assert c0.assignee == "researcher"
    # Second child has parents=[0] → stays in todo until c0 completes.
    assert c1.status == "todo"
    assert c1.assignee == "engineer"


def test_decompose_records_audit_comment_and_event(kanban_home):
    with kb.connect() as conn:
        tid = _create_triage(conn)
        child_ids = kb.decompose_triage_task(
            conn,
            tid,
            root_assignee="orch",
            children=[{"title": "task A", "assignee": "researcher"}],
            author="alice",
        )
    assert child_ids is not None

    with kb.connect() as conn:
        comments = kb.list_comments(conn, tid)
        events = kb.list_events(conn, tid)

    assert any("Decomposed into" in (c.body or "") for c in comments)
    assert any(ev.kind == "decomposed" for ev in events)


def test_decompose_missing_parents_is_parallel(kanban_home):
    with kb.connect() as conn:
        tid = _create_triage(conn)
        child_ids = kb.decompose_triage_task(
            conn,
            tid,
            root_assignee="orch",
            children=[{"title": "parallel task"}],
            author="alice",
        )

    assert child_ids is not None
    with kb.connect() as conn:
        child = kb.get_task(conn, child_ids[0])
    assert child is not None
    assert child.status == "ready"


@pytest.mark.parametrize(
    ("parents", "child_index", "child_count"),
    [
        ([-1], 1, 2),
        ([2], 1, 2),
        ([True], 2, 3),
        ([False], 1, 2),
        ([0, True], 2, 3),
    ],
    ids=["negative", "out-of-range", "true", "false", "mixed"],
)
def test_decompose_rejects_invalid_parent_indices_atomically(
    kanban_home, parents, child_index, child_count
):
    with kb.connect() as conn:
        tid = _create_triage(conn)

    children = [
        {"title": f"child {idx}", "parents": []}
        for idx in range(child_count)
    ]
    children[child_index]["parents"] = parents

    with kb.connect() as conn:
        with pytest.raises(ValueError, match="parents"):
            kb.decompose_triage_task(
                conn,
                tid,
                root_assignee="orch",
                children=children,
                author="alice",
            )

    with kb.connect() as conn:
        root = kb.get_task(conn, tid)
        task_count = conn.execute("SELECT COUNT(*) AS count FROM tasks").fetchone()["count"]
        link_count = conn.execute("SELECT COUNT(*) AS count FROM task_links").fetchone()["count"]
    assert root is not None
    assert root.status == "triage"
    assert task_count == 1
    assert link_count == 0


@pytest.fixture
def scoped_kanban_home(tmp_path, monkeypatch):
    root = tmp_path / "hermes"
    root.mkdir()
    _isolate_kanban_env(tmp_path, monkeypatch, root)

    repo = root / "repo"
    repo.mkdir()
    with pdb.connect_closing() as conn:
        project_id = pdb.create_project(
            conn, name="Scoped Project", primary_path=str(repo)
        )
        project = pdb.get_project(conn, project_id)
    assert project is not None
    kb.create_board("scoped", project_id=project.id, legacy_unscoped=False)
    return root, project


def test_decompose_scoped_children_inherit_project_scope(scoped_kanban_home):
    _root, project = scoped_kanban_home
    with kb.connect(board="scoped") as conn:
        root = kb.create_task(
            conn, title="scoped root", board="scoped", triage=True
        )
        kb.add_notify_sub(
            conn,
            task_id=root,
            platform="telegram",
            chat_id="scope-chat",
            thread_id="scope-thread",
            user_id="scope-user",
        )
        # Simulate a worker profile with no matching local projects.db. The
        # shared board snapshot must still route decomposition.
        pdb.projects_db_path().unlink()
        child_ids = kb.decompose_triage_task(
            conn,
            root,
            root_assignee="orchestrator",
            children=[
                {"title": "first child", "assignee": "alice", "parents": []},
                {"title": "second child", "assignee": "bob", "parents": [0]},
            ],
            author="decomposer",
        )
        assert child_ids is not None
        rows = [
            conn.execute(
                "SELECT project_id, legacy_unscoped, workspace_kind, "
                "workspace_path, branch_name FROM tasks WHERE id = ?",
                (child_id,),
            ).fetchone()
            for child_id in child_ids
        ]
        links = conn.execute(
            "SELECT parent_id, child_id FROM task_links WHERE child_id = ? "
            "ORDER BY parent_id",
            (root,),
        ).fetchall()
        sibling_link = conn.execute(
            "SELECT parent_id, child_id FROM task_links "
            "WHERE parent_id = ? AND child_id = ?",
            (child_ids[0], child_ids[1]),
        ).fetchone()
        child_subs = [kb.list_notify_subs(conn, child_id) for child_id in child_ids]

    assert [row["project_id"] for row in rows] == [project.id, project.id]
    assert [bool(row["legacy_unscoped"]) for row in rows] == [False, False]
    assert [row["workspace_kind"] for row in rows] == ["worktree", "worktree"]
    assert [row["workspace_path"] for row in rows] == [None, None]
    assert all(row["branch_name"].startswith(f"{project.slug}/") for row in rows)
    assert len({row["branch_name"] for row in rows}) == len(rows)
    assert [(row["parent_id"], row["child_id"]) for row in links] == [
        (child_id, root) for child_id in sorted(child_ids)
    ]
    assert sibling_link is not None
    assert (sibling_link["parent_id"], sibling_link["child_id"]) == (
        child_ids[0],
        child_ids[1],
    )
    assert [
        (sub["platform"], sub["chat_id"], sub["thread_id"], sub["user_id"])
        for subs in child_subs
        for sub in subs
    ] == [
        ("telegram", "scope-chat", "scope-thread", "scope-user"),
        ("telegram", "scope-chat", "scope-thread", "scope-user"),
    ]


def test_decompose_rejects_unscoped_root_without_partial_children(
    scoped_kanban_home,
):
    _root, _project = scoped_kanban_home
    with kb.connect(board="scoped") as conn:
        root = kb.create_task(
            conn, title="malformed scoped root", board="scoped", triage=True
        )
        conn.execute(
            "UPDATE tasks SET project_id = NULL, legacy_unscoped = 0 WHERE id = ?",
            (root,),
        )
        conn.commit()
        before_events = conn.execute(
            "SELECT COUNT(*) FROM task_events WHERE task_id = ?", (root,)
        ).fetchone()[0]

        with pytest.raises(kb.BoardProjectError) as exc_info:
            kb.decompose_triage_task(
                conn,
                root,
                root_assignee="orchestrator",
                children=[{"title": "must not be inserted", "assignee": "alice"}],
                author="decomposer",
            )

        assert exc_info.value.code == "UNSCOPED_TASK_ON_SCOPED_BOARD"
        assert conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title = ?",
            ("must not be inserted",),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM task_links WHERE child_id = ?", (root,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM task_events WHERE task_id = ?", (root,)
        ).fetchone()[0] == before_events
        root_task = kb.get_task(conn, root)
        assert root_task is not None
        assert root_task.status == "triage"


def test_decompose_preserves_explicit_legacy_scope(scoped_kanban_home):
    _root, _project = scoped_kanban_home
    with kb.connect(board="scoped") as conn:
        root = kb.create_task(
            conn,
            title="legacy root",
            board="scoped",
            triage=True,
            legacy_unscoped=True,
        )
        child_ids = kb.decompose_triage_task(
            conn,
            root,
            root_assignee="orchestrator",
            children=[{"title": "legacy child", "assignee": "alice"}],
            author="decomposer",
        )
        assert child_ids is not None
        child = conn.execute(
            "SELECT project_id, legacy_unscoped, branch_name FROM tasks WHERE id = ?",
            (child_ids[0],),
        ).fetchone()

    assert child is not None
    assert child["project_id"] is None
    assert bool(child["legacy_unscoped"]) is True
    assert child["branch_name"] is None


@pytest.mark.parametrize("parents", [True, False, None], ids=["true", "false", "null"])
def test_decompose_rejects_present_non_list_parents(kanban_home, parents):
    with kb.connect() as conn:
        tid = _create_triage(conn)

    with kb.connect() as conn:
        with pytest.raises(ValueError, match="parents must be a list"):
            kb.decompose_triage_task(
                conn,
                tid,
                root_assignee="orch",
                children=[
                    {"title": "parallel"},
                    {"title": "invalid", "parents": parents},
                ],
                author="alice",
            )




