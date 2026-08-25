"""Regression coverage for exact same-card PR continuation."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb


HEAD_SHA = "e4b9de58701f9b90c5e2329b33eec8a9f2229c07"
PR_URL = "https://github.com/example/repo/pull/6"


@pytest.fixture
def conn(tmp_path: Path):
    db = kb.connect(tmp_path / "kanban.db")
    try:
        yield db
    finally:
        db.close()


def _create_task(conn, *, title="implementation", assignee="builder"):
    return kb.create_task(
        conn,
        title=title,
        assignee=assignee,
        workspace_kind="worktree",
        workspace_path=f"/tmp/{title.replace(' ', '-')}",
        branch_name=f"wt/{title.replace(' ', '-')}",
    )


def _handoff(conn, task_id):
    task = kb.claim_task(conn, task_id, claimer="builder:test")
    assert task is not None and task.current_run_id is not None
    run_id = task.current_run_id
    metadata = {
        "task_id": task_id,
        "worker_run_id": run_id,
        "worker_profile": task.assignee,
        "workspace_kind": "worktree",
        "workspace_path": task.workspace_path,
        "review_evidence": {
            "provider": "github",
            "repository": "example/repo",
            "branch": task.branch_name,
            "head_sha": HEAD_SHA,
            "pr_url": PR_URL,
            "pr_number": 6,
        },
    }
    kb.record_review_provenance(
        conn, task_id, metadata, expected_run_id=run_id
    )
    kb.add_comment(conn, task_id, author="builder", body=f"PR {PR_URL}")
    return task, run_id


def _requeue_after_failure(conn, task_id, run_id, outcome):
    now = int(time.time())
    with kb.write_txn(conn):
        conn.execute(
            "UPDATE task_runs SET outcome=?, status=?, ended_at=? WHERE id=?",
            (outcome, outcome, now, run_id),
        )
        conn.execute(
            """UPDATE tasks SET status='ready', current_run_id=NULL,
               claim_lock=NULL, claim_expires=NULL WHERE id=?""",
            (task_id,),
        )


@pytest.mark.parametrize("outcome", ["timed_out", "reclaimed"])
def test_same_card_continuation_allows_one_exact_retry_then_guards_again(
    conn, outcome
):
    task_id = _create_task(conn, title=f"retry-{outcome}")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, outcome)

    assert kb.check_respawn_guard(conn, task_id) is None
    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id != run_id
    consumed = [
        event for event in kb.list_events(conn, task_id)
        if event.kind == "respawn_continuation_consumed"
    ]
    assert len(consumed) == 1
    assert isinstance(consumed[0].payload, dict)
    assert consumed[0].payload["prior_run_id"] == run_id

    _requeue_after_failure(conn, task_id, retry.current_run_id, outcome)
    assert kb.check_respawn_guard(conn, task_id) == "active_pr"


def test_blocked_same_card_continuation_survives_unblock(conn):
    task_id = _create_task(conn, title="blocked-retry")
    task, run_id = _handoff(conn, task_id)
    assert kb.block_task(
        conn,
        task_id,
        reason="review rework is pending",
        kind="needs_input",
        expected_run_id=run_id,
    )
    assert kb.unblock_task(conn, task_id)

    assert kb.check_respawn_guard(conn, task_id) is None
    assert kb.claim_task(conn, task_id, claimer="builder:retry") is not None


def test_fresh_own_pr_without_structured_handoff_stays_guarded(conn):
    task_id = _create_task(conn, title="fresh-pr")
    task = kb.claim_task(conn, task_id, claimer="builder:test")
    assert task is not None
    kb.add_comment(conn, task_id, author="builder", body=f"PR {PR_URL}")
    _requeue_after_failure(conn, task_id, task.current_run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) == "active_pr"


def test_parent_and_sibling_pr_urls_do_not_guard_current_task(conn):
    parent_id = _create_task(conn, title="parent")
    sibling_id = _create_task(conn, title="sibling")
    child_id = _create_task(conn, title="child")
    kb.link_tasks(conn, parent_id, child_id)
    kb.add_comment(conn, parent_id, author="builder", body=f"PR {PR_URL}")
    kb.add_comment(conn, sibling_id, author="builder", body=f"PR {PR_URL}")

    assert kb.check_respawn_guard(conn, child_id) is None


def test_malformed_and_foreign_handoff_identity_fail_closed(conn):
    task_id = _create_task(conn, title="identity")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    malformed = {
        "task_id": task_id,
        "worker_run_id": run_id,
        "workspace_kind": "worktree",
        "workspace_path": task.workspace_path,
        "review_evidence": {"provider": "github", "pr_url": PR_URL},
    }
    with pytest.raises(ValueError):
        kb.record_review_provenance(conn, task_id, malformed)

    foreign = {
        "task_id": "t_foreign",
        "worker_run_id": run_id,
        "worker_profile": task.assignee,
        "workspace_kind": "worktree",
        "workspace_path": task.workspace_path,
        "review_evidence": {
            "provider": "github",
            "repository": "example/repo",
            "branch": task.branch_name,
            "head_sha": HEAD_SHA,
            "pr_url": PR_URL,
            "pr_number": 6,
        },
    }
    with pytest.raises(ValueError):
        kb.record_review_provenance(conn, task_id, foreign)

    # A malformed event must not become an allow-list entry, even though the
    # task has a recent PR URL and a failed run.
    with kb.write_txn(conn):
        kb._append_event(
            conn,
            task_id,
            kb._REVIEW_PROVENANCE_EVENT,
            {"review_provenance": {"task_id": "t_foreign", "run_id": run_id}},
            run_id=run_id,
        )
    assert kb.check_respawn_guard(conn, task_id) == "active_pr"


def test_owner_requeue_with_stale_identity_does_not_duplicate(conn):
    task_id = _create_task(conn, title="owner-requeue")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "reclaimed")

    assert kb.check_respawn_guard(conn, task_id) is None
    retry = kb.claim_task(conn, task_id, claimer="builder:owner")
    assert retry is not None
    _requeue_after_failure(conn, task_id, retry.current_run_id, "reclaimed")

    assert kb.check_respawn_guard(conn, task_id) == "active_pr"
    consumed = [
        event for event in kb.list_events(conn, task_id)
        if event.kind == "respawn_continuation_consumed"
    ]
    assert len(consumed) == 1


def test_dispatcher_second_pass_does_not_spawn_duplicate(conn, monkeypatch):
    task_id = _create_task(conn, title="dispatcher-retry", assignee="hermes-coding")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")
    monkeypatch.setattr(
        "hermes_cli.profiles.profile_exists", lambda _profile: True
    )
    monkeypatch.setattr(
        kb,
        "_resolve_worktree_workspace",
        lambda current, board=None: (
            Path(current.workspace_path), current.branch_name
        ),
    )

    first = kb.dispatch_once(
        conn,
        spawn_fn=lambda _task, _workspace: 123,
        max_spawn=1,
    )
    assert len(first.spawned) == 1
    retry = kb.get_task(conn, task_id)
    assert retry is not None and retry.current_run_id is not None
    _requeue_after_failure(conn, task_id, retry.current_run_id, "timed_out")

    second = kb.dispatch_once(
        conn,
        spawn_fn=lambda _task, _workspace: pytest.fail("duplicate spawn"),
        max_spawn=1,
    )
    assert second.spawned == []
    assert (task_id, "active_pr") in second.respawn_guarded
