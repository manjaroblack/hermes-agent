"""Fail-closed admission checks for code-bearing Kanban workspaces.

The admission predicate deliberately has no database or task mutation side
 effects.  Callers provide the task snapshot and board metadata, and use the
structured result to park an unsafe card in triage before claiming it.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


CODE_PROFILE = "hermes-coding"
READ_ONLY_PROFILES = frozenset(
    {
        "hermes-incident",
        "hermes-orchestrator",
        "hermes-review",
        "hermes-security-audit",
    }
)


@dataclass(frozen=True)
class AdmissionResult:
    """A stable, auditable result from :func:`admit_workspace`.

    ``expected``, ``actual``, and ``repair`` are intentionally JSON-safe
    dictionaries.  They are persisted in the rejection event so an operator
    can repair a card without reproducing the dispatcher's filesystem view.
    """

    admitted: bool
    reason: Optional[str] = None
    expected: dict[str, Any] = field(default_factory=dict)
    actual: dict[str, Any] = field(default_factory=dict)
    repair: dict[str, Any] = field(default_factory=dict)
    code_bearing: bool = False
    read_only: bool = False

    @property
    def accepted(self) -> bool:
        """Compatibility spelling for callers that use acceptance language."""
        return self.admitted

    @property
    def ok(self) -> bool:
        """Compatibility spelling for predicate-style callers."""
        return self.admitted

    def to_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "expected": dict(self.expected),
            "actual": dict(self.actual),
            "repair": dict(self.repair),
            "code_bearing": self.code_bearing,
            "read_only": self.read_only,
        }

    def event_payload(self, *, previous_status: Optional[str] = None) -> dict[str, Any]:
        payload = {
            "reason": self.reason or "workspace_admission_rejected",
            "expected": dict(self.expected),
            "actual": dict(self.actual),
            "repair": dict(self.repair),
            "code_bearing": self.code_bearing,
            "read_only": self.read_only,
        }
        if previous_status is not None:
            payload["previous_status"] = previous_status
        return payload


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _profile(task: Any) -> str:
    return _text(_value(task, "assignee")).casefold()


def _explicit_bool(task: Any, names: tuple[str, ...]) -> Optional[bool]:
    for name in names:
        value = _value(task, name, None)
        if value is not None:
            return bool(value)
    return None


_DELIVERY_RE = re.compile(
    r"\b(?:commit|push|pull\s+request|open\s+(?:a\s+)?pr|submit\s+(?:a\s+)?pr)\b",
    re.IGNORECASE,
)
_NEGATED_DELIVERY_RE = re.compile(
    r"\b(?:no|without|not|don't|do\s+not)\s+(?:a\s+)?(?:commit|push|pull\s+request|pr)\b",
    re.IGNORECASE,
)


def is_read_only_role(task: Any) -> bool:
    """Return whether a task is owned by an explicitly read-only lane."""
    explicit = _explicit_bool(task, ("read_only", "readonly"))
    if explicit is not None:
        return explicit
    return _profile(task) in READ_ONLY_PROFILES


def is_code_bearing(task: Any) -> bool:
    """Classify whether a task needs the stronger workspace contract.

    The explicit task flags are supported for graph builders that carry richer
    metadata than the SQLite ``Task`` row.  The ordinary Kanban row remains
    conservative: the coding profile and persistent workspace kinds are code
    bearing unless an explicit read-only lane owns the task.
    """
    if is_read_only_role(task):
        return False
    if _profile(task) == CODE_PROFILE:
        return True
    kind = _text(_value(task, "workspace_kind", "scratch"))
    if kind in {"dir", "worktree"}:
        return True
    explicit = _explicit_bool(task, ("code_bearing", "requires_code", "requires_pr"))
    if explicit is not None:
        return explicit
    body = _text(_value(task, "body"))
    if _DELIVERY_RE.search(body) and not _NEGATED_DELIVERY_RE.search(body):
        return True
    return bool(_explicit_bool(task, ("requires_commit", "requires_push", "durable_delivery")))


def _repair(reason: str, *, detail: str) -> dict[str, Any]:
    return {
        "action": "triage",
        "owner": "hermes-orchestrator",
        "detail": detail,
        "reason": reason,
    }


def _reject(
    reason: str,
    *,
    expected: Optional[dict[str, Any]] = None,
    actual: Optional[dict[str, Any]] = None,
    detail: str,
    code_bearing: bool,
    read_only: bool,
) -> AdmissionResult:
    return AdmissionResult(
        admitted=False,
        reason=reason,
        expected=expected or {},
        actual=actual or {},
        repair=_repair(reason, detail=detail),
        code_bearing=code_bearing,
        read_only=read_only,
    )


def _accept(*, code_bearing: bool, read_only: bool, actual: Optional[dict[str, Any]] = None) -> AdmissionResult:
    return AdmissionResult(
        admitted=True,
        expected={},
        actual=actual or {},
        code_bearing=code_bearing,
        read_only=read_only,
    )


def _git(path: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = (result.stdout or "").strip()
    return value or None


def _git_path(raw: Optional[str], *, cwd: Path) -> Optional[Path]:
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve(strict=False)


def _worktree_records(repo: Path) -> list[dict[str, Optional[str]]]:
    raw = _git(repo, "worktree", "list", "--porcelain")
    if not raw:
        return []
    records: list[dict[str, Optional[str]]] = []
    current: Optional[dict[str, Optional[str]]] = None
    for line in raw.splitlines():
        if line.startswith("worktree "):
            if current is not None:
                records.append(current)
            current = {"path": str(Path(line[9:]).resolve(strict=False)), "branch": None}
        elif current is not None and line.startswith("branch "):
            current["branch"] = line[7:].strip() or None
    if current is not None:
        records.append(current)
    return records


def _board_repo(board: Any) -> tuple[Optional[Path], Optional[Path], Optional[str]]:
    default_workdir = _text(_value(board, "default_workdir"))
    if not default_workdir:
        return None, None, "board_scope_missing"
    anchor = Path(default_workdir).expanduser()
    if not anchor.is_absolute():
        return None, None, "board_scope_missing"
    anchor = anchor.resolve(strict=False)
    if not anchor.is_dir():
        return None, None, "board_scope_missing"
    root = _git_path(_git(anchor, "rev-parse", "--show-toplevel"), cwd=anchor)
    common = _git_path(_git(anchor, "rev-parse", "--git-common-dir"), cwd=anchor)
    git_dir = _git_path(_git(anchor, "rev-parse", "--git-dir"), cwd=anchor)
    if root is None or common is None or git_dir is None:
        return None, None, "repo_identity_mismatch"
    if root != anchor or git_dir != common:
        return None, None, "live_checkout_forbidden"
    return root, common, None


def _delivery_requires_code(task: Any) -> bool:
    body = _text(_value(task, "body"))
    return bool(_DELIVERY_RE.search(body) and not _NEGATED_DELIVERY_RE.search(body))


def _admit_read_only_worktree(task: Any, board: Any) -> AdmissionResult:
    """Admit a declared review/audit worktree without code ownership checks."""
    raw_path = _text(_value(task, "workspace_path"))
    if not raw_path:
        return _reject(
            "not_a_git_worktree",
            expected={"workspace_kind": "scratch or real linked worktree"},
            actual={"workspace_path": None},
            detail="Use a scratch workspace or declare the existing review worktree.",
            code_bearing=False,
            read_only=True,
        )
    requested = Path(raw_path).expanduser()
    if not requested.is_absolute():
        return _reject(
            "not_a_git_worktree",
            expected={"workspace_path": "absolute linked worktree"},
            actual={"workspace_path": raw_path},
            detail="Store an absolute path to the candidate worktree.",
            code_bearing=False,
            read_only=True,
        )
    actual_path = requested.resolve(strict=False)
    repo_root, repo_common, repo_error = _board_repo(board)
    expected = {
        "workspace_kind": "scratch or real linked worktree",
        "project_repo": str(repo_root) if repo_root else None,
    }
    actual: dict[str, Any] = {
        "workspace_path": str(actual_path),
        "exists": actual_path.exists(),
    }
    if repo_error is not None or repo_root is None or repo_common is None:
        return _reject(
            repo_error or "repo_identity_mismatch",
            expected=expected,
            actual=actual,
            detail="Set the board default_workdir to the project's primary checkout.",
            code_bearing=False,
            read_only=True,
        )
    if actual_path == repo_root or actual_path == repo_common:
        return _reject(
            "live_checkout_forbidden",
            expected=expected,
            actual=actual,
            detail="Review and audit workers must not run in the live checkout.",
            code_bearing=False,
            read_only=True,
        )
    if not actual_path.is_dir():
        return _reject(
            "not_a_git_worktree",
            expected=expected,
            actual=actual,
            detail="Use a real linked worktree or switch the read-only task to scratch.",
            code_bearing=False,
            read_only=True,
        )
    target_root = _git_path(_git(actual_path, "rev-parse", "--show-toplevel"), cwd=actual_path)
    target_common = _git_path(_git(actual_path, "rev-parse", "--git-common-dir"), cwd=actual_path)
    target_git_dir = _git_path(_git(actual_path, "rev-parse", "--git-dir"), cwd=actual_path)
    branch = _text(_git(actual_path, "branch", "--show-current"))
    actual.update(
        {
            "git_root": str(target_root) if target_root else None,
            "git_common_dir": str(target_common) if target_common else None,
            "branch_name": branch or None,
        }
    )
    if (
        target_root != actual_path
        or target_common != repo_common
        or target_git_dir is None
        or target_git_dir == target_common
        or not branch
    ):
        return _reject(
            "not_a_git_worktree",
            expected=expected,
            actual=actual,
            detail="Use a real linked worktree of the board project's primary repository.",
            code_bearing=False,
            read_only=True,
        )
    if branch in {"main", "master", "local/runtime"}:
        return _reject(
            "live_checkout_forbidden",
            expected=expected,
            actual=actual,
            detail="Use a task-specific branch rather than a live/default runtime branch.",
            code_bearing=False,
            read_only=True,
        )
    records = _worktree_records(repo_root)
    if not any(record.get("path") == str(actual_path) for record in records):
        return _reject(
            "not_a_git_worktree",
            expected=expected,
            actual=actual,
            detail="Register the declared path with git worktree add.",
            code_bearing=False,
            read_only=True,
        )
    return _accept(code_bearing=False, read_only=True, actual=actual)


def admit_workspace(task: Any, board: Any) -> AdmissionResult:
    """Pure, fail-closed admission predicate for a task snapshot and board.

    The function does not open a database and never creates, changes, or
    deletes a workspace.  It only reads the declared board/task identity and
    the live git metadata needed to prove that a code task owns its dedicated
    linked worktree.
    """
    if task is None:
        return _reject(
            "task_missing",
            detail="Provide a real task snapshot before dispatch.",
            code_bearing=True,
            read_only=False,
        )

    read_only = is_read_only_role(task)
    code_bearing = is_code_bearing(task)
    kind = _text(_value(task, "workspace_kind", "scratch")) or "scratch"
    task_id = _text(_value(task, "id"))

    # Scratch is a legitimate non-code/read-only workspace.  It does not
    # carry a source checkout and therefore must not be forced through git.
    if not code_bearing:
        if read_only and kind == "worktree":
            return _admit_read_only_worktree(task, board)
        if read_only and kind != "scratch":
            return _reject(
                "kind_not_worktree",
                expected={"workspace_kind": "scratch or worktree"},
                actual={"workspace_kind": kind},
                detail="Use a scratch workspace for read-only work, or a real linked worktree.",
                code_bearing=False,
                read_only=True,
            )
        return _accept(code_bearing=False, read_only=read_only, actual={"workspace_kind": kind})

    if kind != "worktree":
        return _reject(
            "kind_not_worktree",
            expected={"workspace_kind": "worktree"},
            actual={"workspace_kind": kind},
            detail="Set workspace_kind=worktree and use the task-keyed project worktree.",
            code_bearing=True,
            read_only=read_only,
        )

    board_project = _text(_value(board, "project_id"))
    task_project = _text(_value(task, "project_id"))
    if not board_project or task_project != board_project:
        return _reject(
            "project_mismatch",
            expected={"project_id": board_project or "scoped board project"},
            actual={"project_id": task_project or None},
            detail="Link the card to the board's project; do not dispatch an unscoped or cross-project card.",
            code_bearing=True,
            read_only=read_only,
        )

    repo_root, repo_common, repo_error = _board_repo(board)
    if repo_error is not None or repo_root is None or repo_common is None:
        return _reject(
            repo_error or "repo_identity_mismatch",
            expected={"project_id": board_project, "default_workdir": _text(_value(board, "default_workdir"))},
            actual={"default_workdir": _text(_value(board, "default_workdir")) or None},
            detail="Set the board default_workdir to the project's primary, non-linked git checkout.",
            code_bearing=True,
            read_only=read_only,
        )

    expected_path = (repo_root / ".worktrees" / task_id).resolve(strict=False)
    raw_path = _text(_value(task, "workspace_path"))
    expected_branch = _text(_value(task, "branch_name")) or f"wt/{task_id}"
    expected = {
        "project_id": board_project,
        "repo_root": str(repo_root),
        "workspace_path": str(expected_path),
        "branch_name": expected_branch,
        "task_id": task_id,
    }
    if not task_id:
        return _reject(
            "task_identity_missing",
            expected=expected,
            actual={},
            detail="Recreate or repair the card so it has a stable task id.",
            code_bearing=True,
            read_only=read_only,
        )
    if not raw_path:
        return _reject(
            "path_not_task_worktree",
            expected=expected,
            actual={"workspace_path": None},
            detail="Materialize the canonical <project>/.worktrees/<task-id> path before dispatch.",
            code_bearing=True,
            read_only=read_only,
        )
    requested = Path(raw_path).expanduser()
    if not requested.is_absolute():
        return _reject(
            "path_not_task_worktree",
            expected=expected,
            actual={"workspace_path": raw_path},
            detail="Store an absolute, task-keyed worktree path.",
            code_bearing=True,
            read_only=read_only,
        )
    actual_path = requested.resolve(strict=False)
    actual: dict[str, Any] = {
        "workspace_path": str(actual_path),
        "exists": actual_path.exists(),
    }
    if actual_path == repo_root or actual_path == repo_common:
        return _reject(
            "live_checkout_forbidden",
            expected=expected,
            actual=actual,
            detail="Never run a code worker in the project's live/default checkout.",
            code_bearing=True,
            read_only=read_only,
        )
    if actual_path != expected_path:
        return _reject(
            "path_not_task_worktree",
            expected=expected,
            actual=actual,
            detail="Use the canonical task-id-keyed worktree; sibling or inherited paths are unsafe.",
            code_bearing=True,
            read_only=read_only,
        )
    if not actual_path.is_dir():
        return _reject(
            "path_not_task_worktree",
            expected=expected,
            actual=actual,
            detail="Materialize the canonical path as a linked git worktree before dispatch.",
            code_bearing=True,
            read_only=read_only,
        )

    target_root = _git_path(_git(actual_path, "rev-parse", "--show-toplevel"), cwd=actual_path)
    target_common = _git_path(_git(actual_path, "rev-parse", "--git-common-dir"), cwd=actual_path)
    target_git_dir = _git_path(_git(actual_path, "rev-parse", "--git-dir"), cwd=actual_path)
    if target_root is None or target_common is None or target_git_dir is None:
        return _reject(
            "not_a_git_worktree",
            expected=expected,
            actual={**actual, "git": False},
            detail="Materialize a real git worktree at the canonical path.",
            code_bearing=True,
            read_only=read_only,
        )
    if target_root != actual_path or target_common != repo_common:
        return _reject(
            "repo_identity_mismatch",
            expected=expected,
            actual={
                **actual,
                "git_root": str(target_root),
                "git_common_dir": str(target_common),
            },
            detail="Recreate the worktree from the board project's primary repository.",
            code_bearing=True,
            read_only=read_only,
        )
    if target_git_dir == target_common:
        return _reject(
            "live_checkout_forbidden",
            expected=expected,
            actual={**actual, "git_dir": str(target_git_dir)},
            detail="The task path is a primary checkout, not a linked worktree.",
            code_bearing=True,
            read_only=read_only,
        )

    actual_branch = _text(_git(actual_path, "branch", "--show-current"))
    actual["branch_name"] = actual_branch or None
    records = _worktree_records(repo_root)
    target_record = next(
        (record for record in records if record.get("path") == str(actual_path)),
        None,
    )
    if target_record is None:
        return _reject(
            "not_a_git_worktree",
            expected=expected,
            actual=actual,
            detail="Register the canonical path with git worktree add from the project primary checkout.",
            code_bearing=True,
            read_only=read_only,
        )
    if not actual_branch:
        return _reject(
            "branch_identity_mismatch",
            expected=expected,
            actual=actual,
            detail="Checkout the recorded task branch; detached worktrees are not admissible.",
            code_bearing=True,
            read_only=read_only,
        )
    primary_branch = _text(_git(repo_root, "branch", "--show-current"))
    if actual_branch in {"main", "master", "local/runtime"} or actual_branch == primary_branch:
        return _reject(
            "live_checkout_forbidden",
            expected=expected,
            actual={**actual, "primary_branch": primary_branch or None},
            detail="Use a task-specific branch rather than the live/default runtime branch.",
            code_bearing=True,
            read_only=read_only,
        )
    if actual_branch != expected_branch:
        return _reject(
            "branch_identity_mismatch",
            expected=expected,
            actual=actual,
            detail="Repair branch_name or recreate the worktree so task and branch identities match.",
            code_bearing=True,
            read_only=read_only,
        )
    duplicate_branch = [
        record
        for record in records
        if record.get("branch") == f"refs/heads/{actual_branch}"
        and record.get("path") != str(actual_path)
    ]
    if duplicate_branch:
        return _reject(
            "branch_identity_mismatch",
            expected=expected,
            actual={**actual, "duplicate_worktrees": duplicate_branch},
            detail="Remove the sibling checkout or assign the task its own branch before dispatch.",
            code_bearing=True,
            read_only=read_only,
        )

    return _accept(
        code_bearing=True,
        read_only=read_only,
        actual={**actual, "git_common_dir": str(target_common)},
    )


__all__ = [
    "AdmissionResult",
    "CODE_PROFILE",
    "READ_ONLY_PROFILES",
    "admit_workspace",
    "is_code_bearing",
    "is_read_only_role",
]
