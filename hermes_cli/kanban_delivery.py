"""Resumable, fail-closed Git/GitHub delivery for Kanban tasks.

The normal Kanban worker still edits and validates code with terminal/file tools.
This module owns only the durable delivery boundary: immutable repository/PR
identity, idempotent Git/GitHub effects, exact-head review/check gates, a
config-driven risk-tiered merge authorization boundary, and the external runtime
cutover handoff.

No subprocess is executed while a SQLite write transaction is held. Every
external effect is recorded as ``started`` before execution and read back before
an ambiguous retry. Persisted payloads are canonical JSON and redact credential-
shaped values before they reach the board.
"""

from __future__ import annotations

import hashlib
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol, Sequence
from urllib.parse import urlsplit

from hermes_cli import kanban_db as kb

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure identity/state contracts
# ---------------------------------------------------------------------------

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_BRANCH_RE = re.compile(r"^[^\x00-\x1f\x7f\s]{1,255}$")
_REMOTE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
_PR_URL_RE = re.compile(
    r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)/?$",
    re.IGNORECASE,
)
_SECRET_RE = re.compile(
    r"(?:ghp_[A-Za-z0-9_\-]{20,}|github_pat_[A-Za-z0-9_\-]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{12,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._\-+/=]{12,})",
    re.IGNORECASE,
)

TARGET_POLICIES = frozenset({"fork_only", "fork_with_upstream_sync"})
MERGE_METHODS = frozenset({"squash", "merge", "rebase"})
DELIVERY_STATES = frozenset(
    {
        "intake",
        "upstream_sync_pending",
        "upstream_sync_review_pending",
        "upstream_sync_ci_green",
        "upstream_sync_authorization_pending",
        "upstream_sync_verified",
        "upstream_sync_not_required",
        "workspace_admitted",
        "worktree_ready",
        "editing",
        "validated",
        "committed",
        "fork_pushed",
        "fork_pr_open",
        "fork_review_pending",
        "fork_ci_green",
        "merge_authorization_pending",
        "fork_merge_verified",
        "runtime_cutover_pending",
        "rollback_pack_ready",
        "runtime_materialized",
        "activation_pending",
        "activation_verified",
        "completed",
        "blocked",
        "needs_input",
        "aborted",
    }
)

# A transition is deliberately explicit. There is no generic "set state"
# escape hatch, so a stale worker cannot jump over an authorization gate.
_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "intake": frozenset({"upstream_sync_pending", "upstream_sync_not_required", "blocked", "aborted"}),
    "upstream_sync_pending": frozenset({"upstream_sync_review_pending", "upstream_sync_verified", "blocked", "aborted"}),
    "upstream_sync_review_pending": frozenset({"upstream_sync_ci_green", "blocked", "aborted"}),
    "upstream_sync_ci_green": frozenset({"upstream_sync_authorization_pending", "blocked", "aborted"}),
    "upstream_sync_authorization_pending": frozenset({"upstream_sync_verified", "blocked", "aborted"}),
    "upstream_sync_verified": frozenset({"workspace_admitted", "blocked", "aborted"}),
    "upstream_sync_not_required": frozenset({"workspace_admitted", "blocked", "aborted"}),
    "workspace_admitted": frozenset({"worktree_ready", "editing", "blocked", "aborted"}),
    "worktree_ready": frozenset({"editing", "blocked", "aborted"}),
    "editing": frozenset({"validated", "blocked", "aborted"}),
    "validated": frozenset({"committed", "blocked", "aborted"}),
    "committed": frozenset({"fork_pushed", "blocked", "aborted"}),
    "fork_pushed": frozenset({"fork_pr_open", "blocked", "aborted"}),
    "fork_pr_open": frozenset({"fork_review_pending", "fork_ci_green", "blocked", "aborted"}),
    "fork_review_pending": frozenset({"editing", "fork_ci_green", "blocked", "aborted"}),
    "fork_ci_green": frozenset({"merge_authorization_pending", "blocked", "aborted"}),
    "merge_authorization_pending": frozenset({"fork_merge_verified", "blocked", "aborted"}),
    "fork_merge_verified": frozenset({"runtime_cutover_pending", "completed", "blocked", "aborted"}),
    "runtime_cutover_pending": frozenset({"rollback_pack_ready", "blocked", "aborted"}),
    "rollback_pack_ready": frozenset({"runtime_materialized", "blocked", "aborted"}),
    "runtime_materialized": frozenset({"activation_pending", "blocked", "aborted"}),
    "activation_pending": frozenset({"activation_verified", "blocked", "aborted"}),
    "activation_verified": frozenset({"completed", "blocked", "aborted"}),
    "completed": frozenset(),
    "blocked": frozenset({"aborted", "editing", "fork_review_pending", "needs_input"}),
    "needs_input": frozenset({"aborted", "editing", "blocked"}),
    "aborted": frozenset(),
}


class DeliveryError(RuntimeError):
    """Base class for delivery failures safe to show to an operator."""


class DeliveryBlocked(DeliveryError):
    """A required safety gate is not satisfied."""


class DeliveryStateError(DeliveryError):
    """An operation was attempted from an incompatible phase."""


class DeliveryConflict(DeliveryError):
    """A durable identity or effect key conflicts with the requested one."""


class EffectPending(DeliveryBlocked):
    """An earlier external effect is ambiguous and needs read-back."""


def canonical_json(value: Any) -> str:
    """Return stable JSON for hashes and persisted evidence."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _safe_value(value: Any, *, key: str = "") -> Any:
    """Recursively redact credential-shaped values before persistence."""
    lowered = key.casefold()
    if any(token in lowered for token in ("token", "password", "secret", "cookie", "authorization")) and not isinstance(value, (Mapping, list, tuple)):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): _safe_value(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item, key=key) for item in value]
    if isinstance(value, str):
        value = _SECRET_RE.sub("[REDACTED]", value)
        # Never persist a URL containing userinfo, even if it did not match a
        # provider token pattern.
        value = re.sub(r"(https?://)([^/@\s]+):([^/@\s]+)@", r"\1[REDACTED]@", value)
    return value


def safe_json(value: Any) -> str:
    return canonical_json(_safe_value(value))


def _safe_diagnostic(value: Any) -> str:
    text = str(value or "")
    text = _SECRET_RE.sub("[REDACTED]", text)
    # Keep durable errors short and independent of provider stderr.
    return text[:500] or "external operation failed"


# The policy is intentionally data-only so operators can review and change the
# allow/deny rules in config.yaml without changing the delivery state machine.
DEFAULT_RISK_POLICY: dict[str, Any] = {
    "policy_id": "hermes-tiered-v1",
    "mode": "tiered",
    "auto_merge": True,
    "auto_cleanup": True,
    "tier_a_allow_paths": ["*.md", "*.json", "*.yaml", "*.yml", "tests/**", "docs/**"],
    "tier_b_paths": ["pyproject.toml", "setup.py", "package.json", "package-lock.json", "uv.lock", "*.lock", "Dockerfile", "*.sh"],
    "protected_paths": [
        "*.pem",
        "**/*.pem",
        "*.key",
        "**/*.key",
        ".env*",
        "auth/**",
        "auth.py",
        "**/auth.py",
        "*credential*.py",
        "**/*credential*.py",
        "*secret*.py",
        "**/*secret*.py",
        "secret_scope.py",
        "**/secret_scope.py",
        "agent/**",
        "gateway/**",
        "security/**",
        "tools/**",
        "run_agent.py",
        "cli.py",
        "model_tools.py",
        "toolsets.py",
        "*prompt*cache*",
        "**/*prompt*cache*",
        "*context*compress*.py",
        "**/*context*compress*.py",
        "deploy/**",
        "systemd/**",
        "migrations/**",
    ],
    "required_tier_b_evidence": ["security_scan", "staged_health", "rollback_artifact"],
    "branch_protection_required": True,
    "require_independent_model_family": True,
    "implementer_model_family": "primary",
    "implementer_actor": "",
    "independent_model_family_provenance": {},
}


@dataclass(frozen=True)
class RiskDecision:
    """Durable, explainable result of the delivery path-risk classifier."""

    tier: str
    reason: str
    classifier_inputs: dict[str, Any]
    protected_path_rules: tuple[str, ...]
    required_evidence: tuple[str, ...]
    rollback_required: bool

    def as_dict(self) -> dict[str, Any]:
        return _safe_value(
            {
                "tier": self.tier,
                "reason": self.reason,
                "classifier_inputs": self.classifier_inputs,
                "protected_path_rules": list(self.protected_path_rules),
                "required_evidence": list(self.required_evidence),
                "rollback_required": self.rollback_required,
            }
        )


def normalize_risk_policy(value: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
    """Normalize config data while preserving a fail-closed policy shape."""
    source = dict(DEFAULT_RISK_POLICY)
    if value is not None:
        if not isinstance(value, Mapping):
            raise ValueError("delivery risk policy must be an object")
        source.update(dict(value))
    mode = str(source.get("mode") or "tiered").casefold()
    if mode not in {"tiered", "human"}:
        raise ValueError("delivery risk policy mode must be tiered or human")

    def patterns(name: str) -> list[str]:
        raw = source.get(name)
        if raw is None:
            raw = DEFAULT_RISK_POLICY.get(name, [])
        if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
            raise ValueError(f"delivery risk policy {name} must be a list")
        return sorted({str(item).strip().replace("\\", "/") for item in raw if str(item).strip()})

    required = source.get("required_tier_b_evidence", DEFAULT_RISK_POLICY["required_tier_b_evidence"])
    if isinstance(required, str) or not isinstance(required, (list, tuple)):
        raise ValueError("delivery risk policy required_tier_b_evidence must be a list")

    provenance_value = source.get(
        "independent_model_family_provenance",
        DEFAULT_RISK_POLICY["independent_model_family_provenance"],
    )
    provenance: dict[str, dict[str, str]] = {}
    if isinstance(provenance_value, Mapping):
        rejected_sources = {
            "body",
            "github_review",
            "metadata",
            "review_body",
            "review_metadata",
            "self",
            "self_declared",
        }
        for actor_value, entry in provenance_value.items():
            actor = str(actor_value or "").strip().casefold()
            if not actor or not isinstance(entry, Mapping):
                continue
            family = str(entry.get("model_family") or entry.get("family") or "").strip()
            source_name = str(entry.get("source") or "").strip()
            issuer = str(entry.get("issuer") or "").strip()
            attestation_id = str(
                entry.get("attestation_id") or entry.get("record_id") or ""
            ).strip()
            if (
                family
                and source_name
                and source_name.casefold() not in rejected_sources
                and issuer
                and issuer.casefold() != actor
                and attestation_id
            ):
                provenance[actor] = {
                    "model_family": family[:100],
                    "source": source_name[:200],
                    "issuer": issuer[:200],
                    "attestation_id": attestation_id[:200],
                }
    elif provenance_value not in (None, ""):
        raise ValueError("delivery risk policy independent_model_family_provenance must be an object")
    policy = {
        "policy_id": str(source.get("policy_id") or "hermes-tiered-v1")[:100],
        "mode": mode,
        "auto_merge": bool(source.get("auto_merge", True)),
        "auto_cleanup": bool(source.get("auto_cleanup", True)),
        "tier_a_allow_paths": patterns("tier_a_allow_paths"),
        "tier_b_paths": patterns("tier_b_paths"),
        "protected_paths": patterns("protected_paths"),
        "required_tier_b_evidence": sorted({str(item).strip() for item in required if str(item).strip()}),
        "branch_protection_required": bool(source.get("branch_protection_required", True)),
        "require_independent_model_family": bool(source.get("require_independent_model_family", True)),
        "implementer_model_family": str(source.get("implementer_model_family") or "primary")[:100],
        "implementer_actor": str(source.get("implementer_actor") or "")[:200],
        "independent_model_family_provenance": provenance,
    }
    return policy


def classify_delivery_risk(
    changed_paths: Sequence[str],
    *,
    target_policy: str,
    policy: Optional[Mapping[str, Any]] = None,
) -> RiskDecision:
    """Classify a delivery scope; protected and unknown paths always win."""
    normalized: list[str] = []
    invalid: list[str] = []
    for raw in changed_paths:
        path = str(raw).strip().replace("\\", "/")
        if not path or path.startswith("/") or "\x00" in path or any(part == ".." for part in Path(path).parts):
            invalid.append(path or "<empty>")
        else:
            normalized.append(path)
    normalized = sorted(set(normalized))
    effective = normalize_risk_policy(policy)
    protected = tuple(effective["protected_paths"])
    inputs = {
        "changed_paths": normalized,
        "target_policy": str(target_policy),
        "invalid_paths": invalid,
        "policy_id": effective["policy_id"],
    }
    if invalid or not normalized:
        return RiskDecision("C", "unknown or unsafe changed-file scope", inputs, protected, tuple(), True)

    protected_matches = sorted(
        {path for path in normalized if any(fnmatch.fnmatchcase(path, pattern) for pattern in protected)}
    )
    if protected_matches:
        inputs["protected_matches"] = protected_matches
        return RiskDecision("C", "protected path requires attributable human approval", inputs, protected, tuple(), True)

    tier_b_patterns = tuple(effective["tier_b_paths"])
    allow_patterns = tuple(effective["tier_a_allow_paths"])
    tier_b_matches = sorted(
        {path for path in normalized if any(fnmatch.fnmatchcase(path, pattern) for pattern in tier_b_patterns)}
    )
    all_allowlisted = bool(allow_patterns) and all(
        any(fnmatch.fnmatchcase(path, pattern) for pattern in allow_patterns) for path in normalized
    )
    inputs["tier_b_matches"] = tier_b_matches
    inputs["allowlisted"] = all_allowlisted
    if str(target_policy) != "fork_only" or tier_b_matches:
        return RiskDecision(
            "B",
            "broader or runtime-sensitive scope requires additional automated evidence",
            inputs,
            protected,
            tuple(effective["required_tier_b_evidence"]),
            True,
        )
    if all_allowlisted:
        return RiskDecision("A", "all changed paths are explicitly allow-listed", inputs, protected, tuple(), True)
    return RiskDecision("C", "changed path is outside the configured allow-list", inputs, protected, tuple(), True)


def _git_status_paths(status: str) -> list[str]:
    paths: list[str] = []
    for line in str(status or "").splitlines():
        if line.startswith("? "):
            paths.append(line[2:])
            continue
        if line.startswith(("1 ", "2 ", "u ")):
            fields = line.split("\t")
            if len(fields) > 1:
                paths.extend(field for field in fields[1:] if field)
            else:
                fields = line.split(maxsplit=8)
                if len(fields) > 8 and fields[8]:
                    paths.append(fields[8])
    return paths


def _git_status_inventory(status: str) -> dict[str, list[str]]:
    """Keep path-only dirty state; never persist file contents or raw blobs."""
    dirty: list[str] = []
    untracked: list[str] = []
    for line in str(status or "").splitlines():
        if line.startswith("? "):
            untracked.append(line[2:])
        elif line.startswith(("1 ", "2 ", "u ")):
            fields = line.split("\t")
            if len(fields) > 1:
                dirty.extend(field for field in fields[1:] if field)
            else:
                fields = line.split(maxsplit=8)
                if len(fields) > 8 and fields[8]:
                    dirty.append(fields[8])
    return {
        "dirty_paths": sorted(set(dirty)),
        "untracked_paths": sorted(set(untracked)),
    }


def _runtime_health_status(evidence: Mapping[str, Any]) -> str:
    statuses: list[str] = []
    for key in ("health", "dispatcher", "cron"):
        statuses.append(str(evidence.get(key) or "").strip().casefold())
    staged = evidence.get("staged_health")
    if isinstance(staged, Mapping) and staged.get("status") is not None:
        statuses.append(str(staged.get("status") or "").strip().casefold())
    healthy = {"ok", "healthy", "running", "passed", "success", "green"}
    failed = {"failed", "failure", "unhealthy", "error", "stopped", "red"}
    if statuses and all(status in healthy for status in statuses):
        return "healthy"
    if any(status in failed for status in statuses):
        return "failed"
    return "unknown"


def normalize_repository(value: Any) -> str:
    repository = str(value or "").strip().removesuffix(".git")
    if not _REPO_RE.fullmatch(repository):
        raise ValueError("repository must be canonical owner/name")
    return repository


def normalize_branch(value: Any, *, field: str = "branch") -> str:
    branch = str(value or "").strip()
    forbidden = set("~^:?*[\\]#%&")
    unsafe = (
        not _BRANCH_RE.fullmatch(branch)
        or branch.startswith(("-", "."))
        or branch.endswith((".", "/"))
        or ".." in branch
        or "//" in branch
        or "@{" in branch
        or any(char in forbidden for char in branch)
    )
    if unsafe:
        raise ValueError(f"{field} must be a safe non-empty Git branch name")
    return branch


def normalize_sha(value: Any, *, field: str = "sha") -> str:
    sha = str(value or "").strip().lower()
    if not _SHA_RE.fullmatch(sha):
        raise ValueError(f"{field} must be a 40-character lowercase commit SHA")
    return sha


def normalize_pr_url(repository: str, number: int, value: Any = None) -> str:
    expected = f"https://github.com/{repository}/pull/{int(number)}"
    if value in (None, ""):
        return expected
    text = str(value).strip()
    match = _PR_URL_RE.fullmatch(text)
    if match is None or f"{match.group(1)}/{match.group(2)}".casefold() != repository.casefold() or int(match.group(3)) != int(number):
        raise ValueError("pr_url must exactly identify the recorded GitHub repository and number")
    return expected


def validate_transition(current: str, new: str) -> None:
    if current not in DELIVERY_STATES or new not in DELIVERY_STATES:
        raise DeliveryStateError(f"unknown delivery state: {current!r} -> {new!r}")
    if new not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise DeliveryStateError(f"invalid delivery transition {current!r} -> {new!r}")


@dataclass(frozen=True)
class ReviewPacket:
    """Immutable exact-head review/check packet used by merge authorization."""

    provider: str
    repository: str
    remote: str
    pr_url: str
    pr_number: int
    branch: str
    head_sha: str
    base_branch: str
    base_sha: str
    review_decision: str
    review_actor: str
    reviewed_at: int
    checks_policy: str
    checks_exact_head_sha: str
    checks_all_required: bool
    checks_runs: tuple[dict[str, Any], ...]
    checked_at: int
    scope_sha256: Optional[str] = None
    review_model_family: Optional[str] = None
    branch_protected: Optional[bool] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewPacket":
        if not isinstance(value, Mapping):
            raise ValueError("review packet must be an object")
        provider = str(value.get("provider") or "github").casefold()
        if provider != "github":
            raise ValueError("review packet provider must be github")
        repository = normalize_repository(value.get("repository"))
        remote = str(value.get("remote") or "origin").strip()
        if not remote or remote == "upstream":
            raise ValueError("review packet remote must be a writable fork remote")
        number = int(value.get("pr_number") or value.get("number") or 0)
        if number <= 0:
            raise ValueError("review packet requires a positive pr_number")
        pr_url = normalize_pr_url(repository, number, value.get("pr_url"))
        branch = normalize_branch(value.get("branch"))
        head_sha = normalize_sha(value.get("head_sha"), field="head_sha")
        base_branch = normalize_branch(value.get("base_branch"), field="base_branch")
        base_sha = normalize_sha(value.get("base_sha"), field="base_sha")

        review_value = value.get("review")
        review: Mapping[str, Any] = review_value if isinstance(review_value, Mapping) else value
        decision = str(review.get("decision") or review.get("state") or "").casefold()
        if decision != "approved":
            raise ValueError("review packet requires an approved independent review")
        actor = str(review.get("actor") or review.get("review_actor") or "").strip()
        if not actor:
            raise ValueError("review packet requires a review actor")
        reviewed_at = int(review.get("reviewed_at") or review.get("at") or 0)
        if reviewed_at <= 0:
            raise ValueError("review packet requires reviewed_at")

        checks_value = value.get("checks")
        checks: Mapping[str, Any] = checks_value if isinstance(checks_value, Mapping) else {}
        exact_head = normalize_sha(
            checks.get("exact_head_sha"), field="checks.exact_head_sha"
        )
        if exact_head != head_sha:
            raise ValueError("checks.exact_head_sha must match immutable head_sha")
        if checks.get("all_required") is not True:
            raise ValueError("checks.all_required must be true")
        runs_value = checks.get("runs")
        if not isinstance(runs_value, list) or not runs_value:
            raise ValueError("checks.runs must contain completed required checks")
        runs: list[dict[str, Any]] = []
        for item in runs_value:
            if not isinstance(item, Mapping):
                raise ValueError("checks.runs contains an invalid item")
            item_copy = dict(item)
            status = str(item_copy.get("status") or "").casefold()
            conclusion = str(item_copy.get("conclusion") or "").casefold()
            if status != "completed" or conclusion != "success":
                raise ValueError("all required checks must be completed with success")
            runs.append(_safe_value(item_copy))
        checked_at = int(checks.get("checked_at") or checks.get("at") or 0)
        if checked_at <= 0:
            raise ValueError("checks require checked_at")
        branch_protected = checks.get("branch_protected")
        if branch_protected is not None and not isinstance(branch_protected, bool):
            raise ValueError("checks.branch_protected must be boolean when present")
        model_family = str(review.get("model_family") or "").strip() or None
        scope = value.get("scope_sha256")
        if scope is not None:
            scope = str(scope).strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", scope):
                raise ValueError("scope_sha256 must be a 64-character hash")
        packet = cls(
            provider="github",
            repository=repository,
            remote=remote,
            pr_url=pr_url,
            pr_number=number,
            branch=branch,
            head_sha=head_sha,
            base_branch=base_branch,
            base_sha=base_sha,
            review_decision="approved",
            review_actor=actor,
            reviewed_at=reviewed_at,
            checks_policy=str(checks.get("policy") or "required").strip() or "required",
            checks_exact_head_sha=exact_head,
            checks_all_required=True,
            checks_runs=tuple(runs),
            checked_at=checked_at,
            scope_sha256=scope,
            review_model_family=model_family,
            branch_protected=branch_protected,
        )
        return packet

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["checks_runs"] = list(self.checks_runs)
        value["review"] = {
            "decision": self.review_decision,
            "actor": self.review_actor,
            "reviewed_at": self.reviewed_at,
        }
        if self.review_model_family:
            value["review"]["model_family"] = self.review_model_family
        value["checks"] = {
            "policy": self.checks_policy,
            "exact_head_sha": self.checks_exact_head_sha,
            "all_required": self.checks_all_required,
            "runs": list(self.checks_runs),
            "checked_at": self.checked_at,
        }
        if self.branch_protected is not None:
            value["checks"]["branch_protected"] = self.branch_protected
        value.pop("review_decision", None)
        value.pop("review_actor", None)
        value.pop("reviewed_at", None)
        value.pop("checks_policy", None)
        value.pop("checks_exact_head_sha", None)
        value.pop("checks_all_required", None)
        value.pop("checks_runs", None)
        value.pop("checked_at", None)
        return _safe_value(value)

    @property
    def packet_hash(self) -> str:
        return sha256_json(self.as_dict())


@dataclass(frozen=True)
class GitResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DeliveryRecord:
    task_id: str
    delivery_version: int
    target_policy: str
    state: str
    project_id: str
    repository: str
    remote_name: str
    remote_url: Optional[str]
    base_branch: str
    base_sha: str
    branch: str
    workspace_kind: str
    workspace_path: str
    project_root: str
    reviewed_repository: Optional[str] = None
    reviewed_pr_number: Optional[int] = None
    reviewed_pr_url: Optional[str] = None
    reviewed_branch: Optional[str] = None
    reviewed_head_sha: Optional[str] = None
    reviewed_base_branch: Optional[str] = None
    reviewed_base_sha: Optional[str] = None
    review_snapshot: Optional[dict[str, Any]] = None
    review_actor: Optional[str] = None
    review_at: Optional[int] = None
    checks_snapshot: Optional[dict[str, Any]] = None
    validation_snapshot: Optional[dict[str, Any]] = None
    scope_sha256: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_parent_sha: Optional[str] = None
    merge_authorization: Optional[dict[str, Any]] = None
    merge_method: Optional[str] = None
    merge_attempt_key: Optional[str] = None
    merged_repository: Optional[str] = None
    merged_pr_number: Optional[int] = None
    merged_commit_sha: Optional[str] = None
    merge_actor: Optional[str] = None
    merged_at: Optional[int] = None
    upstream_sync: Optional[dict[str, Any]] = None
    upstream_source_sha: Optional[str] = None
    upstream_sync_disposition: Optional[str] = None
    runtime_remote: Optional[str] = None
    runtime_branch: Optional[str] = None
    runtime_before_sha: Optional[str] = None
    runtime_after_sha: Optional[str] = None
    runtime_integration_mode: Optional[str] = None
    rollback_pack_path: Optional[str] = None
    rollback_pack_sha256: Optional[str] = None
    rollback_manifest: Optional[dict[str, Any]] = None
    release_authorization: Optional[dict[str, Any]] = None
    activation_state: Optional[str] = None
    live_identity: Optional[dict[str, Any]] = None
    runtime_actions: Optional[list[dict[str, Any]]] = None
    activation_verified_at: Optional[int] = None
    last_error: Optional[dict[str, Any]] = None
    created_at: int = 0
    updated_at: int = 0

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "DeliveryRecord":
        def obj(name: str) -> Optional[dict[str, Any]]:
            raw = row.get(name) if hasattr(row, "get") else row[name]
            if not raw:
                return None
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                return parsed if isinstance(parsed, dict) else None
            except (TypeError, json.JSONDecodeError):
                return None

        def array(name: str) -> Optional[list[dict[str, Any]]]:
            raw = row.get(name) if hasattr(row, "get") else row[name]
            if not raw:
                return None
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                return parsed if isinstance(parsed, list) else None
            except (TypeError, json.JSONDecodeError):
                return None

        values = dict(row)
        return cls(
            task_id=str(values["task_id"]),
            delivery_version=int(values.get("delivery_version") or 1),
            target_policy=str(values["target_policy"]),
            state=str(values["state"]),
            project_id=str(values.get("project_id") or ""),
            repository=values["repository"],
            remote_name=values["remote_name"],
            remote_url=values.get("remote_url"),
            base_branch=values["base_branch"],
            base_sha=str(values["base_sha"]),
            branch=str(values["branch"]),
            workspace_kind=str(values["workspace_kind"]),
            workspace_path=str(values["workspace_path"]),
            project_root=str(values.get("project_root") or values["workspace_path"]),
            reviewed_repository=values.get("reviewed_repository"),
            reviewed_pr_number=values.get("reviewed_pr_number"),
            reviewed_pr_url=values.get("reviewed_pr_url"),
            reviewed_branch=values.get("reviewed_branch"),
            reviewed_head_sha=values.get("reviewed_head_sha"),
            reviewed_base_branch=values.get("reviewed_base_branch"),
            reviewed_base_sha=values.get("reviewed_base_sha"),
            review_snapshot=obj("review_snapshot_json"),
            review_actor=values.get("review_actor"),
            review_at=values.get("review_at"),
            checks_snapshot=obj("checks_snapshot_json"),
            validation_snapshot=obj("validation_snapshot_json"),
            scope_sha256=values.get("scope_sha256"),
            commit_sha=values.get("commit_sha"),
            commit_parent_sha=values.get("commit_parent_sha"),
            merge_authorization=obj("merge_authorization_json"),
            merge_method=values.get("merge_method"),
            merge_attempt_key=values.get("merge_attempt_key"),
            merged_repository=values.get("merged_repository"),
            merged_pr_number=values.get("merged_pr_number"),
            merged_commit_sha=values.get("merged_commit_sha"),
            merge_actor=values.get("merge_actor"),
            merged_at=values.get("merged_at"),
            upstream_sync=obj("upstream_sync_json"),
            upstream_source_sha=values.get("upstream_source_sha"),
            upstream_sync_disposition=values.get("upstream_sync_disposition"),
            runtime_remote=values.get("runtime_remote"),
            runtime_branch=values.get("runtime_branch"),
            runtime_before_sha=values.get("runtime_before_sha"),
            runtime_after_sha=values.get("runtime_after_sha"),
            runtime_integration_mode=values.get("runtime_integration_mode"),
            rollback_pack_path=values.get("rollback_pack_path"),
            rollback_pack_sha256=values.get("rollback_pack_sha256"),
            rollback_manifest=obj("rollback_manifest_json"),
            release_authorization=obj("release_authorization_json"),
            activation_state=values.get("activation_state"),
            live_identity=obj("live_identity_json"),
            runtime_actions=array("runtime_actions_json"),
            activation_verified_at=values.get("activation_verified_at"),
            last_error=obj("last_error_json"),
            created_at=int(values.get("created_at") or 0),
            updated_at=int(values.get("updated_at") or 0),
        )

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for field in (
            "review_snapshot",
            "checks_snapshot",
            "validation_snapshot",
            "merge_authorization",
            "upstream_sync",
            "rollback_manifest",
            "release_authorization",
            "live_identity",
            "runtime_actions",
            "last_error",
        ):
            result[field] = _safe_value(result[field])
        return result


# ---------------------------------------------------------------------------
# External adapters
# ---------------------------------------------------------------------------

class GitAdapter(Protocol):
    def validate_repository(self, path: Path) -> Mapping[str, str]: ...
    def remote_url_for(self, path: Path, remote: str) -> str: ...
    def rev_parse(self, path: Path, ref: str) -> str: ...
    def remote_head(self, path: Path, remote: str, branch: str) -> Optional[str]: ...


class GitHubAdapter(Protocol):
    def current_user(self) -> str: ...
    def get_pr(self, repository: str, number: int) -> Mapping[str, Any]: ...
    def find_pr(self, repository: str, head: str, base: str) -> Optional[Mapping[str, Any]]: ...
    def create_pr(self, repository: str, head: str, base: str, title: str, body: str) -> Mapping[str, Any]: ...
    def request_review(self, repository: str, number: int, reviewer: str) -> Mapping[str, Any]: ...
    def get_required_checks(self, repository: str, branch: str, head_sha: str) -> Mapping[str, Any]: ...
    def get_reviews(self, repository: str, number: int) -> Mapping[str, Any]: ...
    def get_branch_protection(self, repository: str, branch: str) -> Mapping[str, Any]: ...
    def merge_pr(self, repository: str, number: int, method: str, head_sha: str) -> Mapping[str, Any]: ...
    def delete_branch(self, repository: str, branch: str) -> Mapping[str, Any]: ...


class SubprocessGitAdapter:
    """Bounded local Git adapter with explicit argv and no shell interpolation."""

    def __init__(self, *, timeout: float = 30.0):
        self.timeout = float(timeout)

    def run(self, cwd: Path, *args: str, timeout: Optional[float] = None) -> GitResult:
        argv = ("git", *[str(arg) for arg in args])
        try:
            completed = subprocess.run(
                list(argv),
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
                check=False,
                env={key: value for key, value in os.environ.items() if key not in {"GIT_ASKPASS"}},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise DeliveryBlocked(f"git operation could not be executed: {_safe_diagnostic(exc)}") from None
        return GitResult(argv=argv, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)

    def _ok(self, result: GitResult, operation: str) -> str:
        if result.returncode != 0:
            raise DeliveryBlocked(f"git {operation} failed")
        return result.stdout.strip()

    def validate_repository(self, path: Path) -> Mapping[str, str]:
        path = Path(path).expanduser()
        if not path.is_absolute() or not path.is_dir():
            raise DeliveryBlocked("project path must be an existing absolute directory")
        root = Path(self._ok(self.run(path, "rev-parse", "--show-toplevel"), "repository validation")).resolve()
        common = Path(self._ok(self.run(path, "rev-parse", "--git-common-dir"), "worktree validation"))
        if not common.is_absolute():
            common = (path / common).resolve()
        common = common.resolve()
        return {"root": str(root), "common_dir": str(common)}

    def remote_url_for(self, path: Path, remote: str) -> str:
        return self._ok(self.run(path, "remote", "get-url", remote), "remote lookup")

    def rev_parse(self, path: Path, ref: str) -> str:
        return normalize_sha(self._ok(self.run(path, "rev-parse", "--verify", f"{ref}^{{commit}}"), "ref lookup"))

    def status_porcelain(self, path: Path) -> str:
        return self._ok(self.run(path, "status", "--porcelain=v2", "--untracked-files=all"), "status")

    def branch_name(self, path: Path) -> str:
        return self._ok(self.run(path, "symbolic-ref", "--quiet", "--short", "HEAD"), "branch lookup")

    def ensure_worktree(self, repository: Path, target: Path, branch: str, base_ref: str) -> Mapping[str, Any]:
        repository = Path(repository).resolve()
        target = Path(target).expanduser()
        if not target.is_absolute():
            raise DeliveryBlocked("worktree target must be absolute")
        if target == repository or repository in target.parents:
            raise DeliveryBlocked("worktree target is not isolated from the project repository")
        listed = self._ok(self.run(repository, "worktree", "list", "--porcelain"), "worktree list")
        for block in listed.split("\n\n"):
            lines = block.splitlines()
            existing_path = next((line[6:] for line in lines if line.startswith("worktree ")), None)
            existing_branch = next((line[11:] for line in lines if line.startswith("branch refs/heads/")), None)
            if existing_path and Path(existing_path).resolve() == target:
                if existing_branch != branch:
                    raise DeliveryConflict("worktree path is already linked to a different branch")
                return {"path": str(target), "branch": branch, "reused": True}
            if existing_branch == branch:
                raise DeliveryConflict("delivery branch is already linked to another worktree")
        if target.exists() and any(target.iterdir()):
            raise DeliveryBlocked("unexpected non-empty worktree target")
        target.parent.mkdir(parents=True, exist_ok=True)
        result = self.run(repository, "worktree", "add", "-b", branch, str(target), base_ref)
        self._ok(result, "worktree creation")
        return {"path": str(target), "branch": branch, "reused": False}

    def clean_diff_check(self, path: Path) -> None:
        self._ok(self.run(path, "diff", "--check"), "diff check")

    def commit(self, path: Path, message: str, paths: Optional[Sequence[str]] = None) -> Mapping[str, str]:
        if not message.strip():
            raise ValueError("commit message is required")
        if not paths:
            raise DeliveryBlocked("commit requires an explicit non-empty changed-file scope")
        for raw_path in paths:
            value = str(raw_path).strip()
            if not value or Path(value).is_absolute() or "\x00" in value or any(part == ".." for part in Path(value).parts):
                raise DeliveryBlocked("commit scope contains an unsafe path")
        self.clean_diff_check(path)
        status = self.status_porcelain(path)
        if not status:
            raise DeliveryBlocked("worktree has no changes to commit")
        scope = [Path(str(item).strip()) for item in paths]
        dirty = [Path(item) for item in _git_status_paths(status)]
        outside = [
            item for item in dirty
            if not any(item == allowed or allowed in item.parents for allowed in scope)
        ]
        if outside:
            raise DeliveryBlocked("worktree contains dirty files outside the declared commit scope")
        args: list[str] = ["add"]
        args.extend(["--", *[str(p).strip() for p in paths]])
        self._ok(self.run(path, *args), "staging")
        self._ok(self.run(path, "commit", "-m", message), "commit")
        sha = self.rev_parse(path, "HEAD")
        parent_result = self.run(path, "rev-parse", "HEAD^", timeout=self.timeout)
        parent = parent_result.stdout.strip() if parent_result.returncode == 0 else ""
        if parent:
            parent = normalize_sha(parent, field="commit_parent_sha")
        if self.status_porcelain(path):
            raise DeliveryBlocked("worktree remained dirty after commit")
        return {"sha": sha, "parent_sha": parent}

    def push(self, path: Path, remote: str, branch: str, head_sha: str) -> Mapping[str, str]:
        if remote == "upstream":
            raise DeliveryBlocked("upstream is fetch-only; feature pushes are forbidden")
        self._ok(self.run(path, "push", remote, f"HEAD:refs/heads/{branch}"), "push")
        remote_sha = self._ok(self.run(path, "ls-remote", remote, f"refs/heads/{branch}"), "push read-back")
        observed = remote_sha.split()[0] if remote_sha else ""
        if observed != head_sha:
            raise DeliveryBlocked("remote branch read-back does not match committed head")
        return {"remote": remote, "branch": branch, "head_sha": observed}

    def remote_head(self, path: Path, remote: str, branch: str) -> Optional[str]:
        result = self.run(path, "ls-remote", remote, f"refs/heads/{branch}")
        if result.returncode != 0:
            raise DeliveryBlocked("remote branch read-back failed")
        observed = result.stdout.strip().split()[0] if result.stdout.strip() else ""
        return normalize_sha(observed, field="remote_head_sha") if observed else None

    def fetch(self, path: Path, remote: str, ref: str) -> Mapping[str, str]:
        if remote != "upstream":
            raise DeliveryBlocked("upstream synchronization requires the upstream remote")
        self._ok(self.run(path, "fetch", "--no-tags", remote, ref), "upstream fetch")
        sha = self.rev_parse(path, f"FETCH_HEAD")
        return {"remote": remote, "ref": ref, "sha": sha, "transport": "git-fetch"}

    def remove_worktree(self, repository: Path, target: Path) -> None:
        status = self.status_porcelain(target)
        if status:
            raise DeliveryBlocked("refusing to remove a dirty delivery worktree")
        self._ok(self.run(repository, "worktree", "remove", "--", str(target)), "worktree cleanup")

    def rollback_runtime(self, path: Path, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        """Restore a runtime checkout using only the immutable pack commands."""
        path = Path(path).expanduser().resolve()
        runtime = manifest.get("runtime") if isinstance(manifest, Mapping) else None
        restore = manifest.get("restore") if isinstance(manifest, Mapping) else None
        if not isinstance(runtime, Mapping) or not isinstance(restore, Mapping):
            raise DeliveryBlocked("rollback pack is missing runtime restore metadata")
        before_sha = normalize_sha(runtime.get("before_sha"), field="rollback_before_sha")
        expected_after = runtime.get("after_sha")
        if expected_after:
            expected_after = normalize_sha(expected_after, field="rollback_after_sha")
        current_sha = self.rev_parse(path, "HEAD")
        if expected_after and current_sha != expected_after:
            raise DeliveryConflict("runtime checkout head changed after materialization")
        expected_path = str(runtime.get("path") or "").strip()
        if expected_path and Path(expected_path).expanduser().resolve() != path:
            raise DeliveryConflict("runtime checkout path changed after materialization")
        expected_branch = str(runtime.get("branch") or "").strip()
        if expected_branch and self.branch_name(path) != expected_branch:
            raise DeliveryConflict("runtime checkout branch changed after materialization")
        identity = runtime.get("identity")
        expected_remote_url = (
            str(identity.get("remote_url") or "").strip()
            if isinstance(identity, Mapping)
            else ""
        )
        remote_name = str(runtime.get("remote") or "").strip()
        if expected_remote_url and remote_name:
            observed_remote_url = _safe_remote_url(self.remote_url_for(path, remote_name))
            if observed_remote_url != expected_remote_url:
                raise DeliveryConflict("runtime checkout remote changed after materialization")
        commands = restore.get("commands")
        expected_commands = [
            ["git", "-C", str(path), "reset", "--hard", before_sha],
            ["git", "-C", str(path), "clean", "-fd"],
        ]
        if commands != expected_commands:
            raise DeliveryConflict("rollback pack restore command does not match runtime identity")
        inventory = manifest.get("inventory")
        if isinstance(inventory, Mapping) and (
            inventory.get("dirty_paths") or inventory.get("untracked_paths")
        ):
            raise DeliveryBlocked(
                "runtime rollback refuses to discard pre-existing dirty or untracked paths"
            )
        results: list[dict[str, Any]] = []
        for args in (("reset", "--hard", before_sha), ("clean", "-fd")):
            result = self.run(path, *args)
            results.append(
                {
                    "returncode": result.returncode,
                    "stderr": _safe_diagnostic(result.stderr) if result.stderr else None,
                }
            )
            if result.returncode != 0:
                raise DeliveryBlocked("runtime rollback command failed")
        restored_sha = self.rev_parse(path, "HEAD")
        if restored_sha != before_sha or self.status_porcelain(path):
            raise DeliveryBlocked("runtime rollback read-back is not clean at the prepared revision")
        return {
            "status": "passed",
            "commands": expected_commands,
            "results": results,
            "before_sha": before_sha,
            "after_sha": restored_sha,
            "verified_clean": True,
        }


class GhGitHubAdapter:
    """GitHub adapter through authenticated ``gh api`` with redacted errors."""

    def __init__(self, *, timeout: float = 30.0, executable: Optional[str] = None):
        self.timeout = float(timeout)
        self.executable = executable or shutil.which("gh") or "gh"

    def _api(self, endpoint: str, *, method: str = "GET", fields: Optional[Mapping[str, Any]] = None) -> Any:
        argv = [self.executable, "api", endpoint, "--hostname", "github.com", "--method", method]
        for key, value in (fields or {}).items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    argv.extend(["-f", f"{key}[]={item}"])
            else:
                argv.extend(["-f", f"{key}={value}"])
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise DeliveryBlocked(f"GitHub provider unavailable: {_safe_diagnostic(exc)}") from None
        if completed.returncode != 0:
            raise DeliveryBlocked("GitHub provider operation failed")
        if not completed.stdout.strip():
            return {}
        try:
            payload = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError):
            raise DeliveryBlocked("GitHub provider returned invalid JSON") from None
        if not isinstance(payload, (Mapping, list)):
            raise DeliveryBlocked("GitHub provider returned an unexpected response")
        return payload

    def get_pr(self, repository: str, number: int) -> Mapping[str, Any]:
        return self._api(f"repos/{normalize_repository(repository)}/pulls/{int(number)}")

    def current_user(self) -> str:
        payload = self._api("user")
        login = str(payload.get("login") or "").strip() if isinstance(payload, Mapping) else ""
        if not login:
            raise DeliveryBlocked("GitHub provider did not return an authenticated owner identity")
        return login

    def find_pr(self, repository: str, head: str, base: str) -> Optional[Mapping[str, Any]]:
        repo = normalize_repository(repository)
        # Pull search is not authoritative for an exact head, so fetch the
        # bounded all-state list and compare head/base in Python. Closed or
        # draft matches are returned so callers fail closed rather than create a duplicate.
        payload = self._api(f"repos/{repo}/pulls?state=all&per_page=100")
        items = payload if isinstance(payload, list) else []
        matches = []
        for item in items:
            if not isinstance(item, Mapping):
                continue
            item_head = item.get("head") if isinstance(item.get("head"), Mapping) else {}
            item_base = item.get("base") if isinstance(item.get("base"), Mapping) else {}
            if item_head.get("ref") == head and item_base.get("ref") == base:
                matches.append(item)
        if len(matches) > 1:
            raise DeliveryConflict("multiple open pull requests match the immutable head/base")
        return matches[0] if matches else None

    def create_pr(self, repository: str, head: str, base: str, title: str, body: str) -> Mapping[str, Any]:
        return self._api(
            f"repos/{normalize_repository(repository)}/pulls",
            method="POST",
            fields={"head": head, "base": base, "title": title, "body": body},
        )

    def request_review(self, repository: str, number: int, reviewer: str) -> Mapping[str, Any]:
        return self._api(
            f"repos/{normalize_repository(repository)}/pulls/{int(number)}/requested_reviewers",
            method="POST",
            fields={"reviewers": [reviewer]},
        )

    def get_required_checks(self, repository: str, branch: str, head_sha: str) -> Mapping[str, Any]:
        repository = normalize_repository(repository)
        branch = normalize_branch(branch, field="base_branch")
        head_sha = normalize_sha(head_sha, field="checks_head_sha")
        check_runs = self._api(
            f"repos/{repository}/commits/{head_sha}/check-runs?per_page=100"
        )
        statuses = self._api(f"repos/{repository}/commits/{head_sha}/status")
        if not isinstance(check_runs, Mapping) or not isinstance(statuses, Mapping):
            raise DeliveryBlocked("GitHub provider returned invalid live check evidence")
        return {
            "head_sha": head_sha,
            "branch": branch,
            "runs": check_runs.get("check_runs", []),
            "statuses": statuses.get("statuses", []),
            "checked_at": int(time.time()),
        }

    def get_reviews(self, repository: str, number: int) -> Mapping[str, Any]:
        repository = normalize_repository(repository)
        payload = self._api(f"repos/{repository}/pulls/{int(number)}/reviews?per_page=100")
        if not isinstance(payload, list):
            raise DeliveryBlocked("GitHub provider returned invalid live review evidence")
        return {"reviews": payload, "pr_number": int(number)}

    def get_branch_protection(self, repository: str, branch: str) -> Mapping[str, Any]:
        repository = normalize_repository(repository)
        branch = normalize_branch(branch, field="base_branch")
        payload = self._api(f"repos/{repository}/branches/{branch}/protection")
        if not isinstance(payload, Mapping):
            raise DeliveryBlocked("GitHub provider returned invalid live branch protection")
        return {
            "enabled": True,
            "branch": branch,
            "required_status_checks": payload.get("required_status_checks"),
            "raw": payload,
        }

    def merge_pr(self, repository: str, number: int, method: str, head_sha: str) -> Mapping[str, Any]:
        if method not in MERGE_METHODS:
            raise ValueError("unsupported merge method")
        head_sha = normalize_sha(head_sha, field="merge_head_sha")
        return self._api(
            f"repos/{normalize_repository(repository)}/pulls/{int(number)}/merge",
            method="PUT",
            fields={"merge_method": method, "sha": head_sha},
        )

    def delete_branch(self, repository: str, branch: str) -> Mapping[str, Any]:
        return self._api(
            f"repos/{normalize_repository(repository)}/git/refs/heads/{branch}",
            method="DELETE",
        )


# ---------------------------------------------------------------------------
# Durable schema/effect helpers
# ---------------------------------------------------------------------------

DELIVERY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kanban_deliveries (
    task_id TEXT PRIMARY KEY,
    delivery_version INTEGER NOT NULL,
    target_policy TEXT NOT NULL,
    state TEXT NOT NULL,
    project_id TEXT NOT NULL,
    repository TEXT NOT NULL,
    remote_name TEXT NOT NULL,
    remote_url TEXT,
    base_branch TEXT NOT NULL,
    base_sha TEXT NOT NULL,
    branch TEXT NOT NULL,
    workspace_kind TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    project_root TEXT,
    stack_parent_json TEXT,
    reviewed_repository TEXT,
    reviewed_pr_number INTEGER,
    reviewed_pr_url TEXT,
    reviewed_branch TEXT,
    reviewed_head_sha TEXT,
    reviewed_base_branch TEXT,
    reviewed_base_sha TEXT,
    review_snapshot_json TEXT,
    review_actor TEXT,
    review_at INTEGER,
    checks_snapshot_json TEXT,
    validation_snapshot_json TEXT,
    scope_sha256 TEXT,
    commit_sha TEXT,
    commit_parent_sha TEXT,
    merge_authorization_json TEXT,
    merge_method TEXT,
    merge_attempt_key TEXT,
    merged_repository TEXT,
    merged_pr_number INTEGER,
    merged_commit_sha TEXT,
    merge_actor TEXT,
    merged_at INTEGER,
    upstream_sync_json TEXT,
    upstream_source_sha TEXT,
    upstream_sync_disposition TEXT,
    runtime_remote TEXT,
    runtime_branch TEXT,
    runtime_before_sha TEXT,
    runtime_after_sha TEXT,
    runtime_integration_mode TEXT,
    rollback_pack_path TEXT,
    rollback_pack_sha256 TEXT,
    rollback_manifest_json TEXT,
    release_authorization_json TEXT,
    activation_state TEXT,
    live_identity_json TEXT,
    runtime_actions_json TEXT,
    activation_verified_at INTEGER,
    last_error_json TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS kanban_delivery_effects (
    task_id TEXT NOT NULL,
    effect_key TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT,
    started_at INTEGER NOT NULL,
    completed_at INTEGER,
    PRIMARY KEY (task_id, effect_key)
);
CREATE INDEX IF NOT EXISTS idx_delivery_state ON kanban_deliveries(state);
CREATE INDEX IF NOT EXISTS idx_delivery_pr ON kanban_deliveries(reviewed_repository, reviewed_pr_number);
"""


def ensure_schema(conn: Any) -> None:
    """Add delivery tables without changing legacy tasks/cards."""
    conn.executescript(DELIVERY_SCHEMA_SQL)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(kanban_deliveries)").fetchall()}
    if "remote_url" not in columns:
        conn.execute("ALTER TABLE kanban_deliveries ADD COLUMN remote_url TEXT")
    if "project_root" not in columns:
        conn.execute("ALTER TABLE kanban_deliveries ADD COLUMN project_root TEXT")
    if "runtime_actions_json" not in columns:
        conn.execute("ALTER TABLE kanban_deliveries ADD COLUMN runtime_actions_json TEXT")


def _row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, Mapping):
        return dict(row)
    return {key: row[key] for key in row.keys()}


def _event(conn: Any, task_id: str, kind: str, payload: Mapping[str, Any]) -> None:
    conn.execute(
        "INSERT INTO task_events (task_id, kind, payload, created_at) VALUES (?, ?, ?, ?)",
        (task_id, kind, safe_json(payload), int(time.time())),
    )


def _json_column(value: Any) -> Optional[str]:
    return None if value is None else safe_json(value)


def _worker_context_active() -> bool:
    """Return whether this process is a gateway/delegated Kanban worker."""
    return bool(
        os.environ.get("HERMES_KANBAN_TASK")
        or os.environ.get("HERMES_DELEGATED_CHILD_CONTEXT")
    )


def _reject_worker_context(operation: str) -> None:
    if _worker_context_active():
        raise DeliveryBlocked(f"gateway/delegated workers cannot {operation}")


def _payload_items(payload: Any, *keys: str) -> list[Mapping[str, Any]]:
    value: Any = payload
    if isinstance(payload, Mapping):
        for key in keys:
            candidate = payload.get(key)
            if candidate is not None:
                value = candidate
                break
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _live_sha(value: Any, *, field: str, expected: str) -> None:
    if value in (None, ""):
        return
    try:
        observed = normalize_sha(value, field=field)
    except ValueError:
        raise DeliveryBlocked(f"live {field} is invalid") from None
    if observed != expected:
        raise DeliveryConflict(f"live {field} does not match the immutable reviewed head")


def _required_check_names(*payloads: Any) -> list[str]:
    names: set[str] = set()
    for payload in payloads:
        if not isinstance(payload, Mapping):
            continue
        for key in ("required_names", "required_contexts"):
            value = payload.get(key)
            if isinstance(value, (list, tuple)):
                names.update(str(item).strip() for item in value if str(item).strip())
        for key in ("required_status_checks", "required_checks"):
            value = payload.get(key)
            if not isinstance(value, Mapping):
                continue
            contexts = value.get("contexts")
            if isinstance(contexts, (list, tuple)):
                names.update(str(item).strip() for item in contexts if str(item).strip())
            checks = value.get("checks")
            if isinstance(checks, (list, tuple)):
                for item in checks:
                    if isinstance(item, Mapping):
                        name = item.get("context") or item.get("name")
                        if str(name or "").strip():
                            names.add(str(name).strip())
    return sorted(names)


def _check_name(item: Mapping[str, Any]) -> str:
    return str(item.get("name") or item.get("context") or "").strip()


def _check_success(item: Mapping[str, Any]) -> bool:
    status = str(item.get("status") or "").casefold()
    conclusion = str(item.get("conclusion") or "").casefold()
    state = str(item.get("state") or "").casefold()
    return (status == "completed" and conclusion == "success") or state == "success"


def _live_check_evidence(
    payload: Any,
    protection: Any,
    *,
    head_sha: str,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise DeliveryBlocked("live required checks are unavailable")
    _live_sha(payload.get("head_sha") or payload.get("sha"), field="checks_head_sha", expected=head_sha)
    runs = _payload_items(payload, "runs", "check_runs")
    statuses = _payload_items(payload, "statuses")
    if not runs and not statuses:
        raise DeliveryBlocked("live required checks are missing")
    for item in [*runs, *statuses]:
        _live_sha(
            item.get("head_sha") or item.get("sha") or item.get("commit_id"),
            field="check_run_head_sha",
            expected=head_sha,
        )
    required = _required_check_names(protection, payload)
    if not required and payload.get("all_required") is True:
        required = sorted({_check_name(item) for item in [*runs, *statuses] if _check_name(item)})
    if not required:
        raise DeliveryBlocked("live branch protection did not declare required checks")
    if payload.get("all_required") is False:
        raise DeliveryBlocked("live required checks are not green")
    missing: list[str] = []
    failed: list[str] = []
    for name in required:
        matches = [item for item in [*runs, *statuses] if _check_name(item) == name]
        if not matches:
            missing.append(name)
        elif not any(_check_success(item) for item in matches):
            failed.append(name)
    if missing or failed:
        detail = ", ".join(
            [*(f"missing:{name}" for name in missing), *(f"failed:{name}" for name in failed)]
        )
        raise DeliveryBlocked(f"live required checks are not green: {detail}")
    return {
        "head_sha": head_sha,
        "required_names": required,
        "runs": [_safe_value(dict(item)) for item in runs],
        "statuses": [_safe_value(dict(item)) for item in statuses],
        "all_required": True,
        "checked_at": payload.get("checked_at") or int(time.time()),
    }


def _review_actor(item: Mapping[str, Any]) -> str:
    user = item.get("user")
    if isinstance(user, Mapping):
        return str(user.get("login") or user.get("name") or "").strip()
    return str(item.get("actor") or item.get("review_actor") or "").strip()


def _review_model_family(
    item: Mapping[str, Any],
    *,
    provenance: Optional[Mapping[str, Any]] = None,
    implementer_model_family: Optional[str] = None,
) -> Optional[str]:
    """Resolve family only from operator-owned durable provenance.

    Review bodies and metadata are writable by the implementer and therefore
    cannot attest to the model that produced an approval.  The provenance map
    is loaded from the delivery policy before the provider review is read and
    is keyed by the provider's reviewer identity.
    """
    actor = _review_actor(item).casefold()
    if not actor or not isinstance(provenance, Mapping):
        return None
    entry = provenance.get(actor)
    if not isinstance(entry, Mapping):
        for key, candidate in provenance.items():
            if str(key).casefold() == actor and isinstance(candidate, Mapping):
                entry = candidate
                break
    if not isinstance(entry, Mapping):
        return None
    family = str(entry.get("model_family") or entry.get("family") or "").strip()
    source = str(entry.get("source") or "").strip().casefold()
    issuer = str(entry.get("issuer") or "").strip()
    attestation_id = str(entry.get("attestation_id") or entry.get("record_id") or "").strip()
    if (
        not family
        or not source
        or source in {"body", "github_review", "metadata", "review_body", "review_metadata", "self", "self_declared"}
        or not issuer
        or issuer.casefold() == actor
        or not attestation_id
    ):
        return None
    if (
        implementer_model_family
        and family.casefold() == str(implementer_model_family).strip().casefold()
    ):
        return None
    return family[:100]


def _live_review_evidence(
    payload: Any,
    *,
    head_sha: str,
    implementer_actor: str,
    model_family_provenance: Optional[Mapping[str, Any]] = None,
    implementer_model_family: Optional[str] = None,
) -> dict[str, Any]:
    reviews = _payload_items(payload, "reviews")
    if not reviews:
        raise DeliveryBlocked("live independent review evidence is missing")
    approved: list[dict[str, Any]] = []
    for item in reviews:
        review_sha = item.get("commit_id") or item.get("head_sha") or item.get("commit_sha")
        if review_sha in (None, ""):
            continue
        try:
            observed_review_sha = normalize_sha(review_sha, field="review_head_sha")
        except ValueError:
            continue
        if observed_review_sha != head_sha:
            continue
        actor = _review_actor(item)
        state = str(item.get("state") or item.get("decision") or "").casefold().replace(" ", "_")
        if state in {"changes_requested", "changes-requested", "request_changes"}:
            raise DeliveryBlocked("live review has requested changes on the immutable head")
        if state == "approved" and actor and actor.casefold() != implementer_actor.casefold():
            model_family = _review_model_family(
                item,
                provenance=model_family_provenance,
                implementer_model_family=implementer_model_family,
            )
            if not model_family:
                raise DeliveryBlocked(
                    "live independent review lacks durable independent model-family provenance"
                )
            approved.append(
                {
                    "decision": "approved",
                    "actor": actor,
                    "commit_id": head_sha,
                    "reviewed_at": item.get("submitted_at") or item.get("reviewed_at") or int(time.time()),
                    "model_family": model_family,
                    "review_id": item.get("id"),
                }
            )
    if not approved:
        raise DeliveryBlocked("live review is missing an independent approval")
    return _safe_value(approved[-1])


def _live_branch_protection_evidence(payload: Any, *, branch: str) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or payload.get("enabled") is not True:
        raise DeliveryBlocked("live branch protection is not enabled")
    observed_branch = str(payload.get("branch") or "").strip()
    if observed_branch and observed_branch != branch:
        raise DeliveryConflict("live branch protection names a different base branch")
    return _safe_value(dict(payload))


def _read_live_review_checks(
    github: GitHubAdapter,
    packet: ReviewPacket,
    *,
    implementer_actor: str,
    model_family_provenance: Optional[Mapping[str, Any]] = None,
    implementer_model_family: Optional[str] = None,
) -> dict[str, Any]:
    probes = (
        ("required checks", "get_required_checks", (packet.repository, packet.base_branch, packet.head_sha)),
        ("reviews", "get_reviews", (packet.repository, packet.pr_number)),
        ("branch protection", "get_branch_protection", (packet.repository, packet.base_branch)),
    )
    values: dict[str, Any] = {}
    for label, name, args in probes:
        probe = getattr(github, name, None)
        if not callable(probe):
            raise DeliveryBlocked(f"live {label} adapter is unavailable")
        try:
            values[name] = probe(*args)
        except DeliveryBlocked:
            raise
        except Exception as exc:
            raise DeliveryBlocked(f"live {label} adapter failed: {_safe_diagnostic(exc)}") from None
    protection = _live_branch_protection_evidence(
        values["get_branch_protection"], branch=packet.base_branch
    )
    checks = _live_check_evidence(
        values["get_required_checks"], protection, head_sha=packet.head_sha
    )
    review = _live_review_evidence(
        values["get_reviews"],
        head_sha=packet.head_sha,
        implementer_actor=implementer_actor,
        model_family_provenance=model_family_provenance,
        implementer_model_family=implementer_model_family,
    )
    return {
        "checks": checks,
        "review": review,
        "branch_protection": protection,
    }


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class DeliveryCoordinator:
    """Durable delivery coordinator with injected external boundaries."""

    def __init__(
        self,
        conn: Any,
        *,
        git: Optional[GitAdapter] = None,
        github: Optional[GitHubAdapter] = None,
        now: Callable[[], int] = lambda: int(time.time()),
        risk_policy: Optional[Mapping[str, Any]] = None,
    ):
        self.conn = conn
        ensure_schema(conn)
        self.git = git or SubprocessGitAdapter()
        self.github = github or GhGitHubAdapter()
        self.now = now
        # The configured tiered policy is the production default. Tests or
        # compatibility callers that need the former human-only boundary must
        # opt into mode=human explicitly.
        self.risk_policy = normalize_risk_policy(risk_policy)

    @staticmethod
    def validate_transition(current: str, new: str) -> None:
        validate_transition(current, new)

    def _get(self, task_id: str) -> Optional[DeliveryRecord]:
        row = self.conn.execute(
            "SELECT * FROM kanban_deliveries WHERE task_id = ?", (task_id,)
        ).fetchone()
        return DeliveryRecord.from_row(row) if row else None

    def status(self, task_id: str) -> dict[str, Any]:
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        effects = self.conn.execute(
            "SELECT effect_key, request_fingerprint, status, result_json, started_at, completed_at "
            "FROM kanban_delivery_effects WHERE task_id = ? ORDER BY started_at",
            (task_id,),
        ).fetchall()
        return {
            "delivery": record.as_dict(),
            "effects": [
                {
                    "effect_key": row["effect_key"],
                    "request_fingerprint": row["request_fingerprint"],
                    "status": row["status"],
                    "result": _safe_value(json.loads(row["result_json"])) if row["result_json"] else None,
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                }
                for row in effects
            ],
        }

    def _set_state(
        self,
        task_id: str,
        new_state: str,
        *,
        expected: Optional[Iterable[str]] = None,
        fields: Optional[Mapping[str, Any]] = None,
        event: Optional[Mapping[str, Any]] = None,
    ) -> DeliveryRecord:
        if new_state not in DELIVERY_STATES:
            raise DeliveryStateError(f"unknown delivery state {new_state!r}")
        fields = dict(fields or {})
        expected_states = frozenset(expected) if expected is not None else None
        with kb.write_txn(self.conn):
            row = self.conn.execute(
                "SELECT * FROM kanban_deliveries WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                raise DeliveryError("delivery does not exist")
            current = str(row["state"])
            if expected_states is not None and current not in expected_states:
                raise DeliveryStateError(
                    f"delivery is {current!r}; expected one of {sorted(expected_states)}"
                )
            if current != new_state:
                validate_transition(current, new_state)
            assignments = ["state = ?", "updated_at = ?"]
            params: list[Any] = [new_state, int(self.now())]
            for name, value in fields.items():
                if name not in {
                    "target_policy", "project_id", "repository", "remote_name", "remote_url", "base_branch", "base_sha",
                    "branch", "workspace_kind", "workspace_path", "project_root", "stack_parent_json", "reviewed_repository",
                    "reviewed_pr_number", "reviewed_pr_url", "reviewed_branch", "reviewed_head_sha",
                    "reviewed_base_branch", "reviewed_base_sha", "review_snapshot_json", "review_actor", "review_at",
                    "checks_snapshot_json", "validation_snapshot_json", "scope_sha256", "commit_sha", "commit_parent_sha",
                    "merge_authorization_json", "merge_method", "merge_attempt_key", "merged_repository",
                    "merged_pr_number", "merged_commit_sha", "merge_actor", "merged_at", "upstream_sync_json",
                    "upstream_source_sha", "upstream_sync_disposition", "runtime_remote", "runtime_branch",
                    "runtime_before_sha", "runtime_after_sha", "runtime_integration_mode", "rollback_pack_path",
                    "rollback_pack_sha256", "rollback_manifest_json", "release_authorization_json", "activation_state",
                    "live_identity_json", "runtime_actions_json", "activation_verified_at", "last_error_json",
                }:
                    raise ValueError(f"unknown delivery field {name!r}")
                assignments.append(f"{name} = ?")
                params.append(_json_column(value) if name.endswith("_json") else value)
            params.append(task_id)
            cur = self.conn.execute(
                f"UPDATE kanban_deliveries SET {', '.join(assignments)} WHERE task_id = ? AND state = ?",
                [*params[:-1], task_id, current],
            )
            if cur.rowcount != 1:
                raise DeliveryConflict("delivery state changed concurrently; resume from durable state")
            if event is not None:
                _event(self.conn, task_id, "delivery_" + new_state, event)
        result = self._get(task_id)
        if result is None:
            raise DeliveryError("delivery disappeared after state transition")
        return result

    def _begin_effect(self, task_id: str, effect_key: str, request: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        fingerprint = sha256_json(request)
        with kb.write_txn(self.conn):
            row = self.conn.execute(
                "SELECT request_fingerprint, status, result_json FROM kanban_delivery_effects "
                "WHERE task_id = ? AND effect_key = ?",
                (task_id, effect_key),
            ).fetchone()
            if row is not None:
                if row["request_fingerprint"] != fingerprint:
                    raise DeliveryConflict("effect key was reused with a different immutable request")
                if row["status"] == "applied":
                    return json.loads(row["result_json"]) if row["result_json"] else {}
                if row["status"] in {"started", "ambiguous"}:
                    raise EffectPending("previous external effect is unresolved; read back before retry")
            now = int(self.now())
            self.conn.execute(
                "INSERT INTO kanban_delivery_effects "
                "(task_id, effect_key, request_fingerprint, status, started_at) VALUES (?, ?, ?, 'started', ?) "
                "ON CONFLICT(task_id, effect_key) DO UPDATE SET request_fingerprint=excluded.request_fingerprint, "
                "status='started', started_at=excluded.started_at, completed_at=NULL, result_json=NULL",
                (task_id, effect_key, fingerprint, now),
            )
            _event(self.conn, task_id, "delivery_effect_started", {"effect_key": effect_key, "request_fingerprint": fingerprint})
        return None

    def _effect(self, task_id: str, effect_key: str) -> Optional[dict[str, Any]]:
        row = self.conn.execute(
            "SELECT status, result_json FROM kanban_delivery_effects WHERE task_id = ? AND effect_key = ?",
            (task_id, effect_key),
        ).fetchone()
        if row is None:
            return None
        result = json.loads(row["result_json"]) if row["result_json"] else {}
        return {"status": row["status"], "result": result}

    def _finish_effect(self, task_id: str, effect_key: str, result: Mapping[str, Any], *, status: str = "applied") -> None:
        if status not in {"applied", "ambiguous", "failed"}:
            raise ValueError("invalid effect status")
        with kb.write_txn(self.conn):
            now = int(self.now())
            self.conn.execute(
                "UPDATE kanban_delivery_effects SET status = ?, result_json = ?, completed_at = ? "
                "WHERE task_id = ? AND effect_key = ?",
                (status, safe_json(result), now, task_id, effect_key),
            )
            _event(self.conn, task_id, "delivery_effect_" + status, {"effect_key": effect_key, "result": result})

    def _record_error(self, task_id: str, reason: str, *, state: str = "blocked") -> None:
        safe = {"reason": _safe_diagnostic(reason), "at": int(self.now())}
        current = self._get(task_id)
        if current is None:
            return
        if current.state == state:
            self._set_state(task_id, state, expected={state}, fields={"last_error_json": safe}, event=safe)
        else:
            self._set_state(task_id, state, expected={current.state}, fields={"last_error_json": safe}, event=safe)

    def _task(self, task_id: str) -> Any:
        task = kb.get_task(self.conn, task_id)
        if task is None:
            raise DeliveryError(f"unknown Kanban task {task_id}")
        return task

    def _project_root(self, project_path: Path, repository: str, remote_name: str) -> tuple[Path, str]:
        resolved = Path(project_path).expanduser().resolve()
        identity = self.git.validate_repository(resolved)
        root = Path(str(identity.get("root") or "")).resolve()
        if not root.is_dir():
            raise DeliveryBlocked("Git did not return an existing project root")
        remote_url = _safe_remote_url(self.git.remote_url_for(root, remote_name))
        remote_repository = _repository_from_remote(remote_url)
        if remote_repository is None:
            raise DeliveryConflict("configured Git remote URL does not identify a canonical repository")
        if remote_repository.casefold() != repository.casefold():
            raise DeliveryConflict("configured repository does not match the authoritative Git remote")
        return root, remote_url

    def start(
        self,
        task_id: str,
        *,
        project_path: Path | str,
        repository: str,
        remote_name: str = "origin",
        base_branch: str = "main",
        branch: Optional[str] = None,
        workspace_path: Optional[Path | str] = None,
        target_policy: str = "fork_only",
        merge_method: str = "squash",
        project_id: Optional[str] = None,
        stack_parent: Optional[Mapping[str, Any]] = None,
    ) -> DeliveryRecord:
        repository = normalize_repository(repository)
        base_branch = normalize_branch(base_branch, field="base_branch")
        if target_policy not in TARGET_POLICIES:
            raise ValueError("target_policy must be fork_only or fork_with_upstream_sync")
        if merge_method not in MERGE_METHODS:
            raise ValueError("merge_method must be squash, merge, or rebase")
        remote_name = str(remote_name or "").strip()
        if not _REMOTE_RE.fullmatch(remote_name):
            raise DeliveryBlocked("remote name is invalid")
        if remote_name == "upstream":
            raise DeliveryBlocked("upstream is fetch-only; feature delivery must use the fork remote")
        task = self._task(task_id)
        root, remote_url = self._project_root(Path(project_path), repository, remote_name)
        base_sha = self.git.rev_parse(root, base_branch)
        branch = normalize_branch(branch or task.branch_name or f"hermes-agent/{task_id}-delivery")
        workspace = Path(workspace_path or task.workspace_path or (root / ".worktrees" / task_id)).expanduser()
        if not workspace.is_absolute():
            raise DeliveryBlocked("delivery workspace path must be absolute")
        # Project metadata is authoritative when the task/board is scoped;
        # task workspace paths are only candidates that must match it.
        meta = kb.read_board_metadata()
        project_id = project_id or getattr(task, "project_id", None) or meta.get("project_id")
        if project_id:
            from hermes_cli import projects_db

            with projects_db.connect_closing() as projects_conn:
                project = projects_db.get_project(projects_conn, str(project_id))
            if project is None or project.archived:
                raise DeliveryConflict("delivery project is missing or archived")
            primary = project.primary_path or next(
                (folder.path for folder in project.folders if folder.is_primary),
                project.folders[0].path if project.folders else None,
            )
            if primary and Path(primary).expanduser().resolve() != root:
                raise DeliveryConflict("project path does not match the authoritative project primary repository")
            project_id = project.id
        elif meta.get("project_primary_path"):
            canonical_root = Path(str(meta["project_primary_path"])).expanduser().resolve()
            if canonical_root != root:
                raise DeliveryConflict("project path does not match the board's canonical project snapshot")

        existing = self._get(task_id)
        if existing is not None:
            immutable = {
                "project_id": existing.project_id,
                "repository": existing.repository,
                "remote_name": existing.remote_name,
                "remote_url": existing.remote_url,
                "base_branch": existing.base_branch,
                "base_sha": existing.base_sha,
                "branch": existing.branch,
                "workspace_path": existing.workspace_path,
                "project_root": existing.project_root,
                "target_policy": existing.target_policy,
                "merge_method": existing.merge_method,
            }
            requested = {
                "project_id": str(project_id or ""),
                "repository": repository,
                "remote_name": remote_name,
                "remote_url": remote_url,
                "base_branch": base_branch,
                "base_sha": base_sha,
                "branch": branch,
                "workspace_path": str(workspace),
                "project_root": str(root),
                "target_policy": target_policy,
                "merge_method": merge_method,
            }
            if immutable != requested:
                raise DeliveryConflict("delivery already exists with a different immutable identity")
            return existing

        now = int(self.now())
        initial = "upstream_sync_pending" if target_policy == "fork_with_upstream_sync" else "upstream_sync_not_required"
        with kb.write_txn(self.conn):
            self.conn.execute(
                "INSERT INTO kanban_deliveries (task_id, delivery_version, target_policy, state, project_id, repository, "
                "remote_name, remote_url, base_branch, base_sha, branch, workspace_kind, workspace_path, project_root, stack_parent_json, "
                "merge_method, upstream_sync_disposition, created_at, updated_at) "
                "VALUES (?, 1, ?, 'intake', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    target_policy,
                    str(project_id or ""),
                    repository,
                    remote_name,
                    remote_url,
                    base_branch,
                    base_sha,
                    branch,
                    "worktree" if workspace != root else task.workspace_kind,
                    str(workspace),
                    str(root),
                    _json_column(stack_parent),
                    merge_method,
                    "pending" if target_policy == "fork_with_upstream_sync" else "not_required",
                    now,
                    now,
                ),
            )
            _event(
                self.conn,
                task_id,
                "delivery_started",
                {
                    "repository": repository,
                    "remote": remote_name,
                    "base_branch": base_branch,
                    "base_sha": base_sha,
                    "branch": branch,
                    "workspace_path": str(workspace),
                    "remote_url": _safe_value(remote_url),
                    "target_policy": target_policy,
                },
            )
        self._set_state(
            task_id,
            initial,
            expected={"intake"},
            event={"target_policy": target_policy},
        )
        if initial == "upstream_sync_pending":
            return self._get(task_id)  # type: ignore[return-value]
        return self._set_state(task_id, "workspace_admitted", expected={initial}, event={"project_root": str(root)})

    def resume(self, task_id: str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        if record.state == "workspace_admitted":
            target = Path(record.workspace_path).resolve()
            if record.workspace_kind == "worktree":
                # Worktrees are intentionally outside the project root.  The
                # durable project_root is authoritative; deriving it from a
                # sibling/parent path either rejects a safe external worktree
                # or points Git at the wrong repository.
                project_root = Path(record.project_root).resolve()
                ensure = getattr(self.git, "ensure_worktree", None)
                if ensure is None:
                    raise DeliveryBlocked("Git adapter cannot materialize an isolated worktree")
                ensure(project_root, target, record.branch, record.base_branch)
                self._set_state(task_id, "worktree_ready", expected={"workspace_admitted"}, event={"workspace_path": str(target), "branch": record.branch})
            else:
                self._set_state(task_id, "worktree_ready", expected={"workspace_admitted"}, event={"workspace_path": record.workspace_path, "directory_workspace": True})
            record = self._get(task_id) or record
        if record.state == "worktree_ready":
            return self._set_state(task_id, "editing", expected={"worktree_ready"}, event={"worker may edit only the pinned workspace": True})
        return record

    def record_validation(
        self,
        task_id: str,
        *,
        commands: Sequence[str],
        passed: bool,
        tree_sha: str,
        tool_versions: Optional[Mapping[str, str]] = None,
        diagnostics: Optional[str] = None,
    ) -> DeliveryRecord:
        if not commands or any(not str(command).strip() for command in commands):
            raise ValueError("validation requires at least one command")
        tree_sha = normalize_sha(tree_sha, field="tree_sha")
        record = self._get(task_id)
        if record is None or record.state not in {"editing", "validated"}:
            raise DeliveryStateError("validation requires an admitted editing workspace")
        probe = getattr(self.git, "rev_parse", None)
        if not callable(probe):
            raise DeliveryBlocked("Git adapter cannot attest the validated tree identity")
        try:
            observed_tree = normalize_sha(probe(Path(record.workspace_path), "HEAD"), field="observed_tree_sha")
        except Exception as exc:
            raise DeliveryBlocked(f"validated tree identity is unavailable: {_safe_diagnostic(exc)}") from None
        if observed_tree != tree_sha:
            raise DeliveryConflict("validation tree identity does not match the authoritative workspace HEAD")
        snapshot = {
            "commands": [str(command)[:300] for command in commands],
            "passed": bool(passed),
            "tree_sha": tree_sha,
            "tool_versions": dict(tool_versions or {}),
            "diagnostics": _safe_diagnostic(diagnostics) if diagnostics else None,
            "checked_at": int(self.now()),
        }
        if not passed:
            self._record_error(task_id, diagnostics or "configured validation did not pass")
            raise DeliveryBlocked("configured validation is not green")
        return self._set_state(task_id, "validated", expected={"editing", "validated"}, fields={"validation_snapshot_json": snapshot}, event=snapshot)

    def commit(self, task_id: str, *, message: str, paths: Optional[Sequence[str]] = None) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        if record.state == "committed":
            return record
        if record.state != "validated":
            raise DeliveryStateError("commit requires validated delivery")
        if not paths:
            raise DeliveryBlocked("commit requires an explicit non-empty changed-file scope")
        normalized_paths: list[str] = []
        for raw_path in paths:
            value = str(raw_path).strip()
            if not value or Path(value).is_absolute() or "\x00" in value or any(part == ".." for part in Path(value).parts):
                raise DeliveryBlocked("commit scope contains an unsafe path")
            normalized_paths.append(value)
        path = Path(record.workspace_path)
        scope_sha = sha256_json(normalized_paths)
        validation_snapshot = dict(record.validation_snapshot or {})
        validation_snapshot["scope_paths"] = list(normalized_paths)
        validation_snapshot["scope_sha256"] = scope_sha
        commit_key = f"commit:{path}:{record.branch}:{sha256_json({'message': message, 'paths': normalized_paths})}"
        replay = self._begin_effect(task_id, commit_key, {"path": str(path), "branch": record.branch, "message": message, "paths": normalized_paths})
        if replay is not None:
            return self._set_state(task_id, "committed", expected={"validated", "committed"}, fields={"validation_snapshot_json": validation_snapshot, "scope_sha256": scope_sha, "commit_sha": replay.get("sha"), "commit_parent_sha": replay.get("parent_sha")}, event={"replayed": True, "scope_paths": normalized_paths, **replay})
        try:
            result = getattr(self.git, "commit")(path, message, normalized_paths)
            sha = normalize_sha(result.get("sha"), field="commit_sha")
            parent = result.get("parent_sha") or None
            if parent:
                parent = normalize_sha(parent, field="commit_parent_sha")
            result = {"sha": sha, "parent_sha": parent}
            self._finish_effect(task_id, commit_key, result)
        except Exception as exc:
            self._finish_effect(task_id, commit_key, {"diagnostic": _safe_diagnostic(exc)}, status="failed")
            self._record_error(task_id, str(exc))
            raise
        return self._set_state(task_id, "committed", expected={"validated"}, fields={"validation_snapshot_json": validation_snapshot, "scope_sha256": scope_sha, "commit_sha": sha, "commit_parent_sha": parent}, event={"scope_paths": normalized_paths, **result})

    def push(self, task_id: str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is not None and record.state == "fork_pushed":
            return record
        if record is None or record.state not in {"committed", "blocked"} or not record.commit_sha:
            raise DeliveryStateError("push requires a committed delivery")
        key = f"push:{record.repository}:{record.remote_name}:{record.branch}:{record.commit_sha}"
        request = {"repository": record.repository, "remote": record.remote_name, "branch": record.branch, "head_sha": record.commit_sha}
        effect = self._effect(task_id, key)
        if effect is not None and effect["status"] in {"started", "ambiguous"}:
            remote_head = getattr(self.git, "remote_head", None)
            if not callable(remote_head):
                raise EffectPending("push remains unresolved; Git adapter cannot read back the remote branch")
            try:
                observed = remote_head(Path(record.workspace_path), record.remote_name, record.branch)
            except Exception as exc:
                raise EffectPending(f"push remains unresolved: {_safe_diagnostic(exc)}") from None
            if observed != record.commit_sha:
                raise EffectPending("push remains unresolved; remote branch does not match the committed head")
            result = {"remote": record.remote_name, "branch": record.branch, "head_sha": observed}
            self._finish_effect(task_id, key, result)
        else:
            replay = self._begin_effect(task_id, key, request)
            if replay is not None:
                result = replay
            else:
                try:
                    result = getattr(self.git, "push")(Path(record.workspace_path), record.remote_name, record.branch, record.commit_sha)
                    self._finish_effect(task_id, key, result)
                except Exception as exc:
                    self._finish_effect(task_id, key, {"diagnostic": _safe_diagnostic(exc)}, status="ambiguous" if isinstance(exc, TimeoutError) else "failed")
                    self._record_error(task_id, str(exc), state=record.state if isinstance(exc, TimeoutError) else "blocked")
                    raise
        return self._set_state(task_id, "fork_pushed", expected={"committed", "blocked", "fork_pushed"}, event={"head_sha": record.commit_sha, "replayed": effect is not None})

    def open_pr(self, task_id: str, *, title: str, body: str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is not None and record.state == "fork_pr_open":
            return record
        if record is None or record.state != "fork_pushed":
            raise DeliveryStateError("PR creation requires a pushed delivery")
        key = f"pr-create:{record.repository}:{record.branch}:{record.base_branch}:{record.commit_sha}"
        request = {"repository": record.repository, "head": record.branch, "head_sha": record.commit_sha, "base": record.base_branch, "title": title[:200], "body": body[:10000]}
        fingerprint = sha256_json(request)
        effect = self._effect(task_id, key)
        if effect is not None and effect["status"] in {"started", "ambiguous"}:
            row = self.conn.execute(
                "SELECT request_fingerprint FROM kanban_delivery_effects WHERE task_id = ? AND effect_key = ?",
                (task_id, key),
            ).fetchone()
            if row is not None and row["request_fingerprint"] != fingerprint:
                raise DeliveryConflict("effect key was reused with a different immutable request")
            existing = self.github.find_pr(record.repository, record.branch, record.base_branch)
            if existing is None:
                raise EffectPending("PR creation remains unresolved; provider read-back found no PR")
            number = int(existing.get("number") or 0)
            replay = {"number": number}
        elif effect is not None and effect["status"] == "applied":
            replay = dict(effect["result"])
        else:
            replay = self._begin_effect(task_id, key, request)
        if replay is None:
            existing = self.github.find_pr(record.repository, record.branch, record.base_branch)
            if existing is None:
                result = self.github.create_pr(record.repository, record.branch, record.base_branch, title, body)
            else:
                result = dict(existing)
            number = int(result.get("number") or 0)
            if number <= 0:
                raise DeliveryBlocked("GitHub did not return a PR number")
            result = dict(self.github.get_pr(record.repository, number))
            _validate_pr_identity(result, record.repository, number, record.branch, record.base_branch, record.commit_sha)
            replay = {"number": number, "url": normalize_pr_url(record.repository, number, result.get("html_url") or result.get("url")), "head_sha": record.commit_sha}
            self._finish_effect(task_id, key, replay)
        replay = dict(replay)
        number = int(replay["number"])
        live = self.github.get_pr(record.repository, number)
        _validate_pr_identity(live, record.repository, number, record.branch, record.base_branch, record.commit_sha)
        if str(live.get("state") or "").casefold() != "open":
            raise DeliveryBlocked("recorded PR is not open for review")
        replay.setdefault("url", normalize_pr_url(record.repository, number, live.get("html_url") or live.get("url")))
        replay.setdefault("head_sha", record.commit_sha)
        if effect is not None and effect["status"] in {"started", "ambiguous"}:
            self._finish_effect(task_id, key, replay)
        return self._set_state(
            task_id,
            "fork_pr_open",
            expected={"fork_pushed", "fork_pr_open"},
            fields={"reviewed_repository": record.repository, "reviewed_pr_number": number, "reviewed_pr_url": replay.get("url"), "reviewed_branch": record.branch, "reviewed_head_sha": record.commit_sha, "reviewed_base_branch": record.base_branch, "reviewed_base_sha": record.base_sha},
            event={"repository": record.repository, "pr_number": number, "pr_url": replay.get("url"), "head_sha": record.commit_sha},
        )

    def request_review(self, task_id: str, *, reviewer: str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is not None and record.state == "fork_review_pending":
            return record
        if record is None or record.state not in {"fork_pr_open", "fork_review_pending"} or not record.reviewed_pr_number:
            raise DeliveryStateError("review request requires an open recorded PR")
        reviewer = str(reviewer or "").strip()
        task = self._task(task_id)
        if not reviewer or reviewer.casefold() == str(task.assignee or "").casefold():
            raise DeliveryBlocked("reviewer must be independent from the implementer")
        key = f"review-request:{record.repository}:{record.reviewed_pr_number}:{record.reviewed_head_sha}:{reviewer}"
        replay = self._begin_effect(task_id, key, {"repository": record.repository, "pr": record.reviewed_pr_number, "head_sha": record.reviewed_head_sha, "reviewer": reviewer})
        if replay is None:
            result = self.github.request_review(record.repository, int(record.reviewed_pr_number), reviewer)
            self._finish_effect(task_id, key, {"reviewer": reviewer, "provider": _safe_value(result)})
        return self._set_state(task_id, "fork_review_pending", expected={"fork_pr_open", "fork_review_pending"}, event={"reviewer": reviewer, "head_sha": record.reviewed_head_sha})

    def record_changes_requested(self, task_id: str, *, reason: str) -> DeliveryRecord:
        """Return same-card PR rework to the implementer without changing identity."""
        record = self._get(task_id)
        if record is None or record.state not in {"fork_review_pending", "editing"}:
            raise DeliveryStateError("requested changes require a pending review on the recorded PR")
        safe_reason = _safe_diagnostic(reason)
        if record.state == "editing":
            return record
        return self._set_state(
            task_id,
            "editing",
            expected={"fork_review_pending"},
            fields={
                "review_snapshot_json": None,
                "checks_snapshot_json": None,
                "scope_sha256": None,
                "merge_authorization_json": None,
                "merge_attempt_key": None,
                "last_error_json": {"reason": safe_reason, "at": int(self.now()), "kind": "requested_changes"},
            },
            event={"reason": safe_reason, "repository": record.repository, "pr_number": record.reviewed_pr_number, "head_sha": record.reviewed_head_sha},
        )

    def record_review_and_checks(self, task_id: str, packet: ReviewPacket | Mapping[str, Any]) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None or record.state not in {"fork_pr_open", "fork_review_pending", "fork_ci_green"}:
            raise DeliveryStateError("review/check evidence requires a delivery before merge authorization")
        if record.state == "fork_ci_green":
            return record
        if not isinstance(packet, ReviewPacket):
            packet = ReviewPacket.from_mapping(packet)
        if packet.repository.casefold() != record.repository.casefold() or packet.remote != record.remote_name or packet.branch != record.branch or packet.base_branch != record.base_branch or packet.base_sha != record.base_sha:
            raise DeliveryConflict("review packet repository/remote/branch/base does not match delivery identity")
        if record.commit_sha and packet.head_sha != record.commit_sha:
            raise DeliveryConflict("review packet head does not match immutable committed head")
        live = self.github.get_pr(packet.repository, packet.pr_number)
        _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
        if str(live.get("state") or "").casefold() != "open":
            raise DeliveryBlocked("review evidence must be read back from an open pull request")
        task = self._task(task_id)
        if packet.review_actor.casefold() == str(task.assignee or "").casefold():
            raise DeliveryBlocked("review packet actor must be independent from implementer")
        live_evidence = _read_live_review_checks(
            self.github,
            packet,
            implementer_actor=str(task.assignee or ""),
            model_family_provenance=self.risk_policy.get(
                "independent_model_family_provenance"
            ),
            implementer_model_family=str(
                self.risk_policy.get("implementer_model_family") or ""
            ),
        )
        snapshot = packet.as_dict()
        snapshot["live_review"] = live_evidence["review"]
        snapshot["live_checks"] = live_evidence["checks"]
        snapshot["live_branch_protection"] = live_evidence["branch_protection"]
        return self._set_state(
            task_id,
            "fork_ci_green",
            expected={record.state},
            fields={"reviewed_repository": packet.repository, "reviewed_pr_number": packet.pr_number, "reviewed_pr_url": packet.pr_url, "reviewed_branch": packet.branch, "reviewed_head_sha": packet.head_sha, "reviewed_base_branch": packet.base_branch, "reviewed_base_sha": packet.base_sha, "review_snapshot_json": snapshot, "review_actor": live_evidence["review"]["actor"], "review_at": live_evidence["review"]["reviewed_at"], "checks_snapshot_json": {**live_evidence["checks"], "branch_protection": live_evidence["branch_protection"], "live_review": live_evidence["review"]}, "scope_sha256": packet.scope_sha256 or packet.packet_hash},
            event={"packet_hash": packet.packet_hash, "repository": packet.repository, "pr_number": packet.pr_number, "head_sha": packet.head_sha, "review_actor": live_evidence["review"]["actor"], "checked_at": live_evidence["checks"]["checked_at"]},
        )

    def _risk_paths(self, record: DeliveryRecord) -> list[str]:
        snapshot = record.validation_snapshot or {}
        paths = snapshot.get("scope_paths")
        if not isinstance(paths, list):
            return []
        return [str(path) for path in paths]

    def _risk_decision(self, record: DeliveryRecord) -> RiskDecision:
        return classify_delivery_risk(
            self._risk_paths(record),
            target_policy=record.target_policy,
            policy=self.risk_policy,
        )

    def record_risk_evidence(
        self,
        task_id: str,
        *,
        actor: str,
        evidence: Mapping[str, Any],
    ) -> DeliveryRecord:
        """Persist additional automated evidence required by Tier B."""
        _reject_worker_context("record risk evidence")
        record = self._get(task_id)
        actor = str(actor or "").strip()
        if record is None or record.state != "fork_ci_green":
            raise DeliveryStateError("risk evidence requires exact-head green review state")
        if not actor or not isinstance(evidence, Mapping) or not evidence:
            raise DeliveryBlocked("risk evidence requires an attributable policy actor and evidence")
        snapshot = dict(record.checks_snapshot or {})
        existing = snapshot.get("automated_evidence")
        automated = dict(existing) if isinstance(existing, Mapping) else {}
        automated.update(_safe_value(dict(evidence)))
        automated["actor"] = actor[:200]
        automated["recorded_at"] = int(self.now())
        snapshot["automated_evidence"] = automated
        return self._set_state(
            task_id,
            "fork_ci_green",
            expected={"fork_ci_green"},
            fields={"checks_snapshot_json": snapshot},
            event={"policy_actor": actor[:200], "evidence_keys": sorted(str(key) for key in evidence)},
        )

    def _record_risk_escalation(self, task_id: str, decision: RiskDecision, reason: str) -> None:
        record = self._get(task_id)
        if record is None:
            return
        payload = {
            "reason": str(reason)[:500],
            "risk_decision": decision.as_dict(),
            "policy_identity": self.risk_policy["policy_id"],
            "recorded_at": int(self.now()),
        }
        previous = record.last_error or {}
        if (
            str(previous.get("reason") or "") == payload["reason"]
            and str(previous.get("policy_identity") or "") == payload["policy_identity"]
            and (previous.get("risk_decision") or {}).get("tier") == decision.tier
        ):
            self._emit_notification_once(
                task_id,
                notification="risk_escalation",
                payload={
                    "tier": decision.tier,
                    "reason": payload["reason"],
                    "policy_identity": payload["policy_identity"],
                },
            )
            return
        self._set_state(
            task_id,
            record.state,
            expected={record.state},
            fields={"last_error_json": payload},
            event={"risk_escalation": payload},
        )
        self._emit_notification_once(
            task_id,
            notification="risk_escalation",
            payload={
                "tier": decision.tier,
                "reason": payload["reason"],
                "policy_identity": payload["policy_identity"],
            },
        )

    def _emit_notification_once(
        self,
        task_id: str,
        *,
        notification: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Write one durable user/audit event for a controller side effect."""
        with kb.write_txn(self.conn):
            existing_rows = self.conn.execute(
                "SELECT payload FROM task_events WHERE task_id = ? AND kind = ?",
                (task_id, "delivery_notification"),
            ).fetchall()
            for row in existing_rows:
                try:
                    if json.loads(row["payload"]).get("notification") == notification:
                        return
                except (TypeError, json.JSONDecodeError):
                    continue
            _event(
                self.conn,
                task_id,
                "delivery_notification",
                {"notification": notification, **dict(payload)},
            )

    def _emit_automated_merge_notification(
        self,
        task_id: str,
        record: DeliveryRecord,
    ) -> None:
        auth = record.merge_authorization or {}
        if auth.get("mode") != "automated" or not record.review_snapshot:
            return
        packet = ReviewPacket.from_mapping(record.review_snapshot)
        decision = self._risk_decision(record)
        self._emit_notification_once(
            task_id,
            notification="tier_a_auto_merge" if decision.tier == "A" else "automated_merge",
            payload={
                "tier": decision.tier,
                "repository": record.repository,
                "pr_number": packet.pr_number,
                "head_sha": packet.head_sha,
                "merged_commit_sha": record.merged_commit_sha,
                "method": record.merge_method,
                "actor": record.merge_actor,
            },
        )

    def _rollback_failed_runtime_health(
        self,
        task_id: str,
        record: DeliveryRecord,
        health: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Rollback from the durable pack after failed staged health."""
        actions = list(record.runtime_actions or [])
        manifest: Optional[dict[str, Any]] = None
        command: Optional[Sequence[Any]] = None
        try:
            manifest = self._load_rollback_pack(record)
            restore = manifest.get("restore")
            if isinstance(restore, Mapping):
                candidate = restore.get("exact_restore_command") or restore.get("commands")
                if isinstance(candidate, list):
                    command = candidate
            rollback = getattr(self.git, "rollback_runtime", None)
            if not callable(rollback):
                raise DeliveryBlocked("Git adapter cannot execute the durable runtime rollback pack")
            rollback_result = rollback(Path(record.project_root), manifest)
            if not isinstance(rollback_result, Mapping):
                raise DeliveryBlocked("runtime rollback returned no durable result")
            status = str(rollback_result.get("status") or "").casefold()
            if status not in {"passed", "success", "ok", "healthy"}:
                raise DeliveryBlocked("runtime rollback did not verify successfully")
            action = self._runtime_action(
                action="rollback",
                command=command,
                result=rollback_result,
                recorded_at=int(self.now()),
            )
            actions.append(action)
            current = self._set_state(
                task_id,
                "blocked",
                expected={"activation_pending"},
                fields={
                    "activation_state": "rolled_back",
                    "runtime_actions_json": actions,
                    "last_error_json": {
                        "reason": "staged runtime health failed; rollback completed",
                        "health": _safe_value(dict(health)),
                        "rollback": _safe_value(dict(rollback_result)),
                        "at": int(self.now()),
                    },
                },
                event={
                    "controller_action": "runtime_rollback_completed",
                    "health": _safe_value(dict(health)),
                    "rollback": _safe_value(dict(rollback_result)),
                },
            )
            result = current.as_dict()
            result["controller_action"] = "runtime_rollback_completed"
            return result
        except Exception as exc:
            failure = {"status": "failed", "diagnostic": _safe_diagnostic(exc)}
            action = self._runtime_action(
                action="rollback",
                command=command,
                result=failure,
                recorded_at=int(self.now()),
            )
            actions.append(action)
            current = self._set_state(
                task_id,
                "blocked",
                expected={"activation_pending"},
                fields={
                    "activation_state": "rollback_failed",
                    "runtime_actions_json": actions,
                    "last_error_json": {
                        "reason": "staged runtime health failed; rollback did not complete",
                        "health": _safe_value(dict(health)),
                        "rollback": failure,
                        "at": int(self.now()),
                    },
                },
                event={
                    "controller_action": "runtime_rollback_failed",
                    "health": _safe_value(dict(health)),
                    "rollback": failure,
                },
            )
            result = current.as_dict()
            result["controller_action"] = "runtime_rollback_failed"
            return result

    def controller_once(self, task_id: str) -> dict[str, Any]:
        """Advance one durable delivery step from an external controller.

        This is intentionally not a worker/tool path: it only consumes the
        persisted delivery record and provider read-backs, and it never starts
        runtime activation.  Runtime-targeted deliveries stop with an explicit
        handoff until an independent release controller supplies the next
        evidence.
        """
        _reject_worker_context("run the external delivery controller")
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        if record.state in {"completed", "aborted"}:
            return record.as_dict()

        if record.state == "fork_ci_green":
            decision = self._risk_decision(record)
            try:
                self._automated_authorize_merge(task_id)
            except DeliveryBlocked as exc:
                current = self._get(task_id) or record
                result = current.as_dict()
                result["controller_action"] = (
                    "awaiting_tier_b_evidence" if decision.tier == "B" else "escalated"
                )
                result["controller_reason"] = _safe_diagnostic(exc)
                return result
            record = self._get(task_id)
            if record is None:
                raise DeliveryError("delivery disappeared after controller authorization")

        if record.state == "merge_authorization_pending":
            try:
                merged = self.merge(task_id)
            except DeliveryBlocked as exc:
                current = self._get(task_id) or record
                result = current.as_dict()
                result["controller_action"] = "merge_pending_readback"
                result["controller_reason"] = _safe_diagnostic(exc)
                return result
            if isinstance(merged, dict):
                return merged
            record = self._get(task_id)
            if record is None:
                raise DeliveryError("delivery disappeared after controller merge")

        if record.state == "activation_pending":
            health = record.live_identity.get("health_evidence") if record.live_identity else None
            if not isinstance(health, Mapping):
                result = record.as_dict()
                result["controller_action"] = "awaiting_staged_health"
                return result
            health_status = _runtime_health_status(health)
            if health_status == "failed":
                return self._rollback_failed_runtime_health(task_id, record, health)
            result = record.as_dict()
            result["controller_action"] = (
                "awaiting_activation_verification"
                if health_status == "healthy"
                else "awaiting_staged_health"
            )
            return result

        result = record.as_dict()
        if record.target_policy != "fork_only" and record.state in {
            "fork_merge_verified",
            "runtime_cutover_pending",
            "rollback_pack_ready",
            "runtime_materialized",
            "activation_pending",
        }:
            result["controller_action"] = "awaiting_external_runtime_cutover"
        elif record.state == "fork_merge_verified":
            result["controller_action"] = "awaiting_cleanup"
        else:
            result["controller_action"] = "awaiting_next_evidence"
        return result

    def _automated_authorize_merge(self, task_id: str) -> dict[str, Any]:
        _reject_worker_context("automatically authorize a merge")
        record = self._get(task_id)
        if record is None or record.state != "fork_ci_green" or not record.review_snapshot:
            raise DeliveryBlocked("automated merge requires exact-head green review evidence")
        if self.risk_policy["mode"] != "tiered" or not self.risk_policy["auto_merge"]:
            raise DeliveryBlocked("merge authorization required by the configured policy")
        decision = self._risk_decision(record)
        if decision.tier == "C":
            self._record_risk_escalation(task_id, decision, decision.reason)
            raise DeliveryBlocked("risk policy requires attributable human authorization")
        packet = ReviewPacket.from_mapping(record.review_snapshot)
        implementer_actor = self.risk_policy["implementer_actor"]
        if not implementer_actor:
            task_row = self.conn.execute("SELECT assignee FROM tasks WHERE id = ?", (task_id,)).fetchone()
            implementer_actor = str(task_row["assignee"] or "").strip() if task_row is not None else ""
        live_evidence = _read_live_review_checks(
            self.github,
            packet,
            implementer_actor=implementer_actor,
            model_family_provenance=self.risk_policy.get(
                "independent_model_family_provenance"
            ),
            implementer_model_family=str(
                self.risk_policy.get("implementer_model_family") or ""
            ),
        )
        checks = live_evidence["checks"]
        review = live_evidence["review"]
        branch_protection = live_evidence["branch_protection"]
        missing: list[str] = []
        if self.risk_policy["branch_protection_required"] and branch_protection.get("enabled") is not True:
            missing.append("branch_protection")
        if self.risk_policy["require_independent_model_family"]:
            reviewed_family = str(review.get("model_family") or "").strip()
            implementer_family = self.risk_policy["implementer_model_family"]
            if not reviewed_family or reviewed_family.casefold() == implementer_family.casefold():
                missing.append("independent_model_family")
        if implementer_actor and str(review.get("actor") or "").strip().casefold() == implementer_actor.casefold():
            missing.append("independent_reviewer")
        evidence = dict(record.checks_snapshot or {})
        automated_evidence = evidence.get("automated_evidence") if isinstance(evidence, Mapping) else None
        automated_evidence = dict(automated_evidence) if isinstance(automated_evidence, Mapping) else {}
        for required in decision.required_evidence:
            value = automated_evidence.get(required)
            if not value:
                missing.append(required)
                continue
            if isinstance(value, Mapping) and "status" in value:
                allowed_statuses = {"passed", "success", "green"}
                if required == "rollback_artifact":
                    allowed_statuses.add("ready")
                if str(value.get("status")).casefold() not in allowed_statuses:
                    missing.append(required)
        if missing:
            reason = "automated evidence is incomplete: " + ", ".join(sorted(set(missing)))
            self._record_risk_escalation(task_id, decision, reason)
            raise DeliveryBlocked(f"Tier {decision.tier} merge requires additional evidence: {', '.join(sorted(set(missing)))}")
        live = self.github.get_pr(record.repository, packet.pr_number)
        _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
        if str(live.get("state") or "").casefold() != "open" or live.get("draft") is not False:
            raise DeliveryBlocked("pull request is not open and non-draft at automated merge read-back")
        rollback = automated_evidence.get("rollback_artifact")
        if not isinstance(rollback, Mapping):
            rollback = {
                "kind": "git-parent",
                "repository": record.repository,
                "branch": record.branch,
                "source_sha": record.commit_parent_sha,
                "head_sha": record.commit_sha,
                "scope_sha256": record.scope_sha256,
            }
        now = int(self.now())
        auth = {
            "authorization_event_id": "auto_" + secrets_token(),
            "mode": "automated",
            "tier": decision.tier,
            "policy_id": self.risk_policy["policy_id"],
            "policy_identity": "config",
            "source": "risk_policy",
            "authenticated_actor": "hermes-policy",
            "target": "fork",
            "repository": record.repository,
            "pr_number": record.reviewed_pr_number,
            "pr_url": record.reviewed_pr_url,
            "branch": record.reviewed_branch,
            "base_branch": record.reviewed_base_branch,
            "base_sha": record.reviewed_base_sha,
            "head_sha": record.reviewed_head_sha,
            "method": record.merge_method,
            "packet_hash": packet.packet_hash,
            "classifier_inputs": decision.classifier_inputs,
            "protected_path_rules": list(decision.protected_path_rules),
            "automated_evidence": automated_evidence,
            "rollback_artifact": _safe_value(dict(rollback)),
            "reason": decision.reason,
            "confirmed": True,
            "created_at": now,
            "expires_at": now + 3600,
        }
        evidence.update({"head_sha": packet.head_sha, **checks, "branch_protection": branch_protection, "live_review": review, "automated_evidence": automated_evidence})
        self._set_state(
            task_id,
            "merge_authorization_pending",
            expected={"fork_ci_green"},
            fields={"merge_authorization_json": auth, "merge_attempt_key": f"merge:{record.repository}:{record.reviewed_pr_number}:{record.reviewed_head_sha}:{record.merge_method}", "checks_snapshot_json": evidence},
            event={"mode": "automated", "tier": decision.tier, "policy_id": self.risk_policy["policy_id"], "packet_hash": packet.packet_hash},
        )
        return auth

    def authorize_merge(
        self,
        task_id: str,
        *,
        actor: str,
        source: str,
        packet_hash: str,
        method: str,
        reason: str,
        confirmation: bool,
        expires_at: Optional[int] = None,
    ) -> dict[str, Any]:
        _reject_worker_context("authorize a merge")
        record = self._get(task_id)
        if record is None or record.state != "fork_ci_green" or not record.review_snapshot:
            raise DeliveryBlocked("merge authorization requires exact-head green review evidence")
        if source not in {"operator_cli", "approved_controller"}:
            raise DeliveryBlocked("merge authorization source is not an approved human/controller boundary")
        actor = str(actor or "").strip()
        if not actor or not confirmation:
            raise DeliveryBlocked("merge authorization requires an attributable actor and explicit confirmation")
        identity_probe = getattr(self.github, "current_user", None)
        if not callable(identity_probe):
            raise DeliveryBlocked("merge authorization requires an authenticated provider identity")
        try:
            authenticated_actor = str(identity_probe() or "").strip()
        except Exception as exc:
            raise DeliveryBlocked(f"authenticated provider identity is unavailable: {_safe_diagnostic(exc)}") from None
        if not authenticated_actor or authenticated_actor.casefold() != actor.casefold():
            raise DeliveryBlocked("authorization actor does not match authenticated provider identity")
        if method not in MERGE_METHODS:
            raise ValueError("merge method must be squash, merge, or rebase")
        if method != record.merge_method:
            raise DeliveryConflict("authorization method differs from configured delivery method")
        packet = ReviewPacket.from_mapping(record.review_snapshot)
        if packet_hash != packet.packet_hash:
            raise DeliveryConflict("authorization packet hash does not match the current immutable packet")
        task = self._task(task_id)
        live_evidence = _read_live_review_checks(
            self.github,
            packet,
            implementer_actor=str(task.assignee or ""),
            model_family_provenance=self.risk_policy.get(
                "independent_model_family_provenance"
            ),
            implementer_model_family=str(
                self.risk_policy.get("implementer_model_family") or ""
            ),
        )
        if (
            record.state == "merge_authorization_pending"
            and record.merge_authorization
            and record.merge_authorization.get("packet_hash") == packet_hash
            and record.merge_authorization.get("method") == method
        ):
            return record.merge_authorization
        now = int(self.now())
        expiry = int(expires_at) if expires_at is not None else now + 3600
        if expiry <= now:
            raise DeliveryBlocked("merge authorization is already expired")
        auth = {
            "authorization_event_id": "auth_" + secrets_token(),
            "authenticated_actor": actor,
            "source": source,
            "risk_decision": self._risk_decision(record).as_dict(),
            "target": "fork",
            "repository": record.repository,
            "pr_number": record.reviewed_pr_number,
            "pr_url": record.reviewed_pr_url,
            "branch": record.reviewed_branch,
            "base_branch": record.reviewed_base_branch,
            "base_sha": record.reviewed_base_sha,
            "head_sha": record.reviewed_head_sha,
            "method": method,
            "packet_hash": packet_hash,
            "reason": str(reason or "")[:500],
            "confirmed": True,
            "created_at": now,
            "expires_at": expiry,
        }
        evidence = dict(record.checks_snapshot or {})
        evidence.update(
            {
                "head_sha": packet.head_sha,
                "checks": live_evidence["checks"],
                "branch_protection": live_evidence["branch_protection"],
                "live_review": live_evidence["review"],
            }
        )
        self._set_state(
            task_id,
            "merge_authorization_pending",
            expected={"fork_ci_green", "merge_authorization_pending"},
            fields={
                "merge_authorization_json": auth,
                "merge_attempt_key": f"merge:{record.repository}:{record.reviewed_pr_number}:{record.reviewed_head_sha}:{method}",
                "checks_snapshot_json": evidence,
            },
            event={
                "authorization_event_id": auth["authorization_event_id"],
                "actor": actor,
                "source": source,
                "packet_hash": packet_hash,
                "method": method,
                "expires_at": expiry,
                "live_head_sha": packet.head_sha,
            },
        )
        return auth

    def merge(self, task_id: str) -> dict[str, Any]:
        _reject_worker_context("merge")
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        if record.state in {"fork_merge_verified", "completed"} and record.merged_commit_sha:
            self._emit_automated_merge_notification(task_id, record)
            return record.as_dict()
        if record.state == "fork_ci_green":
            self._automated_authorize_merge(task_id)
            record = self._get(task_id)
            if record is None:
                raise DeliveryError("delivery disappeared after automated authorization")
        if record.state != "merge_authorization_pending" or not record.merge_authorization:
            raise DeliveryBlocked("merge requires a durable exact-head authorization")
        auth = record.merge_authorization
        now = int(self.now())
        if int(auth.get("expires_at") or 0) <= now:
            raise DeliveryBlocked("merge authorization has expired")
        packet = ReviewPacket.from_mapping(record.review_snapshot or {})
        if auth.get("packet_hash") != packet.packet_hash:
            raise DeliveryConflict("merge authorization no longer matches the review packet")
        key = record.merge_attempt_key or f"merge:{record.repository}:{packet.pr_number}:{packet.head_sha}:{record.merge_method}"
        request = {"repository": record.repository, "pr": packet.pr_number, "head_sha": packet.head_sha, "method": record.merge_method}
        effect = self._effect(task_id, key)
        replay: Optional[dict[str, Any]] = None
        if effect is not None and effect["status"] in {"started", "ambiguous"}:
            # A prior process may have reached GitHub and died before marking
            # the effect applied. Read back first; never issue a second merge.
            read_back = dict(self.github.get_pr(record.repository, packet.pr_number))
            _validate_pr_identity(read_back, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
            merged_sha = str(read_back.get("merge_commit_sha") or "").lower()
            if _normalized_pr_state(read_back) != "merged" or not _SHA_RE.fullmatch(merged_sha):
                raise EffectPending("merge effect is unresolved; provider read-back is not merged")
            replay = {
                "merged_commit_sha": merged_sha,
                "actor": str(auth.get("authenticated_actor") or "")[:200],
                "merged_at": now,
                **request,
            }
            self._finish_effect(task_id, key, replay)
        elif effect is not None and effect["status"] == "applied":
            replay = dict(effect["result"])
        else:
            live = self.github.get_pr(record.repository, packet.pr_number)
            _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
            if str(live.get("state") or "").casefold() != "open" or live.get("draft") is not False:
                raise DeliveryBlocked("pull request is not open and non-draft at merge read-back")
            replay = self._begin_effect(task_id, key, request)
        if replay is None:
            try:
                response = dict(self.github.merge_pr(record.repository, packet.pr_number, str(record.merge_method), packet.head_sha))
                merged = response.get("merged") is True
                if not merged:
                    self._finish_effect(task_id, key, {"diagnostic": "provider did not confirm merge", "response": _safe_value(response)}, status="failed")
                    raise DeliveryBlocked("GitHub did not confirm the merge")
                read_back = dict(self.github.get_pr(record.repository, packet.pr_number))
                _validate_pr_identity(read_back, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
                merged_state = _normalized_pr_state(read_back)
                merged_sha = str(read_back.get("merge_commit_sha") or "").lower()
                if merged_state != "merged" or not _SHA_RE.fullmatch(merged_sha):
                    self._finish_effect(task_id, key, {"diagnostic": "merge result was not confirmed by provider read-back"}, status="ambiguous")
                    raise EffectPending("merge response is ambiguous; provider read-back is not merged")
                replay = {"merged_commit_sha": merged_sha, "actor": str(response.get("actor") or auth.get("authenticated_actor") or "")[:200], "merged_at": now, **request}
                self._finish_effect(task_id, key, replay)
            except Exception:
                if replay is None and (self._effect(task_id, key) or {}).get("status") == "started":
                    # Do not mark a provider timeout as applied. A later resume
                    # must perform a read-back before attempting another merge.
                    try:
                        self._finish_effect(task_id, key, {"diagnostic": "merge provider result unresolved"}, status="ambiguous")
                    except Exception:
                        pass
                raise
        result = dict(replay)
        self._set_state(task_id, "fork_merge_verified", expected={"merge_authorization_pending", "fork_merge_verified"}, fields={"merged_repository": record.repository, "merged_pr_number": packet.pr_number, "merged_commit_sha": result.get("merged_commit_sha"), "merge_actor": result.get("actor"), "merged_at": result.get("merged_at")}, event={"repository": record.repository, "pr_number": packet.pr_number, "reviewed_head_sha": packet.head_sha, "merged_commit_sha": result.get("merged_commit_sha"), "actor": result.get("actor"), "method": record.merge_method})
        if auth.get("mode") == "automated":
            self._emit_automated_merge_notification(task_id, self._get(task_id) or record)
        if auth.get("mode") == "automated" and self.risk_policy["auto_cleanup"] and record.target_policy == "fork_only":
            return self.cleanup(task_id, delete_remote_branch=True, remove_worktree=False).as_dict()
        return self._get(task_id).as_dict()  # type: ignore[union-attr]

    def cleanup(self, task_id: str, *, delete_remote_branch: bool = False, remove_worktree: bool = False) -> DeliveryRecord:
        record = self._get(task_id)
        if record is not None and record.state == "completed":
            return record
        if record is None or record.state != "fork_merge_verified":
            raise DeliveryStateError("cleanup requires provider-confirmed fork merge")
        if remove_worktree:
            task = self._task(task_id)
            if task.claim_lock and (task.claim_expires is None or int(task.claim_expires) > int(self.now())):
                raise DeliveryBlocked("cannot remove a worktree while the task claim is live")
        if delete_remote_branch:
            key = f"branch-delete:{record.repository}:{record.branch}:{record.merged_commit_sha}"
            replay = self._begin_effect(task_id, key, {"repository": record.repository, "branch": record.branch, "merged_commit_sha": record.merged_commit_sha})
            if replay is None:
                result = self.github.delete_branch(record.repository, record.branch)
                self._finish_effect(task_id, key, {"deleted": True, "provider": _safe_value(result)})
        if remove_worktree:
            path = Path(record.workspace_path)
            if path.exists() and path.name != record.task_id:
                raise DeliveryBlocked("refusing to remove a workspace that is not the canonical delivery worktree")
            if path.exists():
                repository = Path(record.project_root).resolve()
                if getattr(self.git, "remove_worktree", None) is None:
                    raise DeliveryBlocked("Git adapter cannot safely remove delivery worktree")
                getattr(self.git, "remove_worktree")(repository, path)
        if record.target_policy == "fork_only":
            return self._set_state(task_id, "completed", expected={"fork_merge_verified"}, event={"remote_branch_cleanup": bool(delete_remote_branch), "worktree_cleanup": bool(remove_worktree), "target_policy": record.target_policy})
        return self._set_state(task_id, "runtime_cutover_pending", expected={"fork_merge_verified"}, fields={"activation_state": "not_started"}, event={"target_policy": record.target_policy})

    def sync_upstream(self, task_id: str, *, source: str = "upstream/main") -> DeliveryRecord:
        record = self._get(task_id)
        if record is None or record.target_policy != "fork_with_upstream_sync" or record.state != "upstream_sync_pending":
            raise DeliveryStateError("upstream sync requires a fork_with_upstream_sync delivery in pending state")
        if ":" in source:
            remote, ref = source.split(":", 1)
        elif "/" in source:
            remote, ref = source.split("/", 1)
        else:
            remote, ref = "upstream", source
        if remote != "upstream":
            raise DeliveryBlocked("upstream sync source must use the fetch-only upstream remote")
        ref = normalize_branch(ref, field="upstream source ref")
        key = f"upstream-fetch:{remote}:{ref}"
        replay = self._begin_effect(task_id, key, {"remote": remote, "ref": ref})
        if replay is None:
            result = getattr(self.git, "fetch")(Path(record.project_root), remote, ref)
            self._finish_effect(task_id, key, result)
        else:
            result = replay
        source_sha = normalize_sha(result.get("sha"), field="upstream_source_sha")
        snapshot = {"repository": record.repository, "remote": remote, "ref": ref, "source_sha": source_sha, "transport": result.get("transport", "git-fetch"), "fetched_at": int(self.now()), "disposition": "pending"}
        if source_sha == record.base_sha:
            snapshot["disposition"] = "synced"
            self._set_state(
                task_id,
                "upstream_sync_verified",
                expected={"upstream_sync_pending"},
                fields={"upstream_sync_json": snapshot, "upstream_source_sha": source_sha, "upstream_sync_disposition": "synced"},
                event=snapshot,
            )
            return self._set_state(task_id, "workspace_admitted", expected={"upstream_sync_verified"}, event={"upstream_sync": "already_at_configured_base"})
        return self._set_state(task_id, "upstream_sync_review_pending", expected={"upstream_sync_pending"}, fields={"upstream_sync_json": snapshot, "upstream_source_sha": source_sha}, event=snapshot)

    def record_upstream_sync_review_and_checks(self, task_id: str, packet: ReviewPacket | Mapping[str, Any]) -> DeliveryRecord:
        record = self._get(task_id)
        if record is not None and record.state == "upstream_sync_ci_green":
            return record
        if record is None or record.state != "upstream_sync_review_pending":
            raise DeliveryStateError("upstream sync evidence requires a pending fork-local synchronization review")
        if not isinstance(packet, ReviewPacket):
            packet = ReviewPacket.from_mapping(packet)
        if packet.provider != "github" or packet.repository.casefold() != record.repository.casefold() or packet.remote != record.remote_name:
            raise DeliveryConflict("upstream sync packet provider/repository/remote does not match delivery identity")
        if packet.base_branch != record.base_branch or packet.base_sha != record.base_sha:
            raise DeliveryConflict("upstream sync packet base does not match the configured fork base")
        if packet.branch == record.branch:
            raise DeliveryConflict("upstream synchronization must use a separate fork-local sync branch")
        live = self.github.get_pr(packet.repository, packet.pr_number)
        _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
        if str(live.get("state") or "").casefold() != "open":
            raise DeliveryBlocked("upstream sync evidence must name an open fork-local PR")
        task = self._task(task_id)
        if packet.review_actor.casefold() == str(task.assignee or "").casefold():
            raise DeliveryBlocked("upstream sync review actor must be independent from implementer")
        live_evidence = _read_live_review_checks(
            self.github,
            packet,
            implementer_actor=str(task.assignee or ""),
            model_family_provenance=self.risk_policy.get(
                "independent_model_family_provenance"
            ),
            implementer_model_family=str(
                self.risk_policy.get("implementer_model_family") or ""
            ),
        )
        live_snapshot = packet.as_dict()
        live_snapshot["live_review"] = live_evidence["review"]
        live_snapshot["live_checks"] = live_evidence["checks"]
        live_snapshot["live_branch_protection"] = live_evidence["branch_protection"]
        upstream = dict(record.upstream_sync or {})
        upstream.update({
            "sync_pr": {"repository": packet.repository, "number": packet.pr_number, "url": packet.pr_url, "branch": packet.branch, "head_sha": packet.head_sha, "base_branch": packet.base_branch, "base_sha": packet.base_sha},
            "review_snapshot": live_snapshot,
            "packet_hash": packet.packet_hash,
            "disposition": "pending",
        })
        return self._set_state(
            task_id,
            "upstream_sync_ci_green",
            expected={"upstream_sync_review_pending"},
            fields={"upstream_sync_json": upstream, "upstream_sync_disposition": "pending"},
            event={"packet_hash": packet.packet_hash, "repository": packet.repository, "pr_number": packet.pr_number, "head_sha": packet.head_sha, "review_actor": packet.review_actor},
        )

    def authorize_upstream_sync(
        self,
        task_id: str,
        *,
        actor: str,
        source: str,
        packet_hash: str,
        method: str,
        confirmation: bool,
        expires_at: Optional[int] = None,
    ) -> dict[str, Any]:
        _reject_worker_context("authorize upstream synchronization")
        record = self._get(task_id)
        if record is None or record.state not in {"upstream_sync_ci_green", "upstream_sync_authorization_pending"} or not record.upstream_sync:
            raise DeliveryBlocked("upstream synchronization authorization requires exact-head green fork review evidence")
        if source not in {"operator_cli", "approved_controller"} or not confirmation:
            raise DeliveryBlocked("upstream synchronization requires an explicit external authorization")
        if method not in MERGE_METHODS or method != record.merge_method:
            raise DeliveryConflict("upstream synchronization authorization method differs from configured delivery method")
        snapshot = record.upstream_sync.get("review_snapshot")
        packet = ReviewPacket.from_mapping(snapshot or {})
        if packet_hash != packet.packet_hash or packet_hash != record.upstream_sync.get("packet_hash"):
            raise DeliveryConflict("upstream synchronization authorization packet hash is stale")
        actor = str(actor or "").strip()
        if not actor:
            raise DeliveryBlocked("upstream synchronization authorization requires an attributable actor")
        identity_probe = getattr(self.github, "current_user", None)
        if not callable(identity_probe):
            raise DeliveryBlocked("upstream synchronization authorization requires an authenticated provider identity")
        try:
            authenticated_actor = str(identity_probe() or "").strip()
        except Exception as exc:
            raise DeliveryBlocked(f"authenticated provider identity is unavailable: {_safe_diagnostic(exc)}") from None
        if not authenticated_actor or authenticated_actor.casefold() != actor.casefold():
            raise DeliveryBlocked("upstream synchronization authorization actor does not match provider identity")
        now = int(self.now())
        expiry = int(expires_at) if expires_at is not None else now + 3600
        if expiry <= now:
            raise DeliveryBlocked("upstream synchronization authorization is already expired")
        auth = {"authorization_event_id": "upstream_" + secrets_token(), "authenticated_actor": actor, "source": source, "target": "fork_upstream_sync", "repository": record.repository, "pr_number": packet.pr_number, "pr_url": packet.pr_url, "branch": packet.branch, "base_branch": packet.base_branch, "base_sha": packet.base_sha, "head_sha": packet.head_sha, "method": method, "packet_hash": packet_hash, "confirmed": True, "created_at": now, "expires_at": expiry}
        upstream = dict(record.upstream_sync)
        upstream["authorization"] = auth
        self._set_state(task_id, "upstream_sync_authorization_pending", expected={"upstream_sync_ci_green", "upstream_sync_authorization_pending"}, fields={"upstream_sync_json": upstream}, event={"authorization_event_id": auth["authorization_event_id"], "actor": actor, "packet_hash": packet_hash, "expires_at": expiry})
        return auth

    def merge_upstream_sync(self, task_id: str) -> DeliveryRecord:
        _reject_worker_context("merge upstream synchronization")
        record = self._get(task_id)
        if record is None or record.state != "upstream_sync_authorization_pending" or not record.upstream_sync:
            raise DeliveryBlocked("upstream synchronization merge requires durable authorization")
        upstream = dict(record.upstream_sync)
        packet = ReviewPacket.from_mapping(upstream.get("review_snapshot") or {})
        auth_value = upstream.get("authorization")
        auth: Mapping[str, Any] = auth_value if isinstance(auth_value, Mapping) else {}
        if int(auth.get("expires_at") or 0) <= int(self.now()):
            raise DeliveryBlocked("upstream synchronization authorization has expired")
        live = self.github.get_pr(packet.repository, packet.pr_number)
        _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
        key = f"upstream-sync-merge:{packet.repository}:{packet.pr_number}:{packet.head_sha}:{auth.get('method')}"
        request = {"repository": packet.repository, "pr": packet.pr_number, "branch": packet.branch, "base": packet.base_branch, "head_sha": packet.head_sha, "method": auth.get("method")}
        effect = self._effect(task_id, key)
        if effect is not None and effect["status"] in {"started", "ambiguous"}:
            if str(live.get("state") or "").casefold() != "merged":
                raise EffectPending("upstream synchronization merge remains unresolved; provider read-back is not merged")
            result = dict(effect.get("result") or {})
        elif effect is not None and effect["status"] == "applied":
            result = dict(effect.get("result") or {})
        else:
            replay = self._begin_effect(task_id, key, request)
            if replay is not None:
                result = replay
            else:
                response = self.github.merge_pr(packet.repository, packet.pr_number, str(auth.get("method")), packet.head_sha)
                if response.get("merged") is not True:
                    self._finish_effect(task_id, key, {"diagnostic": _safe_diagnostic(response)}, status="failed")
                    raise DeliveryBlocked("provider did not confirm upstream synchronization merge")
                live = self.github.get_pr(packet.repository, packet.pr_number)
                _validate_pr_identity(live, packet.repository, packet.pr_number, packet.branch, packet.base_branch, packet.head_sha)
                if str(live.get("state") or "").casefold() != "merged":
                    self._finish_effect(task_id, key, {"diagnostic": "merge read-back is not merged"}, status="ambiguous")
                    raise EffectPending("upstream synchronization merge read-back is unresolved")
                merged_sha = normalize_sha(live.get("merge_commit_sha") or response.get("sha"), field="upstream_sync_merge_sha")
                result = {"merged": True, "sha": merged_sha, "pr_number": packet.pr_number}
                self._finish_effect(task_id, key, result)
        merged_sha = normalize_sha(result.get("sha") or live.get("merge_commit_sha"), field="upstream_sync_merge_sha")
        upstream["disposition"] = "synced"
        upstream["merged"] = {"repository": packet.repository, "pr_number": packet.pr_number, "head_sha": packet.head_sha, "merged_commit_sha": merged_sha, "merged_at": int(self.now())}
        self._set_state(task_id, "upstream_sync_verified", expected={"upstream_sync_authorization_pending"}, fields={"upstream_sync_json": upstream, "upstream_sync_disposition": "synced", "base_sha": merged_sha}, event=upstream["merged"])
        return self._set_state(task_id, "workspace_admitted", expected={"upstream_sync_verified"}, event={"upstream_sync": "verified"})

    def authorize_cutover(self, task_id: str, *, actor: str, source: str, runtime_remote: str, runtime_branch: str, approved_merge_sha: str, confirmation: bool) -> dict[str, Any]:
        record = self._get(task_id)
        if record is None or record.state not in {"fork_merge_verified", "runtime_cutover_pending"}:
            raise DeliveryBlocked("cutover authorization requires a verified fork merge")
        if os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("HERMES_DELEGATED_CHILD_CONTEXT"):
            raise DeliveryBlocked("gateway/delegated workers cannot authorize runtime cutover")
        if source not in {"operator_cli", "approved_controller"} or not confirmation:
            raise DeliveryBlocked("cutover requires an explicit external release authorization")
        approved_merge_sha = normalize_sha(approved_merge_sha, field="approved_merge_sha")
        if approved_merge_sha != record.merged_commit_sha:
            raise DeliveryConflict("cutover authorization does not name the recorded merged commit")
        auth = {"authorization_event_id": "release_" + secrets_token(), "actor": str(actor or "")[:200], "source": source, "runtime_remote": str(runtime_remote)[:200], "runtime_branch": normalize_branch(runtime_branch, field="runtime_branch"), "approved_merge_sha": approved_merge_sha, "confirmed": True, "created_at": int(self.now())}
        self._set_state(task_id, "runtime_cutover_pending", expected={"fork_merge_verified", "runtime_cutover_pending"}, fields={"runtime_remote": auth["runtime_remote"], "runtime_branch": auth["runtime_branch"], "release_authorization_json": auth, "activation_state": "pending"}, event=auth)
        return auth

    def prepare_cutover(self, task_id: str, *, output_dir: Path | str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None or record.state != "runtime_cutover_pending" or not record.release_authorization:
            raise DeliveryBlocked("rollback pack requires external cutover authorization")
        if os.environ.get("HERMES_KANBAN_TASK"):
            raise DeliveryBlocked("gateway-hosted workers cannot prepare or activate a runtime cutover")
        output = Path(output_dir).expanduser()
        if not output.is_absolute():
            raise DeliveryBlocked("rollback pack output must be an absolute path")
        output.mkdir(parents=True, exist_ok=True)
        root = Path(record.project_root or record.workspace_path).resolve()
        if not root.is_dir():
            raise DeliveryBlocked("runtime project root is not an existing directory")

        status_probe = getattr(self.git, "status_porcelain", None)
        branch_probe = getattr(self.git, "branch_name", None)
        remote_probe = getattr(self.git, "remote_url_for", None)
        if callable(status_probe):
            status = str(status_probe(root) or "")
            before_sha = normalize_sha(
                self.git.rev_parse(root, "HEAD"), field="runtime_before_sha"
            )
            inventory = _git_status_inventory(status)
        else:
            # Minimal test/dry-run adapters do not expose live inventory.  The
            # durable base identity is still safer than inventing a checkout.
            before_sha = normalize_sha(record.base_sha, field="runtime_before_sha")
            inventory = {"dirty_paths": [], "untracked_paths": []}
        actual_branch = ""
        if callable(branch_probe):
            actual_branch = str(branch_probe(root) or "").strip()
        runtime_branch = str(record.runtime_branch or actual_branch or "").strip()
        if actual_branch and runtime_branch and actual_branch != runtime_branch:
            raise DeliveryConflict("runtime checkout branch does not match cutover authorization")
        runtime_remote_url = ""
        if callable(remote_probe) and record.runtime_remote:
            runtime_remote_url = _safe_remote_url(
                remote_probe(root, record.runtime_remote)
            )
            remote_repository = _repository_from_remote(runtime_remote_url)
            if remote_repository and remote_repository.casefold() != record.repository.casefold():
                raise DeliveryConflict("runtime remote does not match delivery repository")

        restore_commands = [
            ["git", "-C", str(root), "reset", "--hard", before_sha],
            ["git", "-C", str(root), "clean", "-fd"],
        ]
        identity = {
            "path": str(root),
            "repository": record.repository,
            "remote": record.runtime_remote,
            "remote_url": runtime_remote_url or None,
            "branch": runtime_branch or None,
            "before_sha": before_sha,
        }
        manifest = {
            "delivery": {
                "task_id": task_id,
                "repository": record.repository,
                "branch": record.branch,
                "merged_commit_sha": record.merged_commit_sha,
                "target_policy": record.target_policy,
            },
            "runtime": {
                "path": str(root),
                "remote": record.runtime_remote,
                "branch": runtime_branch or None,
                "before_sha": before_sha,
                "after_sha": None,
                "identity": identity,
            },
            "inventory": inventory,
            "restore": {
                "commands": restore_commands,
                "exact_restore_command": restore_commands,
                "working_directory": str(root),
                "strategy": "reset_and_clean",
            },
            # Kept as a compatibility alias for older operators that called
            # this field checkout rather than runtime.
            "checkout": str(root),
            "created_at": int(self.now()),
        }
        manifest_path = output / "manifest.json"
        manifest_path.write_text(safe_json(manifest) + "\n", encoding="utf-8")
        pack_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        return self._set_state(
            task_id,
            "rollback_pack_ready",
            expected={"runtime_cutover_pending"},
            fields={
                "runtime_before_sha": before_sha,
                "rollback_pack_path": str(manifest_path),
                "rollback_pack_sha256": pack_sha,
                "rollback_manifest_json": manifest,
                "activation_state": "pending",
            },
            event={
                "rollback_pack_path": str(manifest_path),
                "rollback_pack_sha256": pack_sha,
                "runtime_identity": identity,
                "inventory": inventory,
            },
        )

    def _load_rollback_pack(self, record: DeliveryRecord) -> dict[str, Any]:
        path = Path(str(record.rollback_pack_path or "")).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise DeliveryBlocked("durable rollback pack is missing")
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if record.rollback_pack_sha256 and actual_sha != record.rollback_pack_sha256:
            raise DeliveryConflict("durable rollback pack hash does not match the delivery record")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise DeliveryBlocked("durable rollback pack is unreadable") from None
        if not isinstance(payload, Mapping):
            raise DeliveryBlocked("durable rollback pack must contain an object")
        delivery = payload.get("delivery")
        if not isinstance(delivery, Mapping) or str(delivery.get("task_id") or "") != record.task_id:
            raise DeliveryConflict("rollback pack task identity does not match the delivery record")
        if str(delivery.get("repository") or "").casefold() != record.repository.casefold():
            raise DeliveryConflict("rollback pack repository does not match the delivery record")
        return dict(payload)

    def _persist_rollback_pack(
        self, record: DeliveryRecord, manifest: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        path = Path(str(record.rollback_pack_path or "")).expanduser()
        if not path.is_absolute():
            raise DeliveryBlocked("durable rollback pack path must be absolute")
        payload = dict(manifest)
        path.write_text(safe_json(payload) + "\n", encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest(), payload

    @staticmethod
    def _runtime_action(
        *,
        action: str,
        command: Optional[Sequence[Any]],
        result: Mapping[str, Any],
        recorded_at: int,
    ) -> dict[str, Any]:
        if not action or not isinstance(result, Mapping):
            raise DeliveryBlocked("runtime action requires an action name and result object")
        normalized_command = None
        if command is not None:
            if isinstance(command, (str, bytes)):
                raise DeliveryBlocked("runtime action commands must be an argv list")
            if any(isinstance(part, (list, tuple)) for part in command):
                normalized_command = [
                    [str(part)[:300] for part in argv]
                    for argv in command
                    if isinstance(argv, (list, tuple)) and argv
                ]
            else:
                if not all(str(part).strip() for part in command):
                    raise DeliveryBlocked("runtime action commands must be a non-empty argv list")
                normalized_command = [str(part)[:300] for part in command]
            if not normalized_command:
                raise DeliveryBlocked("runtime action commands must be a non-empty argv list")
        return {
            "action": str(action)[:100],
            "command": normalized_command,
            "result": _safe_value(dict(result)),
            "recorded_at": int(recorded_at),
        }

    def record_runtime_materialized(
        self,
        task_id: str,
        *,
        before_sha: str,
        after_sha: str,
        main_pid: int,
        service_interpreter: str,
        restart_command: Optional[Sequence[str]] = None,
        restart_result: Optional[Mapping[str, Any]] = None,
    ) -> DeliveryRecord:
        """Record an external controller's materialization handoff.

        This method does not restart, reload, or mutate the runtime. It only
        accepts evidence from the separately authorized controller, advances
        two explicit states, and leaves live health verification to
        :meth:`verify_cutover`.
        """
        record = self._get(task_id)
        if record is None or record.state not in {"rollback_pack_ready", "runtime_materialized", "activation_pending"}:
            raise DeliveryStateError("runtime materialization requires a prepared rollback pack")
        if os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("HERMES_DELEGATED_CHILD_CONTEXT"):
            raise DeliveryBlocked("gateway/delegated workers cannot attest runtime materialization")
        before_sha = normalize_sha(before_sha, field="runtime_before_sha")
        after_sha = normalize_sha(after_sha, field="runtime_after_sha")
        if after_sha != record.merged_commit_sha:
            raise DeliveryConflict("runtime materialization does not identify the approved merged commit")
        if record.runtime_before_sha and before_sha != record.runtime_before_sha:
            raise DeliveryConflict("runtime materialization before revision differs from the rollback pack")
        if int(main_pid) <= 0:
            raise DeliveryBlocked("runtime materialization requires a positive main process id")
        interpreter = str(service_interpreter or "").strip()
        if not interpreter or len(interpreter) > 500:
            raise DeliveryBlocked("runtime materialization requires a bounded service interpreter identity")

        manifest = self._load_rollback_pack(record)
        runtime = manifest.get("runtime")
        if not isinstance(runtime, Mapping):
            raise DeliveryBlocked("rollback pack is missing runtime identity")
        if str(runtime.get("before_sha") or "").lower() != before_sha:
            raise DeliveryConflict("runtime materialization before revision differs from the rollback pack")
        manifest["runtime"] = {
            **dict(runtime),
            "before_sha": before_sha,
            "after_sha": after_sha,
        }
        pack_sha, manifest = self._persist_rollback_pack(record, manifest)
        snapshot = {
            "before_sha": before_sha,
            "after_sha": after_sha,
            "main_pid": int(main_pid),
            "service_interpreter": interpreter,
            "materialized_at": int(self.now()),
        }
        actions = list(record.runtime_actions or [])
        if restart_command is not None:
            actions.append(
                self._runtime_action(
                    action="restart",
                    command=restart_command,
                    result=restart_result or {"status": "recorded_external"},
                    recorded_at=int(self.now()),
                )
            )
        fields = {
            "runtime_before_sha": before_sha,
            "runtime_after_sha": after_sha,
            "runtime_integration_mode": "external_controller",
            "activation_state": "pending",
            "live_identity_json": snapshot,
            "rollback_pack_sha256": pack_sha,
            "rollback_manifest_json": manifest,
            "runtime_actions_json": actions,
        }
        if record.state == "rollback_pack_ready":
            self._set_state(
                task_id,
                "runtime_materialized",
                expected={"rollback_pack_ready"},
                fields=fields,
                event=snapshot,
            )
        return self._set_state(
            task_id,
            "activation_pending",
            expected={"runtime_materialized", "activation_pending"},
            fields=fields,
            event=snapshot,
        )

    def record_runtime_health(
        self,
        task_id: str,
        *,
        evidence: Mapping[str, Any],
    ) -> DeliveryRecord:
        """Persist staged health evidence without restarting or finalizing."""
        record = self._get(task_id)
        if record is None or record.state != "activation_pending":
            raise DeliveryStateError("runtime health requires activation_pending state")
        if os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("HERMES_DELEGATED_CHILD_CONTEXT"):
            raise DeliveryBlocked("gateway/delegated workers cannot attest staged runtime health")
        if not isinstance(evidence, Mapping) or _SECRET_RE.search(canonical_json(evidence)):
            raise DeliveryBlocked("runtime health evidence is invalid or contains a credential-shaped value")
        expected_sha = str(record.runtime_after_sha or record.merged_commit_sha or "").lower()
        observed_sha = str(evidence.get("runtime_after_sha") or "").lower()
        if observed_sha != expected_sha:
            raise DeliveryConflict("runtime health evidence does not identify the materialized commit")
        required = (
            "main_pid",
            "start_time",
            "service_interpreter",
            "hermes_cli_import",
            "sqlite_version",
            "health",
            "dispatcher",
            "cron",
        )
        missing = [key for key in required if not evidence.get(key)]
        if missing:
            raise DeliveryBlocked("runtime health evidence is missing: " + ", ".join(missing))
        health = _safe_value(dict(evidence))
        live_identity = dict(record.live_identity or {})
        live_identity.update(health)
        live_identity["health_evidence"] = health
        live_identity["health_recorded_at"] = int(self.now())
        return self._set_state(
            task_id,
            "activation_pending",
            expected={"activation_pending"},
            fields={"live_identity_json": live_identity},
            event={
                "runtime_after_sha": observed_sha,
                "health": str(evidence.get("health"))[:100],
                "dispatcher": str(evidence.get("dispatcher"))[:100],
                "cron": str(evidence.get("cron"))[:100],
            },
        )

    def verify_cutover(self, task_id: str, *, evidence_path: Path | str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None or record.state != "activation_pending":
            raise DeliveryStateError("cutover verification requires materialized runtime activation")
        if os.environ.get("HERMES_KANBAN_TASK"):
            raise DeliveryBlocked("gateway-hosted workers cannot self-attest live activation")
        path = Path(evidence_path).expanduser()
        try:
            evidence = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise DeliveryBlocked("cutover evidence is unreadable") from None
        if not isinstance(evidence, Mapping):
            raise DeliveryBlocked("cutover evidence must be an object")
        if _SECRET_RE.search(canonical_json(evidence)):
            raise DeliveryBlocked("cutover evidence contains a credential-shaped value")
        health_record = self.record_runtime_health(task_id, evidence=evidence)
        status = _runtime_health_status(evidence)
        if status != "healthy":
            raise DeliveryBlocked("cutover evidence is incomplete or not healthy")
        snapshot = dict(health_record.live_identity or {})
        return self._set_state(
            task_id,
            "activation_verified",
            expected={"activation_pending"},
            fields={
                "live_identity_json": snapshot,
                "runtime_actions_json": health_record.runtime_actions or [],
                "activation_verified_at": int(self.now()),
                "activation_state": "verified",
            },
            event={
                "activation_verified_at": int(self.now()),
                "runtime_after_sha": evidence.get("runtime_after_sha"),
                "main_pid": evidence.get("main_pid"),
            },
        )

    def finalize_verified_activation(self, task_id: str) -> DeliveryRecord:
        return self._set_state(task_id, "completed", expected={"activation_verified"}, event={"final": True, "activation_verified": True})

    def abort(self, task_id: str, *, reason: str) -> DeliveryRecord:
        record = self._get(task_id)
        if record is None:
            raise DeliveryError("delivery has not been started")
        if record.state in {"completed", "aborted"}:
            return record
        return self._set_state(task_id, "aborted", expected={record.state}, fields={"last_error_json": {"reason": _safe_diagnostic(reason), "at": int(self.now())}}, event={"reason": _safe_diagnostic(reason)})


def _repository_from_remote(url: str) -> Optional[str]:
    text = str(url or "").strip()
    if text.startswith("git@") and ":" in text:
        text = text.split(":", 1)[1]
    elif "://" in text:
        text = text.split("://", 1)[1].split("@", 1)[-1]
        text = text.split("/", 1)[1] if "/" in text else text
    text = text.removesuffix("/").removesuffix(".git")
    return text if _REPO_RE.fullmatch(text) else None


def _safe_remote_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 1000:
        raise DeliveryBlocked("Git remote URL is missing or unbounded")
    if "://" in text:
        parsed = urlsplit(text)
        if parsed.username or parsed.password:
            raise DeliveryBlocked("Git remote URL contains embedded credentials")
    if _SECRET_RE.search(text):
        raise DeliveryBlocked("Git remote URL contains a credential-shaped value")
    return text


def _normalized_pr_state(pr: Mapping[str, Any]) -> str:
    """Normalize GitHub's merged-PR REST shape without weakening the gate."""
    state = str(pr.get("state") or "").casefold()
    if state == "closed" and pr.get("merged") is True:
        merge_sha = str(pr.get("merge_commit_sha") or "").lower()
        if _SHA_RE.fullmatch(merge_sha) and pr.get("merged_at"):
            return "merged"
    return state


def _validate_pr_identity(pr: Mapping[str, Any], repository: str, number: int, branch: str, base_branch: str, head_sha: Optional[str] = None) -> None:
    if not isinstance(pr, Mapping):
        raise DeliveryBlocked("provider returned an invalid pull request object")
    returned_number = int(pr.get("number") or number)
    if returned_number != number:
        raise DeliveryConflict("provider PR number does not match immutable identity")
    state = _normalized_pr_state(pr)
    if state not in {"open", "merged"}:
        raise DeliveryBlocked("pull request is closed or provider state is unknown")
    if pr.get("draft") is not False:
        raise DeliveryBlocked("pull request is draft or provider did not confirm non-draft")
    head_value = pr.get("head")
    base_value = pr.get("base")
    head: Mapping[str, Any] = head_value if isinstance(head_value, Mapping) else {}
    base: Mapping[str, Any] = base_value if isinstance(base_value, Mapping) else {}
    if str(head.get("ref") or pr.get("head_branch") or "") != branch:
        raise DeliveryConflict("provider PR branch does not match immutable identity")
    if str(base.get("ref") or pr.get("base_branch") or "") != base_branch:
        raise DeliveryConflict("provider PR base does not match immutable identity")
    if head_sha is not None and str(head.get("sha") or pr.get("head_sha") or "").lower() != head_sha.lower():
        raise DeliveryConflict("provider PR head does not match immutable reviewed head")
    url = pr.get("html_url") or pr.get("url")
    if url:
        normalize_pr_url(repository, number, url)


def secrets_token() -> str:
    """Opaque event id only; never derived from or containing credentials."""
    return hashlib.sha256(f"{os.getpid()}:{time.time_ns()}".encode()).hexdigest()[:20]


__all__ = [
    "DELIVERY_STATES",
    "DELIVERY_SCHEMA_SQL",
    "MERGE_METHODS",
    "TARGET_POLICIES",
    "DeliveryBlocked",
    "DeliveryConflict",
    "DeliveryCoordinator",
    "DeliveryError",
    "DeliveryRecord",
    "DeliveryStateError",
    "EffectPending",
    "GhGitHubAdapter",
    "ReviewPacket",
    "SubprocessGitAdapter",
    "canonical_json",
    "ensure_schema",
    "normalize_repository",
    "normalize_sha",
    "validate_transition",
]
