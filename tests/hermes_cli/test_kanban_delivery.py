from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.kanban_delivery import (
    DeliveryBlocked,
    DeliveryConflict,
    DeliveryCoordinator,
    DeliveryStateError,
    GhGitHubAdapter,
    ReviewPacket,
    SubprocessGitAdapter,
    canonical_json,
    classify_delivery_risk,
    normalize_branch,
)


class FakeGit:
    def __init__(self, repo: Path):
        self.repo = repo
        self.calls: list[tuple[str, ...]] = []
        self.head = "1" * 40
        self.base = "2" * 40
        self.remote_url = "https://github.com/example/project.git"

    def validate_repository(self, path: Path):
        self.calls.append(("validate_repository", str(path)))
        return {"root": str(self.repo), "common_dir": str(self.repo / ".git")}

    def remote_url_for(self, path: Path, remote: str):
        self.calls.append(("remote_url_for", str(path), remote))
        return self.remote_url

    def rev_parse(self, path: Path, ref: str):
        self.calls.append(("rev_parse", str(path), ref))
        return self.base if ref == "main" else self.head

    def commit(self, path: Path, message: str, paths=None):
        self.calls.append(("commit", str(path), message))
        return {"sha": self.head, "parent_sha": "0" * 40}

    def push(self, path: Path, remote: str, branch: str, head_sha: str):
        self.calls.append(("push", str(path), remote, branch, head_sha))
        return {"remote": remote, "branch": branch, "head_sha": head_sha}

    def fetch(self, path: Path, remote: str, ref: str):
        self.calls.append(("fetch", str(path), remote, ref))
        return {"remote": remote, "ref": ref, "sha": "4" * 40, "transport": "test-fetch"}


class CrashAfterPushGit(FakeGit):
    def __init__(self, repo: Path):
        super().__init__(repo)
        self.remote_sha = None
        self.push_calls = 0

    def push(self, path: Path, remote: str, branch: str, head_sha: str):
        self.push_calls += 1
        self.remote_sha = head_sha
        raise TimeoutError("connection lost after remote push")

    def remote_head(self, path: Path, remote: str, branch: str):
        return self.remote_sha


class FakeGitHub:
    def __init__(self):
        self.merge_calls = 0
        self.pr = {
            "number": 7,
            "html_url": "https://github.com/example/project/pull/7",
            "state": "open",
            "draft": False,
            "head": {"ref": "feature/t_test", "sha": "1" * 40},
            "base": {"ref": "main", "sha": "2" * 40},
        }

    def get_pr(self, repository: str, number: int):
        return dict(self.pr)

    def find_pr(self, repository: str, head: str, base: str):
        return dict(self.pr) if head == "feature/t_test" and base == "main" else None

    def request_review(self, repository: str, number: int, reviewer: str):
        return {"reviewer": reviewer, "number": number}

    def current_user(self):
        return "owner"

    def get_required_checks(self, repository: str, branch: str, head_sha: str):
        return {
            "head_sha": head_sha,
            "runs": [{"id": 1, "name": "tests", "status": "completed", "conclusion": "success", "head_sha": head_sha}],
            "checked_at": 1000,
        }

    def get_reviews(self, repository: str, number: int):
        return {
            "reviews": [{
                "id": 1,
                "state": "approved",
                "user": {"login": "reviewer"},
                "commit_id": self.pr["head"]["sha"],
                "submitted_at": "1970-01-01T00:16:40Z",
                "model_family": "reviewer-family",
            }]
        }

    def get_branch_protection(self, repository: str, branch: str):
        return {
            "enabled": True,
            "branch": branch,
            "required_status_checks": {"contexts": ["tests"]},
        }

    def merge_pr(self, repository: str, number: int, method: str, head_sha: str):
        self.merge_calls += 1
        assert head_sha == self.pr["head"]["sha"]
        self.pr = {**self.pr, "state": "merged", "merge_commit_sha": "3" * 40}
        return {
            "merged": True,
            "sha": "3" * 40,
            "message": "Pull Request successfully merged",
            "actor": "owner",
            "method": method,
        }


class CrashAfterCreateGitHub(FakeGitHub):
    def __init__(self):
        super().__init__()
        self.create_calls = 0

    def find_pr(self, repository: str, head: str, base: str):
        if self.create_calls:
            return dict(self.pr)
        return None

    def create_pr(self, repository: str, head: str, base: str, title: str, body: str):
        self.create_calls += 1
        raise TimeoutError("connection lost after GitHub accepted PR creation")


class SyncGitHub(FakeGitHub):
    def __init__(self):
        super().__init__()
        self.pr = {
            "number": 8,
            "html_url": "https://github.com/example/project/pull/8",
            "state": "open",
            "draft": False,
            "head": {"ref": "sync/t_test", "sha": "5" * 40},
            "base": {"ref": "main", "sha": "2" * 40},
        }


def _make_task(tmp_path: Path) -> tuple[object, Path]:
    db_path = tmp_path / "kanban.db"
    kb.init_db(db_path)
    conn = kb.connect(db_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    kb.create_task(
        conn,
        title="delivery",
        assignee="hermes-coding",
        workspace_kind="dir",
        workspace_path=str(repo),
        initial_status="running",
    )
    return conn, repo


def _packet() -> ReviewPacket:
    return ReviewPacket.from_mapping(
        {
            "provider": "github",
            "repository": "example/project",
            "remote": "origin",
            "pr_url": "https://github.com/example/project/pull/7",
            "pr_number": 7,
            "branch": "feature/t_test",
            "head_sha": "1" * 40,
            "base_branch": "main",
            "base_sha": "2" * 40,
            "review": {"decision": "approved", "actor": "reviewer", "reviewed_at": 1000},
            "checks": {
                "policy": "required",
                "exact_head_sha": "1" * 40,
                "all_required": True,
                "runs": [{"id": 1, "name": "tests", "status": "completed", "conclusion": "success"}],
                "checked_at": 1000,
            },
        }
    )


def _sync_packet() -> ReviewPacket:
    return ReviewPacket.from_mapping(
        {
            "provider": "github",
            "repository": "example/project",
            "remote": "origin",
            "pr_url": "https://github.com/example/project/pull/8",
            "pr_number": 8,
            "branch": "sync/t_test",
            "head_sha": "5" * 40,
            "base_branch": "main",
            "base_sha": "2" * 40,
            "review": {"decision": "approved", "actor": "reviewer", "reviewed_at": 1000},
            "checks": {
                "policy": "required",
                "exact_head_sha": "5" * 40,
                "all_required": True,
                "runs": [{"id": 2, "name": "tests", "status": "completed", "conclusion": "success"}],
                "checked_at": 1000,
            },
        }
    )


def test_review_packet_hash_is_canonical_and_exact_head_is_immutable():
    packet = _packet()
    assert packet.head_sha == "1" * 40
    assert packet.packet_hash == hashlib.sha256(
        canonical_json(packet.as_dict()).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="exact_head_sha"):
        ReviewPacket.from_mapping(
            {**packet.as_dict(), "checks": {"exact_head_sha": "f" * 40, "all_required": True}}
        )


@pytest.mark.parametrize("branch", ["feature/../main", "feature?state=all", "feature#fragment", "feature~1", "feature@{1}"])
def test_branch_names_cannot_escape_git_ref_or_provider_endpoint(branch: str):
    with pytest.raises(ValueError):
        normalize_branch(branch)


def _prepare_delivery(
    tmp_path: Path,
    provider: FakeGitHub,
    *,
    authorize: bool = True,
    record_review: bool = True,
):
    conn, repo = _make_task(tmp_path)
    coordinator = DeliveryCoordinator(conn, git=FakeGit(repo), github=provider, now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="1" * 40)
    coordinator.commit(task_id, message="test delivery", paths=["changed.py"])
    coordinator.push(task_id)
    coordinator.open_pr(task_id, title="test delivery", body="test")
    packet = _packet()
    if record_review:
        coordinator.record_review_and_checks(task_id, packet)
    if authorize:
        coordinator.authorize_merge(
            task_id,
            actor="owner",
            source="operator_cli",
            packet_hash=packet.packet_hash,
            method="squash",
            reason="explicit test authorization",
            confirmation=True,
        )
    return conn, coordinator, task_id, packet


class MovingHeadGitHub(FakeGitHub):
    def __init__(self):
        super().__init__()
        self.merge_head_sha = None

    def merge_pr(self, repository: str, number: int, method: str, head_sha: str):
        self.merge_calls += 1
        self.merge_head_sha = head_sha
        self.pr = {
            **self.pr,
            "head": {**self.pr["head"], "sha": "f" * 40},
            "state": "merged",
            "merge_commit_sha": "3" * 40,
        }
        return {"merged": True, "sha": "3" * 40, "actor": "owner", "method": method}


class BrokenLiveEvidenceGitHub(FakeGitHub):
    def get_required_checks(self, repository: str, branch: str, head_sha: str):
        raise RuntimeError("live checks unavailable")


class HistoricalReviewGitHub(FakeGitHub):
    def get_reviews(self, repository: str, number: int):
        current = super().get_reviews(repository, number)["reviews"][0]
        return {
            "reviews": [
                {**current, "id": 0, "commit_id": "e" * 40, "state": "commented"},
                current,
            ]
        }


def test_default_policy_fail_closes_high_risk_python_and_root_credentials():
    for path in (
        "hermes_cli/auth.py",
        "agent/secret_scope.py",
        "run_agent.py",
        "tools/kanban_tools.py",
        "cli.py",
        "secret.pem",
        "server.key",
    ):
        decision = classify_delivery_risk([path], target_policy="fork_only")
        assert decision.tier == "C", path


def test_historical_reviews_do_not_override_current_exact_head_approval(tmp_path: Path):
    conn, coordinator, task_id, _packet = _prepare_delivery(
        tmp_path, HistoricalReviewGitHub(), authorize=False
    )
    record = coordinator._get(task_id)
    assert record is not None and record.state == "fork_ci_green"
    assert record.review_actor == "reviewer"
    getattr(conn, "close")()


def test_github_merge_pins_the_recorded_head_sha(monkeypatch):
    adapter = GhGitHubAdapter(executable="gh")
    calls = []

    def fake_api(endpoint, *, method="GET", fields=None):
        calls.append((endpoint, method, fields))
        return {"merged": True}

    monkeypatch.setattr(adapter, "_api", fake_api)
    adapter.merge_pr("example/project", 7, "squash", "1" * 40)

    assert calls == [
        (
            "repos/example/project/pulls/7/merge",
            "PUT",
            {"merge_method": "squash", "sha": "1" * 40},
        )
    ]


def test_merge_rejects_a_head_that_moves_after_pre_merge_readback(tmp_path: Path):
    provider = MovingHeadGitHub()
    conn, coordinator, task_id, packet = _prepare_delivery(tmp_path, provider, authorize=False)
    coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet.packet_hash,
        method="squash",
        reason="moving-head regression",
        confirmation=True,
    )

    with pytest.raises(DeliveryConflict, match="head"):
        coordinator.merge(task_id)

    assert provider.merge_head_sha == packet.head_sha
    assert coordinator._get(task_id).state == "merge_authorization_pending"
    conn.close()


def test_packet_only_green_is_rejected_when_live_evidence_adapter_fails(tmp_path: Path):
    conn, coordinator, task_id, packet = _prepare_delivery(
        tmp_path, BrokenLiveEvidenceGitHub(), authorize=False, record_review=False
    )
    # The provider failure must be observed while recording the packet, not
    # hidden behind packet-only fields.
    with pytest.raises(DeliveryBlocked, match="live|checks"):
        coordinator.record_review_and_checks(task_id, packet)
    conn.close()


@pytest.mark.parametrize(
    "env_name",
    ["HERMES_KANBAN_TASK", "HERMES_DELEGATED_CHILD_CONTEXT"],
)
def test_workers_cannot_record_tier_b_evidence_or_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, env_name: str
):
    conn, coordinator, task_id, _packet = _prepare_delivery(
        tmp_path, FakeGitHub(), authorize=False
    )
    monkeypatch.setenv(env_name, "worker-context")

    with pytest.raises(DeliveryBlocked, match="worker|gateway|delegated"):
        coordinator.record_risk_evidence(
            task_id,
            actor="hermes-policy",
            evidence={"security_scan": {"status": "passed"}},
        )
    with pytest.raises(DeliveryBlocked, match="worker|gateway|delegated"):
        coordinator.merge(task_id)
    conn.close()


def test_merge_requires_durable_exact_packet_authorization_and_is_idempotent(tmp_path: Path):
    conn, coordinator, task_id, packet = _prepare_delivery(tmp_path, FakeGitHub(), authorize=False)
    with pytest.raises(DeliveryBlocked, match="authorization"):
        coordinator.merge(task_id)

    authorization = coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet.packet_hash,
        method="squash",
        reason="explicit test authorization",
        confirmation=True,
    )
    assert authorization["method"] == "squash"
    merged = coordinator.merge(task_id)
    assert merged["merged_commit_sha"] == "3" * 40
    provider = coordinator.github
    assert provider.merge_calls == 1
    assert coordinator.merge(task_id) == merged
    assert provider.merge_calls == 1
    conn.close()


def test_transition_rejects_silent_review_head_rewrite():
    with pytest.raises(DeliveryStateError):
        DeliveryCoordinator.validate_transition("fork_ci_green", "committed")


def test_review_packet_rejects_base_sha_movement(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    coordinator = DeliveryCoordinator(conn, git=FakeGit(repo), github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="1" * 40)
    coordinator.commit(task_id, message="test delivery", paths=["changed.py"])
    coordinator.push(task_id)
    coordinator.open_pr(task_id, title="test", body="test")
    stale = ReviewPacket.from_mapping({**_packet().as_dict(), "base_sha": "3" * 40})
    with pytest.raises(DeliveryConflict, match="base"):
        coordinator.record_review_and_checks(task_id, stale)
    conn.close()


def test_validation_rejects_fabricated_tree_identity(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    coordinator = DeliveryCoordinator(conn, git=FakeGit(repo), github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    with pytest.raises(DeliveryConflict, match="tree|HEAD|identity"):
        coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="f" * 40)
    conn.close()


def test_push_timeout_is_resolved_by_exact_remote_readback(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    git = CrashAfterPushGit(repo)
    coordinator = DeliveryCoordinator(conn, git=git, github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="1" * 40)
    coordinator.commit(task_id, message="test delivery", paths=["changed.py"])
    with pytest.raises(TimeoutError):
        coordinator.push(task_id)
    assert coordinator.push(task_id).state == "fork_pushed"
    assert git.push_calls == 1
    conn.close()


def test_commit_refuses_dirty_files_outside_declared_scope(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "base.py").write_text("pass\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "--", "base.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    (repo / "allowed.py").write_text("pass\n", encoding="utf-8")
    (repo / "unrelated.py").write_text("pass\n", encoding="utf-8")
    before = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    with pytest.raises(DeliveryBlocked, match="scope|dirty"):
        SubprocessGitAdapter().commit(repo, "scoped", ["allowed.py"])
    after = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert after == before


class AmbiguousGitHub(FakeGitHub):
    def merge_pr(self, repository: str, number: int, method: str, head_sha: str):
        self.merge_calls += 1
        return {"merged": True, "sha": "3" * 40, "actor": "owner", "method": method}


def test_ambiguous_merge_is_read_back_before_retry(tmp_path: Path):
    provider = AmbiguousGitHub()
    conn, coordinator, task_id, _packet = _prepare_delivery(tmp_path, provider)
    with pytest.raises(Exception, match="ambiguous|read-back"):
        coordinator.merge(task_id)
    assert provider.merge_calls == 1
    provider.pr = {**provider.pr, "state": "merged", "merge_commit_sha": "3" * 40}
    merged = coordinator.merge(task_id)
    assert merged["merged_commit_sha"] == "3" * 40
    assert provider.merge_calls == 1
    conn.close()


def test_secret_shaped_authorization_evidence_is_redacted(tmp_path: Path):
    conn, coordinator, task_id, packet = _prepare_delivery(tmp_path, FakeGitHub(), authorize=False)
    secret = "ghp_" + "A" * 32
    coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet.packet_hash,
        method="squash",
        reason=f"operator note contains {secret}",
        confirmation=True,
    )
    rows = conn.execute("SELECT payload FROM task_events WHERE task_id = ?", (task_id,)).fetchall()
    stored = "\n".join(str(row["payload"] or "") for row in rows)
    assert secret not in stored
    assert "[REDACTED]" in stored
    conn.close()


def test_remote_url_with_embedded_credentials_is_rejected_before_persistence(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    git = FakeGit(repo)
    git.remote_url = "https://ghp_" + "A" * 32 + "@github.com/example/project.git"
    coordinator = DeliveryCoordinator(conn, git=git, github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    with pytest.raises(DeliveryBlocked, match="credential|remote"):
        coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    assert conn.execute("SELECT COUNT(*) FROM kanban_deliveries").fetchone()[0] == 0
    conn.close()


def test_cutover_verification_requires_materialized_activation(tmp_path: Path):
    conn, coordinator, task_id, _packet = _prepare_delivery(tmp_path, FakeGitHub())
    coordinator.merge(task_id)
    coordinator.authorize_cutover(
        task_id,
        actor="owner",
        source="operator_cli",
        runtime_remote="origin",
        runtime_branch="main",
        approved_merge_sha="3" * 40,
        confirmation=True,
    )
    coordinator.prepare_cutover(task_id, output_dir=tmp_path / "rollback")
    evidence = {
        "runtime_after_sha": "3" * 40,
        "main_pid": 123,
        "start_time": "2026-08-25T12:00:00Z",
        "service_interpreter": "/usr/bin/python3",
        "hermes_cli_import": "ok",
        "sqlite_version": "3.45",
        "health": "ok",
        "dispatcher": "ok",
        "cron": "ok",
    }
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(DeliveryStateError, match="materialized|activation"):
        coordinator.verify_cutover(task_id, evidence_path=evidence_path)
    coordinator.record_runtime_materialized(
        task_id,
        before_sha="2" * 40,
        after_sha="3" * 40,
        main_pid=123,
        service_interpreter="/usr/bin/python3",
    )
    verified = coordinator.verify_cutover(task_id, evidence_path=evidence_path)
    assert verified.state == "activation_verified"
    conn.close()


def test_requested_changes_preserve_same_pr_identity_and_return_to_editing(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    coordinator = DeliveryCoordinator(conn, git=FakeGit(repo), github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="1" * 40)
    coordinator.commit(task_id, message="test delivery", paths=["changed.py"])
    coordinator.push(task_id)
    coordinator.open_pr(task_id, title="test delivery", body="test")
    pending = coordinator.request_review(task_id, reviewer="reviewer")
    changed = coordinator.record_changes_requested(task_id, reason="add a regression test")
    assert pending.reviewed_pr_number == changed.reviewed_pr_number == 7
    assert changed.state == "editing"
    assert changed.review_snapshot is None
    assert changed.merge_authorization is None
    conn.close()


def test_upstream_sync_is_fetch_only_and_stops_before_fork_work(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    git = FakeGit(repo)
    coordinator = DeliveryCoordinator(conn, git=git, github=FakeGitHub(), now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    started = coordinator.start(
        task_id,
        project_path=repo,
        repository="example/project",
        branch="feature/t_test",
        workspace_path=tmp_path / "delivery-worktree",
        target_policy="fork_with_upstream_sync",
    )
    assert started.state == "upstream_sync_pending"
    synced = coordinator.sync_upstream(task_id, source="upstream/main")
    assert synced.state == "upstream_sync_review_pending"
    assert any(call[0] == "fetch" and call[1] == str(repo) and call[2] == "upstream" for call in git.calls)
    assert coordinator.resume(task_id).state == "upstream_sync_review_pending"
    conn.close()


def test_cleanup_refuses_removing_worktree_while_task_claim_is_live(tmp_path: Path):
    conn, coordinator, task_id, _ = _prepare_delivery(tmp_path, FakeGitHub())
    coordinator.merge(task_id)
    conn.execute("UPDATE tasks SET claim_lock = ?, claim_expires = ?", ("worker-live", 2000))
    conn.commit()
    with pytest.raises(DeliveryBlocked, match="claim"):
        coordinator.cleanup(task_id, remove_worktree=True)
    conn.close()


def test_merge_authorization_actor_must_match_authenticated_provider_identity(tmp_path: Path):
    conn, coordinator, task_id, packet = _prepare_delivery(tmp_path, FakeGitHub(), authorize=False)
    with pytest.raises(DeliveryBlocked, match="authenticated|actor"):
        coordinator.authorize_merge(
            task_id,
            actor="intruder",
            source="operator_cli",
            packet_hash=packet.packet_hash,
            method="squash",
            reason="not an owner",
            confirmation=True,
        )
    conn.close()


def test_pr_creation_recovers_by_reading_back_existing_pr_after_timeout(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    github = CrashAfterCreateGitHub()
    coordinator = DeliveryCoordinator(conn, git=FakeGit(repo), github=github, now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(task_id, project_path=repo, repository="example/project", branch="feature/t_test")
    coordinator.resume(task_id)
    coordinator.record_validation(task_id, commands=["scripts/run_tests.sh"], passed=True, tree_sha="1" * 40)
    coordinator.commit(task_id, message="test delivery", paths=["changed.py"])
    coordinator.push(task_id)
    with pytest.raises(TimeoutError):
        coordinator.open_pr(task_id, title="test delivery", body="test")
    recovered = coordinator.open_pr(task_id, title="test delivery", body="test")
    assert recovered.state == "fork_pr_open"
    assert recovered.reviewed_pr_number == 7
    assert github.create_calls == 1
    conn.close()


def test_upstream_sync_uses_fork_local_review_and_merge_before_admission(tmp_path: Path):
    conn, repo = _make_task(tmp_path)
    github = SyncGitHub()
    git = FakeGit(repo)
    coordinator = DeliveryCoordinator(conn, git=git, github=github, now=lambda: 1000, risk_policy={"mode": "human", "auto_merge": False})
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    coordinator.start(
        task_id,
        project_path=repo,
        repository="example/project",
        branch="feature/t_test",
        target_policy="fork_with_upstream_sync",
    )
    coordinator.sync_upstream(task_id)
    packet = _sync_packet()
    assert coordinator.record_upstream_sync_review_and_checks(task_id, packet).state == "upstream_sync_ci_green"
    coordinator.authorize_upstream_sync(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet.packet_hash,
        method="squash",
        confirmation=True,
    )
    admitted = coordinator.merge_upstream_sync(task_id)
    assert admitted.state == "workspace_admitted"
    assert not any(call[0] == "push" and call[2] == "upstream" for call in git.calls)
    conn.close()
