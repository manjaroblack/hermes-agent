"""Fail-closed workspace admission for Kanban claims and respawns.

These tests intentionally build real git repositories/worktrees and use the
real Kanban/project stores so a task cannot bypass admission through a stale
or inherited workspace row.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.kanban_admission import admit_workspace
from hermes_cli import projects_db as pdb


@pytest.fixture
def admission_board(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    repo = tmp_path / "repo"
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")

    with pdb.connect_closing() as pconn:
        project_id = pdb.create_project(
            pconn,
            name="Admission project",
            primary_path=str(repo),
        )

    board = "admission"
    kb.create_board(
        board,
        name="Admission",
        default_workdir=str(repo),
        project_id=project_id,
    )
    kb.set_current_board(board)
    with kb.connect(board=board) as conn:
        yield {
            "board": board,
            "conn": conn,
            "project_id": project_id,
            "repo": repo,
        }


def _git(cwd: Path, *args: str) -> None:
    cwd.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(cwd),
            "-c",
            "user.name=Admission Test",
            "-c",
            "user.email=admission@example.com",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _materialize_task_worktree(repo: Path, task: kb.Task) -> None:
    assert task.workspace_path
    assert task.branch_name
    if Path(task.workspace_path).exists():
        return
    _git(
        repo,
        "worktree",
        "add",
        str(Path(task.workspace_path)),
        "-b",
        task.branch_name,
        "HEAD",
    )


def _latest_admission_event(conn, task_id: str):
    events = kb.list_events(conn, task_id)
    return next(event for event in reversed(events) if event.kind == "workspace_admission_rejected")


def test_auto_decomposed_dir_child_is_triaged_before_claim(admission_board):
    data = admission_board
    conn = data["conn"]
    root = kb.create_task(
        conn,
        title="decompose code work",
        assignee="hermes-coding",
        workspace_kind="dir",
        workspace_path=str(data["repo"]),
        triage=True,
        board=data["board"],
    )
    child_ids = kb.decompose_triage_task(
        conn,
        root,
        root_assignee="hermes-orchestrator",
        children=[{"title": "implement child", "assignee": "hermes-coding"}],
    )
    assert child_ids
    child_id = child_ids[0]
    child = kb.get_task(conn, child_id)
    assert child is not None and child.status == "ready"

    assert kb.claim_task(conn, child_id) is None

    child = kb.get_task(conn, child_id)
    assert child is not None and child.status == "triage"
    event = _latest_admission_event(conn, child_id)
    assert event.payload["reason"] in {"project_mismatch", "kind_not_worktree", "path_not_task_worktree"}
    assert event.payload["repair"]


def test_project_mismatch_is_rejected_before_claim(admission_board, tmp_path):
    data = admission_board
    conn = data["conn"]
    other_repo = tmp_path / "other-repo"
    _git(other_repo, "init", "-b", "main")
    (other_repo / "README.md").write_text("other\n", encoding="utf-8")
    _git(other_repo, "add", "README.md")
    _git(other_repo, "commit", "-m", "init")
    with pdb.connect_closing() as pconn:
        other_project_id = pdb.create_project(
            pconn,
            name="Other project",
            primary_path=str(other_repo),
        )

    task_id = kb.create_task(
        conn,
        title="wrong project",
        assignee="hermes-coding",
        board=data["board"],
    )
    with kb.write_txn(conn):
        conn.execute(
            "UPDATE tasks SET project_id = ?, workspace_kind = 'worktree', "
            "workspace_path = ?, branch_name = ? WHERE id = ?",
            (
                other_project_id,
                str(other_repo / ".worktrees" / task_id),
                f"other/{task_id}",
                task_id,
            ),
        )
    task = kb.get_task(conn, task_id)
    assert task is not None
    _materialize_task_worktree(other_repo, task)

    assert kb.claim_task(conn, task_id) is None
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "triage"
    assert _latest_admission_event(conn, task_id).payload["reason"] == "project_mismatch"


def test_non_worktree_code_card_is_rejected_before_claim(admission_board):
    data = admission_board
    conn = data["conn"]
    task_id = kb.create_task(
        conn,
        title="unsafe directory card",
        assignee="hermes-coding",
        workspace_kind="dir",
        workspace_path=str(data["repo"]),
        board=data["board"],
    )

    assert kb.claim_task(conn, task_id) is None
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "triage"
    assert _latest_admission_event(conn, task_id).payload["reason"] == "kind_not_worktree"


def test_wrong_branch_worktree_is_rejected_before_claim(admission_board):
    data = admission_board
    conn = data["conn"]
    task_id = kb.create_task(
        conn,
        title="wrong branch",
        assignee="hermes-coding",
        board=data["board"],
    )
    task = kb.get_task(conn, task_id)
    assert task is not None and task.workspace_path
    assert task.branch_name
    wrong_branch = f"sibling/{task.id}"
    _git(data["repo"], "worktree", "remove", "--force", task.workspace_path)
    _git(data["repo"], "branch", "-D", task.branch_name)
    _git(
        data["repo"],
        "worktree",
        "add",
        task.workspace_path,
        "-b",
        wrong_branch,
        "HEAD",
    )

    assert kb.claim_task(conn, task_id) is None
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "triage"
    assert _latest_admission_event(conn, task_id).payload["reason"] == "branch_identity_mismatch"


def test_valid_dedicated_worktree_is_claimed(admission_board):
    data = admission_board
    conn = data["conn"]
    task_id = kb.create_task(
        conn,
        title="valid implementation",
        assignee="hermes-coding",
        board=data["board"],
    )
    task = kb.get_task(conn, task_id)
    assert task is not None
    _materialize_task_worktree(data["repo"], task)

    claimed = kb.claim_task(conn, task_id)
    assert claimed is not None
    assert claimed.status == "running"


def test_reclaim_respawn_rechecks_workspace_admission(admission_board):
    data = admission_board
    conn = data["conn"]
    task_id = kb.create_task(
        conn,
        title="reclaim race",
        assignee="hermes-coding",
        board=data["board"],
    )
    task = kb.get_task(conn, task_id)
    assert task is not None
    _materialize_task_worktree(data["repo"], task)
    assert kb.claim_task(conn, task_id) is not None

    with kb.write_txn(conn):
        conn.execute(
            "UPDATE tasks SET workspace_path = ?, claim_expires = ? WHERE id = ?",
            (str(data["repo"]), int(time.time()) - 1, task_id),
        )

    assert kb.release_stale_claims(conn) == 1
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "ready"
    assert kb.claim_task(conn, task_id) is None
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "triage"
    assert _latest_admission_event(conn, task_id).payload["reason"] in {
        "path_not_task_worktree",
        "live_checkout_forbidden",
    }


def test_read_only_incident_and_review_lanes_remain_claimable(admission_board):
    data = admission_board
    conn = data["conn"]
    incident_id = kb.create_task(
        conn,
        title="diagnose dispatcher failure",
        assignee="hermes-incident",
        board=data["board"],
    )
    review_id = kb.create_task(
        conn,
        title="audit a candidate",
        assignee="hermes-review",
        board=data["board"],
    )
    implementation_id = kb.create_task(
        conn,
        title="implementation under review",
        assignee="hermes-coding",
        project_id=data["project_id"],
        board=data["board"],
    )
    implementation = kb.get_task(conn, implementation_id)
    assert implementation is not None and implementation.workspace_path
    review_worktree_id = kb.create_task(
        conn,
        title="review existing worktree",
        assignee="hermes-review",
        project_id=data["project_id"],
        workspace_kind="worktree",
        workspace_path=implementation.workspace_path,
        board=data["board"],
    )

    assert kb.claim_task(conn, incident_id) is not None
    assert kb.claim_task(conn, review_id) is not None
    assert kb.claim_task(conn, review_worktree_id) is not None


def test_dispatch_rejects_before_spawn_and_exposes_admission_bucket(
    admission_board, monkeypatch
):
    data = admission_board
    conn = data["conn"]
    task_id = kb.create_task(
        conn,
        title="dispatch gate",
        assignee="default",
        workspace_kind="dir",
        workspace_path=str(data["repo"]),
        board=data["board"],
    )
    spawned = []
    for name in ("resolve_workspace", "_resolve_worktree_workspace", "_ensure_git_worktree"):
        monkeypatch.setattr(
            kb,
            name,
            lambda *args, **kwargs: pytest.fail(f"workspace resolution bypassed admission: {name}"),
        )

    result = kb.dispatch_once(
        conn,
        board=data["board"],
        spawn_fn=lambda task, workspace: spawned.append((task.id, workspace)),
    )

    assert spawned == []
    assert result.workspace_admission_rejected == [(task_id, "kind_not_worktree")]
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "triage"


def test_admission_rejection_contains_repairable_evidence(admission_board):
    data = admission_board
    result = admit_workspace(
        SimpleNamespace(
            id="t_evidence",
            assignee="hermes-coding",
            workspace_kind="dir",
            workspace_path=str(data["repo"]),
            project_id=data["project_id"],
        ),
        {
            "project_id": data["project_id"],
            "default_workdir": str(data["repo"]),
        },
    )

    assert result.admitted is False
    assert result.reason == "kind_not_worktree"
    payload = result.event_payload(previous_status="ready")
    assert set(("reason", "expected", "actual", "repair")) <= payload.keys()
    assert payload["repair"]["action"] == "triage"
