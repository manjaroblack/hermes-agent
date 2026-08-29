"""Regression coverage for exact same-card PR continuation."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_review_recovery as krr
from hermes_cli import projects_db as pdb


HEAD_SHA = "e4b9de58701f9b90c5e2329b33eec8a9f2229c07"
NEXT_HEAD_SHA = "f5c0ef69812fa0a1d6f343ac44ffd9b0a3330d18"
PR_URL = "https://github.com/example/repo/pull/6"


def _git(cwd: Path, *args: str) -> None:
    cwd.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(cwd),
            "-c",
            "user.name=Lifecycle Test",
            "-c",
            "user.email=lifecycle@example.com",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _materialize_task_worktree(conn, task_id: str) -> kb.Task:
    task = kb.get_task(conn, task_id)
    assert task is not None
    assert task.workspace_path
    assert task.branch_name
    if not Path(task.workspace_path).exists():
        repo = Path(
            kb.read_board_metadata(kb.get_current_board())["default_workdir"]
        )
        _git(
            repo,
            "worktree",
            "add",
            str(Path(task.workspace_path)),
            "-b",
            task.branch_name,
            "HEAD",
        )
    return kb.get_task(conn, task_id)


@pytest.fixture
def conn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def identity_state(evidence):
        return {
            "pr": {
                "state": "open",
                "draft": False,
                "number": evidence.pr_number,
                "html_url": evidence.pr_url,
                "head": {
                    "sha": evidence.head_sha,
                    "ref": evidence.branch,
                },
                "base": {
                    "ref": evidence.base_branch or "main",
                    "repo": {"full_name": evidence.repository},
                },
            }
        }

    monkeypatch.setattr(
        krr,
        "fetch_live_review_identity",
        identity_state,
        raising=False,
    )
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
            name="Lifecycle project",
            primary_path=str(repo),
        )
    kb.create_board(
        "lifecycle",
        name="Lifecycle",
        default_workdir=str(repo),
        project_id=project_id,
    )
    kb.set_current_board("lifecycle")
    db = kb.connect()
    try:
        yield db
    finally:
        db.close()


def _create_task(conn, *, title="implementation", assignee="builder"):
    task_id = kb.create_task(conn, title=title, assignee=assignee)
    _materialize_task_worktree(conn, task_id)
    return task_id


def _handoff(conn, task_id, *, add_pr_comment=True):
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
    if add_pr_comment:
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


def test_direct_claim_rejects_consumed_continuation_budget(conn):
    task_id = _create_task(conn, title="direct-claim-cap")
    _task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id is not None
    _requeue_after_failure(conn, task_id, retry.current_run_id, "timed_out")

    assert kb.claim_task(conn, task_id, claimer="builder:direct") is None
    rejected = [
        event
        for event in kb.list_events(conn, task_id)
        if event.kind == "claim_rejected"
    ]
    assert rejected[-1].payload == {
        "reason": "continuation_consumed",
    }




def test_review_rework_authorization_cannot_bypass_fresh_claim_guard(conn):
    task_id = _create_task(conn, title="fresh-review-authorization")
    assert kb.claim_task(
        conn,
        task_id,
        claimer="builder:direct",
        claim_authorization="review_rework",
    ) is None
    task = kb.get_task(conn, task_id)
    assert task is not None and task.status == "ready"


def test_direct_claim_rechecks_live_identity_before_continuation(conn, monkeypatch):
    task_id = _create_task(conn, title="stale-live-identity")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    def diverged_identity(evidence):
        return {
            "pr": {
                "state": "open",
                "draft": False,
                "number": evidence.pr_number,
                "html_url": evidence.pr_url,
                "head": {"sha": NEXT_HEAD_SHA, "ref": evidence.branch},
                "base": {
                    "ref": evidence.base_branch or "main",
                    "repo": {"full_name": evidence.repository},
                },
            }
        }

    monkeypatch.setattr(krr, "fetch_live_review_identity", diverged_identity)
    assert kb.check_respawn_guard(conn, task_id) == "active_pr"
    assert kb.claim_task(conn, task_id, claimer="builder:direct") is None


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



@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("branch", "wt/foreign", "branch"),
        ("workspace_path", "/tmp/foreign-worktree", "worktree"),
    ],
)
def test_record_review_provenance_rejects_foreign_branch_or_worktree(
    conn, field, value, message
):
    task_id = _create_task(conn, title=f"foreign-{field}")
    task = kb.claim_task(conn, task_id, claimer="builder:test")
    assert task is not None and task.current_run_id is not None
    metadata = {
        "task_id": task_id,
        "worker_run_id": task.current_run_id,
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
    metadata[field] = value
    if field == "branch":
        metadata["review_evidence"]["branch"] = value
    with pytest.raises(ValueError, match=message):
        kb.record_review_provenance(
            conn,
            task_id,
            metadata,
            expected_run_id=task.current_run_id,
        )


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


def test_new_head_after_consumed_continuation_stays_guarded(conn):
    task_id = _create_task(conn, title="changed-head")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) is None
    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id is not None

    kb.record_review_provenance(
        conn,
        task_id,
        {
            "task_id": task_id,
            "worker_run_id": retry.current_run_id,
            "worker_profile": task.assignee,
            "workspace_kind": "worktree",
            "workspace_path": task.workspace_path,
            "review_evidence": {
                "provider": "github",
                "repository": "example/repo",
                "branch": task.branch_name,
                "head_sha": NEXT_HEAD_SHA,
                "pr_url": PR_URL,
                "pr_number": 6,
            },
        },
        expected_run_id=retry.current_run_id,
    )
    _requeue_after_failure(conn, task_id, retry.current_run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) == "active_pr"


def test_review_rework_after_consumed_continuation_stays_allowed(conn):
    task_id = _create_task(conn, title="retry-review-rework")
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) is None
    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id is not None
    assert kb.request_review(
        conn,
        task_id,
        summary="retry handoff",
        reviewer="reviewer",
        expected_run_id=retry.current_run_id,
    )
    review = kb.claim_review_task(conn, task_id, claimer="reviewer:test")
    assert review is not None and review.current_run_id is not None
    assert kb.request_changes(
        conn,
        task_id,
        reason="please revise",
        expected_run_id=review.current_run_id,
    ) == (True, "builder")
    timeline_now = int(time.time())
    comment_id = conn.execute(
        "SELECT id FROM task_comments WHERE task_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (task_id,),
    ).fetchone()["id"]
    with kb.write_txn(conn):
        conn.execute(
            "UPDATE task_comments SET created_at = ? WHERE id = ?",
            (timeline_now - 2, comment_id),
        )
        conn.execute(
            "UPDATE task_events SET created_at = ? "
            "WHERE task_id = ? AND kind = 'changes_requested'",
            (timeline_now - 1, task_id),
        )

    assert kb.check_respawn_guard(conn, task_id) is None
    assert kb.claim_task(conn, task_id, claimer="builder:direct") is None


def test_dispatcher_uses_explicit_review_rework_authorization_after_cap(
    conn, monkeypatch
):
    task_id = _create_task(
        conn, title="dispatcher-review-rework", assignee="hermes-coding"
    )
    task, run_id = _handoff(conn, task_id)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")
    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id is not None
    assert kb.request_review(
        conn,
        task_id,
        summary="retry handoff",
        reviewer="reviewer",
        expected_run_id=retry.current_run_id,
    )
    review = kb.claim_review_task(conn, task_id, claimer="reviewer:test")
    assert review is not None and review.current_run_id is not None
    assert kb.request_changes(
        conn,
        task_id,
        reason="please revise",
        expected_run_id=review.current_run_id,
    ) == (True, "hermes-coding")
    timeline_now = int(time.time())
    comment_id = conn.execute(
        "SELECT id FROM task_comments WHERE task_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (task_id,),
    ).fetchone()["id"]
    with kb.write_txn(conn):
        conn.execute(
            "UPDATE task_comments SET created_at = ? WHERE id = ?",
            (timeline_now - 2, comment_id),
        )
        conn.execute(
            "UPDATE task_events SET created_at = ? "
            "WHERE task_id = ? AND kind = 'changes_requested'",
            (timeline_now - 1, task_id),
        )
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

    result = kb.dispatch_once(
        conn,
        spawn_fn=lambda _task, _workspace: 123,
        max_spawn=1,
    )
    assert len(result.spawned) == 1
    claimed = [
        event
        for event in kb.list_events(conn, task_id)
        if event.kind == "claimed"
    ]
    assert isinstance(claimed[-1].payload, dict)
    assert claimed[-1].payload["claim_authorization"] == "review_rework"


def test_record_review_provenance_rejects_unknown_authority(conn, monkeypatch):
    task_id = _create_task(conn, title="unknown-authority")
    task, run_id = kb.claim_task(conn, task_id, claimer="builder:test"), None
    assert task is not None and task.current_run_id is not None
    run_id = task.current_run_id
    monkeypatch.setattr(
        krr,
        "verify_review_identity",
        lambda _evidence: (False, "identity unavailable", {}),
        raising=False,
    )

    with pytest.raises(ValueError, match="identity unavailable"):
        kb.record_review_provenance(
            conn,
            task_id,
            {
                "task_id": task_id,
                "worker_run_id": run_id,
                "worker_profile": task.assignee,
                "workspace_kind": "worktree",
                "workspace_path": task.workspace_path,
                "review_evidence": {
                    "provider": "github",
                    "repository": "does-not-exist/repo",
                    "branch": task.branch_name,
                    "head_sha": HEAD_SHA,
                    "pr_url": "https://github.com/does-not-exist/repo/pull/404",
                    "pr_number": 404,
                },
            },
            expected_run_id=run_id,
        )


def test_record_review_provenance_records_identity_without_ci_gate(conn, monkeypatch):
    task_id = _create_task(conn, title="identity-without-ci")
    task = kb.claim_task(conn, task_id, claimer="builder:test")
    assert task is not None and task.current_run_id is not None
    identity = {
        "provider": "github",
        "result": "open_non_draft_exact_identity",
        "repository": "example/repo",
        "pr_number": 6,
        "head_sha": HEAD_SHA,
        "branch": task.branch_name,
    }
    monkeypatch.setattr(
        krr,
        "verify_review_identity",
        lambda _evidence: (True, None, identity),
        raising=False,
    )

    candidate = kb.record_review_provenance(
        conn,
        task_id,
        {
            "task_id": task_id,
            "worker_run_id": task.current_run_id,
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
        },
        expected_run_id=task.current_run_id,
    )
    assert candidate["identity_verification"] == identity


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("state", "closed", "not open"),
        ("draft", True, "draft"),
        ("number", 7, "number"),
        ("html_url", "https://github.com/other/repo/pull/6", "URL"),
        ("repository", "other/repo", "repository"),
        ("branch", "foreign-branch", "branch"),
        ("head_sha", NEXT_HEAD_SHA, "head_sha"),
    ],
)
def test_review_identity_rejects_authoritative_mismatches(
    field, value, message
):
    evidence = krr.ReviewEvidence(
        provider="github",
        repository="example/repo",
        branch="wt/identity",
        head_sha=HEAD_SHA,
        pr_url=PR_URL,
        pr_number=6,
    )
    state = {
        "pr": {
            "state": "open",
            "draft": False,
            "number": 6,
            "html_url": PR_URL,
            "head": {"sha": HEAD_SHA, "ref": "wt/identity"},
            "base": {
                "ref": "main",
                "repo": {"full_name": "example/repo"},
            },
        }
    }
    if field in {"state", "draft", "number", "html_url"}:
        state["pr"][field] = value
    elif field == "repository":
        state["pr"]["base"]["repo"]["full_name"] = value
    elif field == "branch":
        state["pr"]["head"]["ref"] = value
    else:
        state["pr"]["head"]["sha"] = value

    ok, diagnostic, _snapshot = krr.verify_review_identity(evidence, state)
    assert not ok
    assert diagnostic is not None and message.casefold() in diagnostic.casefold()


def test_review_identity_accepts_open_non_draft_pr_without_ci_checks():
    evidence = krr.ReviewEvidence(
        provider="github",
        repository="example/repo",
        branch="wt/identity",
        head_sha=HEAD_SHA,
        pr_url=PR_URL,
        pr_number=6,
    )
    ok, diagnostic, snapshot = krr.verify_review_identity(
        evidence,
        {
            "pr": {
                "state": "open",
                "draft": False,
                "number": 6,
                "html_url": PR_URL,
                "head": {"sha": HEAD_SHA, "ref": "wt/identity"},
                "base": {
                    "ref": "main",
                    "repo": {"full_name": "example/repo"},
                },
            }
        },
    )
    assert ok
    assert diagnostic is None
    assert snapshot["result"] == "open_non_draft_exact_identity"


def test_structured_provenance_without_url_stays_guarded_after_retry(conn):
    task_id = _create_task(conn, title="structured-only")
    task, run_id = _handoff(conn, task_id, add_pr_comment=False)
    _requeue_after_failure(conn, task_id, run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) is None
    retry = kb.claim_task(conn, task_id, claimer="builder:retry")
    assert retry is not None and retry.current_run_id != run_id
    _requeue_after_failure(conn, task_id, retry.current_run_id, "timed_out")

    assert kb.check_respawn_guard(conn, task_id) == "active_pr"


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
