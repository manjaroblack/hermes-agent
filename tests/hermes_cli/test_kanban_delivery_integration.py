"""Real-local integration coverage for the guarded Kanban delivery lifecycle.

The delivery coordinator keeps GitHub behind an injected adapter, but these tests
exercise the local repository/worktree, durable Kanban DB, and HERMES_HOME path
for real.  The fake provider is deliberately deterministic and records every
external-side-effect call; it never talks to GitHub.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
from typing import Any, Iterator

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.kanban_delivery import (
    DeliveryBlocked,
    DeliveryConflict,
    DeliveryCoordinator,
    DeliveryStateError,
    ReviewPacket,
    SubprocessGitAdapter,
    classify_delivery_risk,
)


PROJECT_REPOSITORY = "example/project"
PROJECT_REMOTE = "https://github.com/example/project.git"
UPSTREAM_REPOSITORY = "NousResearch/hermes-agent"
UPSTREAM_REMOTE = "https://github.com/NousResearch/hermes-agent.git"
BRANCH = "feature/delivery-integration"
MERGED_SHA = "3" * 40


class RecordingGit(SubprocessGitAdapter):
    """Real Git adapter with counters for idempotency assertions."""

    def __init__(self) -> None:
        super().__init__(timeout=15)
        self.calls: Counter[str] = Counter()

    def ensure_worktree(self, repository: Path, target: Path, branch: str, base_ref: str):
        self.calls["ensure_worktree"] += 1
        return super().ensure_worktree(repository, target, branch, base_ref)

    def remote_url_for(self, path: Path, remote: str) -> str:
        # The local transport is rewritten to a bare repository in the fixture,
        # while this seam preserves the canonical provider identity that the
        # coordinator must record and validate.
        if remote == "origin":
            return PROJECT_REMOTE
        if remote == "upstream":
            return UPSTREAM_REMOTE
        return super().remote_url_for(path, remote)

    def commit(self, path: Path, message: str, paths=None):
        self.calls["commit"] += 1
        return super().commit(path, message, paths)

    def push(self, path: Path, remote: str, branch: str, head_sha: str):
        self.calls["push"] += 1
        return super().push(path, remote, branch, head_sha)

    def fetch(self, path: Path, remote: str, ref: str):
        self.calls["fetch"] += 1
        return super().fetch(path, remote, ref)

    def remove_worktree(self, repository: Path, target: Path) -> None:
        self.calls["remove_worktree"] += 1
        super().remove_worktree(repository, target)


class DeterministicGitHub:
    """Provider seam: local state only, with explicit effect call counters."""

    def __init__(self) -> None:
        self.pr: dict[str, Any] | None = None
        self.expected_head_sha = ""
        self.expected_base_sha = ""
        self.create_calls = 0
        self.review_calls = 0
        self.merge_calls = 0
        self.delete_calls = 0

    def current_user(self) -> str:
        return "owner"

    def get_required_checks(self, repository: str, branch: str, head_sha: str):
        return {
            "head_sha": head_sha,
            "runs": [{
                "id": 1,
                "name": "delivery-tests",
                "status": "completed",
                "conclusion": "success",
                "head_sha": head_sha,
            }],
            "checked_at": 1_100,
        }

    def get_reviews(self, repository: str, number: int):
        assert self.pr is not None
        return {
            "reviews": [{
                "id": 1,
                "state": "approved",
                "user": {"login": "reviewer"},
                "commit_id": self.pr["head"]["sha"],
                "submitted_at": 1_100,
                "model_family": "reviewer-family",
            }]
        }

    def get_branch_protection(self, repository: str, branch: str):
        return {
            "enabled": True,
            "branch": branch,
            "required_status_checks": {"contexts": ["delivery-tests"]},
        }

    def find_pr(self, repository: str, head: str, base: str):
        if self.pr is None:
            return None
        if self.pr["head"]["ref"] == head and self.pr["base"]["ref"] == base:
            return deepcopy(self.pr)
        return None

    def create_pr(self, repository: str, head: str, base: str, title: str, body: str):
        self.create_calls += 1
        self.pr = {
            "number": 42,
            "html_url": f"https://github.com/{repository}/pull/42",
            "state": "open",
            "draft": False,
            "head": {"ref": head, "sha": self.expected_head_sha},
            "base": {"ref": base, "sha": self.expected_base_sha},
            "title": title,
            "body": body,
        }
        return {"number": 42, "html_url": self.pr["html_url"]}

    def get_pr(self, repository: str, number: int):
        if self.pr is None or int(self.pr["number"]) != int(number):
            raise AssertionError("provider seam was asked for an unknown PR")
        return deepcopy(self.pr)

    def request_review(self, repository: str, number: int, reviewer: str):
        self.review_calls += 1
        return {"number": number, "reviewer": reviewer}

    def merge_pr(self, repository: str, number: int, method: str, head_sha: str):
        self.merge_calls += 1
        if self.pr is None:
            return {"merged": False}
        if head_sha != self.pr["head"]["sha"]:
            return {"merged": False, "message": "head SHA mismatch"}
        self.pr["state"] = "merged"
        self.pr["merge_commit_sha"] = MERGED_SHA
        return {"merged": True, "sha": MERGED_SHA, "actor": "owner", "method": method}

    def delete_branch(self, repository: str, branch: str):
        self.delete_calls += 1
        return {"deleted": True, "repository": repository, "branch": branch}


class PermissionDeniedGitHub(DeterministicGitHub):
    def current_user(self) -> str:
        raise RuntimeError("provider permission denied")


class BrokenLiveEvidenceGitHub(DeterministicGitHub):
    def get_required_checks(self, repository: str, branch: str, head_sha: str):
        raise RuntimeError("live checks unavailable")


class LiveGateFailureGitHub(DeterministicGitHub):
    def __init__(self, gate: str):
        super().__init__()
        self.gate = gate

    def get_required_checks(self, repository: str, branch: str, head_sha: str):
        if self.gate == "checks":
            return {
                "head_sha": head_sha,
                "runs": [{"name": "delivery-tests", "status": "completed", "conclusion": "failure", "head_sha": head_sha}],
                "checked_at": 1_100,
            }
        return super().get_required_checks(repository, branch, head_sha)

    def get_reviews(self, repository: str, number: int):
        if self.gate == "review":
            assert self.pr is not None
            return {
                "reviews": [{
                    "id": 1,
                    "state": "changes_requested",
                    "user": {"login": "reviewer"},
                    "commit_id": self.pr["head"]["sha"],
                    "submitted_at": 1_100,
                    "model_family": "reviewer-family",
                }]
            }
        return super().get_reviews(repository, number)

    def get_branch_protection(self, repository: str, branch: str):
        if self.gate == "branch_protection":
            return {"enabled": False, "branch": branch}
        return super().get_branch_protection(repository, branch)


class ClosedMergedGitHub(DeterministicGitHub):
    """GitHub REST-style read-back: merged PRs are returned as closed."""

    def merge_pr(self, repository: str, number: int, method: str, head_sha: str):
        result = super().merge_pr(repository, number, method, head_sha)
        assert self.pr is not None
        self.pr["state"] = "closed"
        self.pr["merged"] = True
        self.pr["merged_at"] = "2026-08-25T12:00:00Z"
        return result


def _git(cwd: Path | None, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git command failed ({result.returncode}): {args}\n{result.stderr}"
        )
    return result.stdout.strip()


def _create_local_repositories(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    """Create a fork, an upstream mirror, and a canonical-URL working repo."""
    origin = tmp_path / "origin.git"
    upstream = tmp_path / "upstream.git"
    repo = tmp_path / "project"
    _git(None, "init", "--bare", "-q", str(origin))
    _git(None, "init", "--bare", "-q", str(upstream))
    _git(None, "init", "-q", "-b", "main", str(repo))
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Hermes Integration Test")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "--", "README.md")
    _git(repo, "commit", "-qm", "base")

    _git(repo, "remote", "add", "origin", PROJECT_REMOTE)
    _git(repo, "config", f"url.{origin.as_uri()}.insteadOf", PROJECT_REMOTE)
    _git(repo, "push", "-q", "origin", "main")

    _git(repo, "remote", "add", "upstream", UPSTREAM_REMOTE)
    _git(repo, "config", f"url.{upstream.as_uri()}.insteadOf", UPSTREAM_REMOTE)
    _git(repo, "push", "-q", "upstream", "main")
    base_sha = _git(repo, "rev-parse", "HEAD")
    return repo, origin, upstream, base_sha


def _make_upstream_only_commit(tmp_path: Path, repo: Path, upstream: Path) -> str:
    source = tmp_path / "upstream-source"
    _git(None, "clone", "-q", str(repo), str(source))
    _git(source, "config", "user.email", "upstream@example.invalid")
    _git(source, "config", "user.name", "Upstream Fixture")
    _git(source, "remote", "remove", "origin")
    _git(source, "remote", "add", "upstream", str(upstream))
    (source / "UPSTREAM.md").write_text("upstream\n", encoding="utf-8")
    _git(source, "add", "--", "UPSTREAM.md")
    _git(source, "commit", "-qm", "upstream change")
    _git(source, "push", "-q", "upstream", "HEAD:refs/heads/main")
    return _git(source, "rev-parse", "HEAD")


@pytest.fixture
def isolated_delivery_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Use a fresh real HERMES_HOME and no inherited Kanban path pins."""
    home = tmp_path / "hermes-home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    for name in (
        "HERMES_KANBAN_DB",
        "HERMES_KANBAN_BOARD",
        "HERMES_KANBAN_HOME",
        "HERMES_KANBAN_WORKSPACES_ROOT",
        "HERMES_KANBAN_TASK",
        "HERMES_DELEGATED_CHILD_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    kb._INITIALIZED_PATHS.clear()
    assert kb.kanban_db_path().resolve().is_relative_to(home.resolve())
    yield home
    kb._INITIALIZED_PATHS.clear()


def _new_context(
    tmp_path: Path,
    *,
    target_policy: str = "fork_only",
    workspace_name: str | None = None,
    github: DeterministicGitHub | None = None,
    now=None,
    risk_policy: dict[str, Any] | None = None,
    change_paths: tuple[str, ...] = ("change.py",),
) -> dict[str, Any]:
    repo, origin, upstream, base_sha = _create_local_repositories(tmp_path)
    conn = kb.connect()
    task_id = kb.create_task(
        conn,
        title="real delivery integration",
        assignee="hermes-coding",
        workspace_kind="dir",
        workspace_path=str(repo),
        initial_status="running",
    )
    workspace = tmp_path / "delivery-worktrees" / (workspace_name or task_id)
    git = RecordingGit()
    provider = github or DeterministicGitHub()
    clock = now or (lambda: 1_000)
    coordinator = DeliveryCoordinator(
        conn,
        git=git,
        github=provider,
        now=clock,
        risk_policy=risk_policy if risk_policy is not None else {"mode": "human", "auto_merge": False},
    )
    started = coordinator.start(
        task_id,
        project_path=repo,
        repository=PROJECT_REPOSITORY,
        branch=BRANCH,
        workspace_path=workspace,
        target_policy=target_policy,
    )
    return {
        "conn": conn,
        "task_id": task_id,
        "repo": repo,
        "origin": origin,
        "upstream": upstream,
        "base_sha": base_sha,
        "workspace": workspace,
        "git": git,
        "github": provider,
        "coordinator": coordinator,
        "started": started,
        "change_paths": change_paths,
        "risk_policy": risk_policy,
    }


def _advance_to_pr(context: dict[str, Any]) -> dict[str, Any]:
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    workspace: Path = context["workspace"]
    github: DeterministicGitHub = context["github"]
    editing = coordinator.resume(task_id)
    assert editing.state == "editing"
    for index, relative_path in enumerate(context["change_paths"]):
        changed = workspace / relative_path
        changed.parent.mkdir(parents=True, exist_ok=True)
        changed.write_text(f"VALUE = {index + 1}\n", encoding="utf-8")
    tree_sha = _git(workspace, "rev-parse", "HEAD")
    validated = coordinator.record_validation(
        task_id,
        commands=["scripts/run_tests.sh tests/hermes_cli/test_kanban_delivery.py -q"],
        passed=True,
        tree_sha=tree_sha,
    )
    assert validated.state == "validated"
    committed = coordinator.commit(
        task_id,
        message="add delivery integration change",
        paths=list(context["change_paths"]),
    )
    assert committed.commit_sha
    pushed = coordinator.push(task_id)
    github.expected_head_sha = pushed.commit_sha or ""
    github.expected_base_sha = pushed.base_sha
    opened = coordinator.open_pr(
        task_id,
        title="delivery integration",
        body="deterministic local provider fixture",
    )
    assert opened.state == "fork_pr_open"
    assert opened.reviewed_pr_number and opened.reviewed_pr_number > 0, opened
    assert coordinator.open_pr(task_id, title="ignored", body="ignored") == opened
    assert github.create_calls == 1
    return {**context, "opened": opened, "committed": committed}


def _packet_for(context: dict[str, Any]) -> dict[str, Any]:
    opened = context["opened"]
    github: DeterministicGitHub = context["github"]
    pr = github.pr
    assert pr is not None
    return {
        "provider": "github",
        "repository": PROJECT_REPOSITORY,
        "remote": "origin",
        "pr_url": pr["html_url"],
        "pr_number": pr["number"],
        "branch": opened.branch,
        "head_sha": opened.commit_sha,
        "base_branch": opened.base_branch,
        "base_sha": opened.base_sha,
        "review": {
            "decision": "approved",
            "actor": "reviewer",
            "model_family": "reviewer-family",
            "reviewed_at": 1_100,
        },
        "checks": {
            "policy": "required",
            "exact_head_sha": opened.commit_sha,
            "all_required": True,
            "branch_protected": True,
            "runs": [
                {
                    "id": 1,
                    "name": "delivery-tests",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
            "checked_at": 1_100,
        },
    }


def _advance_to_review(context: dict[str, Any]) -> dict[str, Any]:
    context = _advance_to_pr(context)
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    before_request = coordinator._get(task_id)
    assert before_request is not None
    assert before_request.state == "fork_pr_open"
    assert before_request.reviewed_pr_number and before_request.reviewed_pr_number > 0, before_request
    pending = coordinator.request_review(task_id, reviewer="reviewer")
    assert pending.state == "fork_review_pending"
    return {**context, "pending": pending, "packet": _packet_for(context)}


def _advance_to_ci_green(context: dict[str, Any]) -> dict[str, Any]:
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    green = coordinator.record_review_and_checks(task_id, context["packet"])
    assert green.state == "fork_ci_green"
    return {**context, "green": green}


def test_real_git_happy_path_and_each_provider_effect_is_idempotent(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_review(_new_context(tmp_path))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    git: RecordingGit = context["git"]
    github: DeterministicGitHub = context["github"]

    # The real worktree and local bare remote are exercised before any provider
    # seam is invoked.
    assert context["workspace"].is_dir()
    assert not context["workspace"].resolve().is_relative_to(context["repo"].resolve())
    assert _git(context["workspace"], "rev-parse", "HEAD") == context["committed"].commit_sha
    assert git.calls["push"] == 1

    # Replaying the durable PR/review effects must not create or request twice.
    pending_again = coordinator.request_review(task_id, reviewer="reviewer")
    assert pending_again.state == "fork_review_pending"
    assert github.create_calls == 1
    assert github.review_calls == 1

    green = coordinator.record_review_and_checks(task_id, context["packet"])
    assert green.state == "fork_ci_green"
    assert coordinator.record_review_and_checks(task_id, context["packet"]).state == "fork_ci_green"

    # Green CI and an independent reviewer are still not merge authorization.
    with pytest.raises(DeliveryBlocked, match="authorization"):
        coordinator.merge(task_id)
    assert github.merge_calls == 0

    auth = coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=ReviewPacket.from_mapping(context["packet"]).packet_hash,
        method="squash",
        reason="explicit integration-test authorization",
        confirmation=True,
    )
    assert auth["confirmed"] is True
    merged = coordinator.merge(task_id)
    assert merged["merged_commit_sha"] == MERGED_SHA
    assert coordinator.merge(task_id) == merged
    assert github.merge_calls == 1

    remote_head = _git(None, "--git-dir", str(context["origin"]), "rev-parse", "refs/heads/" + BRANCH)
    assert remote_head == context["committed"].commit_sha
    effects = coordinator.status(task_id)["effects"]
    assert effects
    assert all(effect["status"] == "applied" for effect in effects)
    context["conn"].close()


def test_commit_replay_and_real_worktree_cleanup_are_safe(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _new_context(tmp_path)
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    workspace = context["workspace"]
    git: RecordingGit = context["git"]
    github: DeterministicGitHub = context["github"]

    coordinator.resume(task_id)
    (workspace / "change.py").write_text("VALUE = 2\n", encoding="utf-8")
    tree_sha = _git(workspace, "rev-parse", "HEAD")
    coordinator.record_validation(task_id, commands=["true"], passed=True, tree_sha=tree_sha)
    committed = coordinator.commit(task_id, message="commit once", paths=["change.py"])
    assert coordinator.commit(task_id, message="ignored", paths=["change.py"]) == committed
    assert git.calls["commit"] == 1
    coordinator.push(task_id)
    github.expected_head_sha = committed.commit_sha or ""
    github.expected_base_sha = committed.base_sha
    coordinator.open_pr(task_id, title="cleanup", body="cleanup")
    coordinator.request_review(task_id, reviewer="reviewer")
    packet = _packet_for({**context, "opened": coordinator._get(task_id)})
    coordinator.record_review_and_checks(task_id, packet)
    coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=ReviewPacket.from_mapping(packet).packet_hash,
        method="squash",
        reason="cleanup authorization",
        confirmation=True,
    )
    coordinator.merge(task_id)

    completed = coordinator.cleanup(
        task_id, delete_remote_branch=True, remove_worktree=True
    )
    assert completed.state == "completed"
    assert not workspace.exists()
    assert git.calls["remove_worktree"] == 1
    assert github.delete_calls == 1
    assert coordinator.cleanup(task_id, delete_remote_branch=True, remove_worktree=True) == completed
    assert git.calls["remove_worktree"] == 1
    assert github.delete_calls == 1
    context["conn"].close()


def test_green_ci_reviewer_go_and_chat_silence_cannot_authorize_merge(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(_advance_to_review(_new_context(tmp_path)))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    packet_hash = ReviewPacket.from_mapping(context["packet"]).packet_hash

    with pytest.raises(DeliveryBlocked, match="source"):
        coordinator.authorize_merge(
            task_id,
            actor="owner",
            source="chat_message",
            packet_hash=packet_hash,
            method="squash",
            reason="a chat message is not durable authorization",
            confirmation=True,
        )
    with pytest.raises(DeliveryBlocked, match="confirmation"):
        coordinator.authorize_merge(
            task_id,
            actor="owner",
            source="operator_cli",
            packet_hash=packet_hash,
            method="squash",
            reason="green CI only",
            confirmation=False,
        )
    with pytest.raises(DeliveryBlocked, match="authorization"):
        coordinator.merge(task_id)
    assert coordinator._get(task_id).state == "fork_ci_green"
    assert context["github"].merge_calls == 0
    context["conn"].close()


@pytest.mark.parametrize("mutation", ["closed", "draft", "head", "branch", "base"])
def test_live_pr_identity_and_state_gates_fail_closed_then_allow_retry(
    isolated_delivery_home: Path, tmp_path: Path, mutation: str
):
    context = _advance_to_review(_new_context(tmp_path))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    github: DeterministicGitHub = context["github"]
    assert github.pr is not None
    if mutation == "closed":
        github.pr["state"] = "closed"
    elif mutation == "draft":
        github.pr["draft"] = True
    elif mutation == "head":
        github.pr["head"]["sha"] = "f" * 40
    elif mutation == "branch":
        github.pr["head"]["ref"] = "foreign-branch"
    else:
        github.pr["base"]["ref"] = "release"

    with pytest.raises((DeliveryBlocked, DeliveryConflict)):
        coordinator.record_review_and_checks(task_id, context["packet"])
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "fork_review_pending"

    # The failure is recoverable only after the provider read-back is corrected
    # and the exact same immutable packet is still valid.
    github.pr = {
        **github.pr,
        "state": "open",
        "draft": False,
        "head": {"ref": context["opened"].branch, "sha": context["opened"].commit_sha},
        "base": {"ref": context["opened"].base_branch, "sha": context["opened"].base_sha},
    }
    assert coordinator.record_review_and_checks(task_id, context["packet"]).state == "fork_ci_green"
    context["conn"].close()


def test_ci_retry_rejects_non_green_packet_without_consuming_review_state(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_review(_new_context(tmp_path))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    bad_packet = deepcopy(context["packet"])
    bad_packet["checks"]["runs"][0]["conclusion"] = "failure"
    with pytest.raises(ValueError, match="completed with success"):
        coordinator.record_review_and_checks(task_id, bad_packet)
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "fork_review_pending"
    assert coordinator.record_review_and_checks(task_id, context["packet"]).state == "fork_ci_green"
    context["conn"].close()


def test_wrong_repository_base_and_unexpected_worktree_never_cross_persistence_gate(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _new_context(tmp_path)
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    repo = context["repo"]
    with pytest.raises(DeliveryConflict, match="remote"):
        coordinator.start(
            task_id,
            project_path=repo,
            repository="other/project",
            branch=BRANCH,
            workspace_path=context["workspace"],
        )
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "workspace_admitted"
    with pytest.raises(DeliveryBlocked):
        coordinator.start(
            task_id,
            project_path=repo,
            repository=PROJECT_REPOSITORY,
            base_branch="develop",
            branch=BRANCH,
            workspace_path=context["workspace"],
        )
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "workspace_admitted"
    context["conn"].close()

    dirty_context = _new_context(tmp_path / "dirty")
    dirty_workspace = dirty_context["workspace"]
    dirty_context["started"]
    dirty_workspace.mkdir(parents=True)
    (dirty_workspace / "unexpected.txt").write_text("do not reuse\n", encoding="utf-8")
    with pytest.raises(DeliveryBlocked, match="non-empty|unexpected"):
        dirty_context["coordinator"].resume(dirty_context["task_id"])
    record = dirty_context["coordinator"]._get(dirty_context["task_id"])
    assert record is not None
    assert record.state == "workspace_admitted"
    assert BRANCH not in _git(dirty_context["repo"], "worktree", "list", "--porcelain")
    dirty_context["conn"].close()


def test_permission_failure_and_expired_authorization_are_fail_closed(
    isolated_delivery_home: Path, tmp_path: Path
):
    denied = _advance_to_ci_green(
        _advance_to_review(_new_context(tmp_path, github=PermissionDeniedGitHub()))
    )
    with pytest.raises(DeliveryBlocked, match="authenticated|permission"):
        denied["coordinator"].authorize_merge(
            denied["task_id"],
            actor="owner",
            source="operator_cli",
            packet_hash=ReviewPacket.from_mapping(denied["packet"]).packet_hash,
            method="squash",
            reason="provider access is unavailable",
            confirmation=True,
        )
    record = denied["coordinator"]._get(denied["task_id"])
    assert record is not None
    assert record.state == "fork_ci_green"
    denied["conn"].close()

    clock = [1_000]
    expiring = _advance_to_ci_green(
        _advance_to_review(_new_context(tmp_path / "expiry", now=lambda: clock[0]))
    )
    packet_hash = ReviewPacket.from_mapping(expiring["packet"]).packet_hash
    expiring["coordinator"].authorize_merge(
        expiring["task_id"],
        actor="owner",
        source="operator_cli",
        packet_hash=packet_hash,
        method="squash",
        reason="short-lived authorization",
        confirmation=True,
        expires_at=1_001,
    )
    clock[0] = 1_001
    with pytest.raises(DeliveryBlocked, match="expired"):
        expiring["coordinator"].merge(expiring["task_id"])
    assert expiring["github"].merge_calls == 0
    expiring["conn"].close()


def test_interrupted_worktree_resume_and_abort_do_not_duplicate_refs(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _new_context(tmp_path)
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    git: RecordingGit = context["git"]
    first = coordinator.resume(task_id)
    assert first.state == "editing"
    second = coordinator.resume(task_id)
    assert second.state == "editing"
    assert git.calls["ensure_worktree"] == 1
    aborted = coordinator.abort(task_id, reason="operator stopped before PR creation")
    assert aborted.state == "aborted"
    assert coordinator.abort(task_id, reason="replayed abort") == aborted
    assert git.calls["ensure_worktree"] == 1
    assert context["github"].create_calls == 0
    assert BRANCH in _git(context["repo"], "worktree", "list", "--porcelain")
    context["conn"].close()


def test_live_claim_blocks_worktree_cleanup(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(_advance_to_review(_new_context(tmp_path)))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    packet_hash = ReviewPacket.from_mapping(context["packet"]).packet_hash
    coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet_hash,
        method="squash",
        reason="merge before cleanup",
        confirmation=True,
    )
    coordinator.merge(task_id)
    context["conn"].execute(
        "UPDATE tasks SET claim_lock = ?, claim_expires = ? WHERE id = ?",
        ("concurrent-worker", 2_000, task_id),
    )
    context["conn"].commit()
    with pytest.raises(DeliveryBlocked, match="claim"):
        coordinator.cleanup(task_id, remove_worktree=True)
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "fork_merge_verified"
    context["conn"].close()


def test_fork_remote_and_upstream_sync_use_distinct_authorities_and_fetch_only(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _new_context(tmp_path, target_policy="fork_with_upstream_sync")
    upstream_sha = _make_upstream_only_commit(
        tmp_path, context["repo"], context["upstream"]
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    synced = coordinator.sync_upstream(task_id, source="upstream/main")
    assert synced.state == "upstream_sync_review_pending"
    assert synced.upstream_source_sha == upstream_sha
    assert context["git"].calls["fetch"] == 1
    assert _git(None, "--git-dir", str(context["origin"]), "show-ref", "--heads")
    assert context["git"].calls["push"] == 0
    with pytest.raises(DeliveryBlocked, match="upstream"):
        context["git"].push(
            context["repo"], "upstream", BRANCH, upstream_sha
        )
    context["conn"].close()


def test_abort_is_durable_and_rollback_does_not_create_pr_or_merge_side_effects(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _new_context(tmp_path)
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    coordinator.abort(task_id, reason="rollback requested")
    status = coordinator.status(task_id)
    assert status["delivery"]["state"] == "aborted"
    assert status["effects"] == []
    assert context["github"].create_calls == 0
    assert context["github"].merge_calls == 0
    assert coordinator.abort(task_id, reason="same rollback replay").state == "aborted"
    context["conn"].close()


def test_cutover_evidence_remains_blocked_until_external_materialization(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(_advance_to_review(_new_context(tmp_path)))
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    packet_hash = ReviewPacket.from_mapping(context["packet"]).packet_hash
    coordinator.authorize_merge(
        task_id,
        actor="owner",
        source="operator_cli",
        packet_hash=packet_hash,
        method="squash",
        reason="prepare external cutover",
        confirmation=True,
    )
    coordinator.merge(task_id)
    coordinator.authorize_cutover(
        task_id,
        actor="owner",
        source="operator_cli",
        runtime_remote="origin",
        runtime_branch="main",
        approved_merge_sha=MERGED_SHA,
        confirmation=True,
    )
    coordinator.prepare_cutover(task_id, output_dir=tmp_path / "rollback-pack")
    evidence_path = tmp_path / "live-evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "runtime_after_sha": MERGED_SHA,
                "main_pid": 100,
                "start_time": "2026-08-25T00:00:00Z",
                "service_interpreter": "/usr/bin/python3",
                "hermes_cli_import": "ok",
                "sqlite_version": "3.45",
                "health": "ok",
                "dispatcher": "ok",
                "cron": "ok",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(DeliveryStateError, match="materialized|activation"):
        coordinator.verify_cutover(task_id, evidence_path=evidence_path)
    coordinator.record_runtime_materialized(
        task_id,
        before_sha=context["base_sha"],
        after_sha=MERGED_SHA,
        main_pid=100,
        service_interpreter="/usr/bin/python3",
    )
    assert coordinator.verify_cutover(task_id, evidence_path=evidence_path).state == "activation_verified"
    context["conn"].close()


@pytest.mark.parametrize("source", ["silence", "reviewer_go", "chat_message"])
def test_non_authorization_signals_never_create_merge_effect(
    isolated_delivery_home: Path, tmp_path: Path, source: str
):
    context = _advance_to_ci_green(_advance_to_review(_new_context(tmp_path)))
    coordinator: DeliveryCoordinator = context["coordinator"]
    with pytest.raises(DeliveryBlocked):
        coordinator.authorize_merge(
            context["task_id"],
            actor="owner",
            source=source,
            packet_hash=ReviewPacket.from_mapping(context["packet"]).packet_hash,
            method="squash",
            reason="not an approved durable boundary",
            confirmation=True,
        )
    with pytest.raises(DeliveryBlocked):
        coordinator.merge(context["task_id"])
    assert context["github"].merge_calls == 0
    context["conn"].close()


def _tiered_policy(**overrides: Any) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "policy_id": "integration-tiered-v1",
        "mode": "tiered",
        "auto_merge": True,
        "tier_a_allow_paths": ["*.py", "tests/**", "docs/**"],
        "tier_b_paths": ["pyproject.toml", "*.lock"],
        "protected_paths": ["gateway/**", ".env*", "**/*.pem", "**/*.key"],
        "branch_protection_required": True,
        "require_independent_model_family": True,
        "required_tier_b_evidence": ["security_scan", "staged_health", "rollback_artifact"],
    }
    policy.update(overrides)
    return policy


def test_tier_a_allowlisted_change_auto_merges_without_human_authorization(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(
        _advance_to_review(_new_context(tmp_path, risk_policy=_tiered_policy()))
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    merged = coordinator.merge(task_id)
    assert merged["merged_commit_sha"] == MERGED_SHA
    assert merged["merge_authorization"]["mode"] == "automated"
    assert merged["merge_authorization"]["tier"] == "A"
    assert merged["merge_authorization"]["policy_id"] == "integration-tiered-v1"
    assert merged["merge_authorization"]["classifier_inputs"]["changed_paths"] == ["change.py"]
    assert merged["state"] == "completed"
    assert context["github"].delete_calls == 1
    assert context["github"].merge_calls == 1
    context["conn"].close()


def test_tier_b_requires_extra_automated_evidence_and_records_rollback(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path,
                risk_policy=_tiered_policy(),
                change_paths=("pyproject.toml",),
            )
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    with pytest.raises(DeliveryBlocked, match="Tier B|evidence|rollback"):
        coordinator.merge(task_id)
    assert context["github"].merge_calls == 0
    coordinator.record_risk_evidence(
        task_id,
        actor="hermes-policy",
        evidence={
            "security_scan": {"status": "passed", "scan_id": "scan-1"},
            "staged_health": {"status": "passed", "health_id": "canary-1"},
            "rollback_artifact": {
                "kind": "git-parent",
                "source_sha": context["committed"].commit_parent_sha,
            },
        },
    )
    merged = coordinator.merge(task_id)
    assert merged["merge_authorization"]["tier"] == "B"
    assert merged["merge_authorization"]["automated_evidence"]["rollback_artifact"]["kind"] == "git-parent"
    assert merged["state"] == "completed"
    assert context["github"].delete_calls == 1
    context["conn"].close()


@pytest.mark.parametrize("change_path", ["gateway/run.py", ".env.production"])
def test_tier_c_protected_paths_require_human_and_persist_escalation_inputs(
    isolated_delivery_home: Path, tmp_path: Path, change_path: str
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path,
                risk_policy=_tiered_policy(
                    tier_a_allow_paths=["**/*"], tier_b_paths=[]
                ),
                change_paths=(change_path,),
            )
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    with pytest.raises(DeliveryBlocked, match="human|Tier C|risk"):
        coordinator.merge(task_id)
    record = coordinator._get(task_id)
    assert record is not None
    assert record.state == "fork_ci_green"
    assert record.last_error is not None
    assert record.last_error["risk_decision"]["tier"] == "C"
    assert change_path in record.last_error["risk_decision"]["classifier_inputs"]["changed_paths"]
    context["conn"].close()


def test_unknown_scope_fails_closed_even_when_allowlist_is_broad(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path,
                risk_policy=_tiered_policy(
                    tier_a_allow_paths=["*.py"], protected_paths=[]
                ),
                change_paths=("new-extension.weird",),
            )
        )
    )
    with pytest.raises(DeliveryBlocked, match="unknown|human|risk"):
        context["coordinator"].merge(context["task_id"])
    assert context["github"].merge_calls == 0
    context["conn"].close()


def test_protected_path_wins_over_an_overbroad_allowlist(
    isolated_delivery_home: Path, tmp_path: Path
):
    policy = _tiered_policy(
        tier_a_allow_paths=["**/*", "gateway/**"], protected_paths=["gateway/**"]
    )
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path, risk_policy=policy, change_paths=("gateway/run.py",)
            )
        )
    )
    with pytest.raises(DeliveryBlocked, match="human|Tier C|risk"):
        context["coordinator"].merge(context["task_id"])
    assert context["github"].merge_calls == 0
    context["conn"].close()


def test_tier_a_auto_merge_replay_is_idempotent(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(
        _advance_to_review(_new_context(tmp_path, risk_policy=_tiered_policy()))
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]
    first = coordinator.merge(task_id)
    second = coordinator.merge(task_id)
    assert second == first
    assert context["github"].merge_calls == 1
    context["conn"].close()


def test_tier_a_rejects_a_review_by_the_implementer(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path,
                risk_policy=_tiered_policy(implementer_actor="reviewer"),
            )
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    with pytest.raises(DeliveryBlocked, match="independent_reviewer|independent approval|evidence"):
        coordinator.merge(context["task_id"])
    record = coordinator._get(context["task_id"])
    assert record is not None and record.state == "fork_ci_green"
    assert record.last_error is None
    assert context["github"].merge_calls == 0
    context["conn"].close()


def test_classifier_rejects_path_traversal_as_tier_c():
    decision = classify_delivery_risk(
        ["../gateway/run.py"],
        target_policy="fork_only",
        policy=_tiered_policy(),
    )
    assert decision.tier == "C"
    assert decision.classifier_inputs["invalid_paths"] == ["../gateway/run.py"]


@pytest.mark.parametrize("path", [
    "hermes_cli/auth.py",
    "agent/secret_scope.py",
    "run_agent.py",
    "tools/kanban_tools.py",
    "cli.py",
    "secret.pem",
    "server.key",
])
def test_default_policy_protects_high_risk_paths(path: str):
    decision = classify_delivery_risk([path], target_policy="fork_only")
    assert decision.tier == "C"
    assert decision.classifier_inputs.get("protected_matches") == [path]


def test_packet_only_green_is_rejected_when_live_evidence_provider_fails(
    isolated_delivery_home: Path, tmp_path: Path
):
    context = _advance_to_review(
        _new_context(tmp_path, github=BrokenLiveEvidenceGitHub())
    )
    with pytest.raises(DeliveryBlocked, match="live|checks"):
        context["coordinator"].record_review_and_checks(
            context["task_id"], context["packet"]
        )
    assert context["coordinator"]._get(context["task_id"]).state == "fork_review_pending"
    context["conn"].close()


@pytest.mark.parametrize("gate", ["checks", "review", "branch_protection"])
def test_packet_green_cannot_override_a_live_failed_gate(
    isolated_delivery_home: Path, tmp_path: Path, gate: str
):
    context = _advance_to_review(
        _new_context(tmp_path, github=LiveGateFailureGitHub(gate))
    )
    with pytest.raises(DeliveryBlocked, match="live|check|review|protection|branch"):
        context["coordinator"].record_review_and_checks(
            context["task_id"], context["packet"]
        )
    assert context["coordinator"]._get(context["task_id"]).state == "fork_review_pending"
    context["conn"].close()


@pytest.mark.parametrize(
    "env_name",
    ["HERMES_KANBAN_TASK", "HERMES_DELEGATED_CHILD_CONTEXT"],
)
def test_workers_cannot_write_tier_b_evidence_or_auto_merge(
    isolated_delivery_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
):
    context = _advance_to_ci_green(
        _advance_to_review(_new_context(tmp_path, risk_policy=_tiered_policy()))
    )
    monkeypatch.setenv(env_name, "worker-context")
    coordinator: DeliveryCoordinator = context["coordinator"]

    with pytest.raises(DeliveryBlocked, match="worker|gateway|delegated"):
        coordinator.record_risk_evidence(
            context["task_id"],
            actor="hermes-policy",
            evidence={"security_scan": {"status": "passed"}},
        )
    with pytest.raises(DeliveryBlocked, match="worker|gateway|delegated"):
        coordinator.merge(context["task_id"])
    assert context["github"].merge_calls == 0
    context["conn"].close()


def test_delivery_coordinator_defaults_to_tiered_policy(
    isolated_delivery_home: Path,
    tmp_path: Path,
):
    _repo, _origin, _upstream, _base_sha = _create_local_repositories(tmp_path)
    conn = kb.connect()
    coordinator = DeliveryCoordinator(
        conn,
        git=RecordingGit(),
        github=DeterministicGitHub(),
    )

    assert coordinator.risk_policy["mode"] == "tiered"
    assert coordinator.risk_policy["auto_merge"] is True
    assert coordinator.risk_policy["auto_cleanup"] is True
    conn.close()


def test_external_controller_auto_merges_tier_a_once_and_notifies_once(
    isolated_delivery_home: Path,
    tmp_path: Path,
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(tmp_path, risk_policy=_tiered_policy())
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    task_id = context["task_id"]

    first = coordinator.controller_once(task_id)
    assert first["state"] == "completed"
    assert context["github"].merge_calls == 1

    events = context["conn"].execute(
        "SELECT kind, payload FROM task_events WHERE task_id = ? "
        "AND kind = 'delivery_notification'",
        (task_id,),
    ).fetchall()
    assert len(events) == 1
    payload = json.loads(events[0]["payload"])
    assert payload["notification"] == "tier_a_auto_merge"
    assert payload["tier"] == "A"
    assert payload["head_sha"] == context["opened"].commit_sha

    second = coordinator.controller_once(task_id)
    assert second == first
    assert context["github"].merge_calls == 1
    assert context["conn"].execute(
        "SELECT COUNT(*) FROM task_events WHERE task_id = ? "
        "AND kind = 'delivery_notification'",
        (task_id,),
    ).fetchone()[0] == 1
    context["conn"].execute(
        "DELETE FROM task_events WHERE task_id = ? AND kind = 'delivery_notification'",
        (task_id,),
    )
    context["conn"].commit()
    assert coordinator.merge(task_id)["state"] == "completed"
    assert context["conn"].execute(
        "SELECT COUNT(*) FROM task_events WHERE task_id = ? "
        "AND kind = 'delivery_notification'",
        (task_id,),
    ).fetchone()[0] == 1
    context["conn"].close()


def test_external_controller_refuses_gateway_worker_context(
    isolated_delivery_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(tmp_path, risk_policy=_tiered_policy())
        )
    )
    monkeypatch.setenv("HERMES_KANBAN_TASK", context["task_id"])
    with pytest.raises(DeliveryBlocked, match="worker|gateway|delegated"):
        context["coordinator"].controller_once(context["task_id"])
    assert context["coordinator"]._get(context["task_id"]).state == "fork_ci_green"
    assert context["github"].merge_calls == 0
    context["conn"].close()


def test_tier_b_controller_stops_until_external_evidence_and_rollback(
    isolated_delivery_home: Path,
    tmp_path: Path,
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(
                tmp_path,
                risk_policy=_tiered_policy(),
                change_paths=("pyproject.toml",),
            )
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    first = coordinator.controller_once(context["task_id"])
    assert first["state"] == "fork_ci_green"
    assert first["controller_action"] == "awaiting_tier_b_evidence"
    assert context["github"].merge_calls == 0
    risk_events = context["conn"].execute(
        "SELECT payload FROM task_events WHERE task_id = ? "
        "AND kind = 'delivery_notification'",
        (context["task_id"],),
    ).fetchall()
    assert len(risk_events) == 1
    assert json.loads(risk_events[0]["payload"])["notification"] == "risk_escalation"

    coordinator.record_risk_evidence(
        context["task_id"],
        actor="external-policy-controller",
        evidence={
            "security_scan": {"status": "passed"},
            "staged_health": {"status": "passed"},
            "rollback_artifact": {"status": "ready", "sha256": "a" * 64},
        },
    )
    second = coordinator.controller_once(context["task_id"])
    assert second["state"] == "completed"
    assert context["github"].merge_calls == 1
    context["conn"].close()


def test_merged_closed_pr_is_normalized_only_with_explicit_merged_flag(
    isolated_delivery_home: Path,
    tmp_path: Path,
):
    context = _advance_to_ci_green(
        _advance_to_review(
            _new_context(tmp_path, github=ClosedMergedGitHub())
        )
    )
    coordinator: DeliveryCoordinator = context["coordinator"]
    packet_hash = ReviewPacket.from_mapping(context["packet"]).packet_hash
    coordinator.authorize_merge(
        context["task_id"],
        actor="owner",
        source="operator_cli",
        packet_hash=packet_hash,
        method="squash",
        reason="closed plus merged provider read-back",
        confirmation=True,
    )
    merged = coordinator.merge(context["task_id"])
    assert merged["merged_commit_sha"] == MERGED_SHA
    context["conn"].close()
