"""Bounded, immutable skill roster snapshots for plugin callbacks.

The cold builder deliberately shares the skill index iterators and visibility helpers used by the
system-prompt and skills tools.  The published value contains only primitive metadata; callers of
``PluginContext.skills_snapshot`` never get a path or a lazy loader.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

MAX_SNAPSHOT_ENTRIES = 512
MAX_NAME_BYTES = 128
MAX_DESCRIPTION_BYTES = 512
MAX_EXCERPT_CHARS = 700
MAX_EXCERPT_BYTES = 2_800
MAX_SKILL_READ_BYTES = 32 * 1024
MAX_RAW_READ_BYTES = 2 * 1024 * 1024
MAX_METADATA_BYTES = 1 * 1024 * 1024


class _SnapshotUnavailable(Exception):
    """Cold publication cannot represent the complete visible roster safely."""


@dataclass(frozen=True, slots=True)
class SkillDescriptor:
    name: str
    description: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class SkillRosterSnapshot:
    generation: str
    entries: tuple[SkillDescriptor, ...]


def _bounded_text(value: Any, *, max_bytes: int, max_chars: Optional[int] = None) -> str:
    text = str(value or "").strip()
    if max_chars is not None:
        text = text[:max_chars]
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip()


def _read_skill(path: Path, remaining: int) -> tuple[str, int] | None:
    """Read one regular skill file without following an escaped symlink."""
    try:
        if not path.is_file():
            return None
        resolved = path.resolve()
        if not resolved.is_file():
            return None
        size = resolved.stat().st_size
        if size > MAX_SKILL_READ_BYTES or size > remaining:
            raise _SnapshotUnavailable
        with resolved.open("rb") as handle:
            raw = handle.read(MAX_SKILL_READ_BYTES + 1)
        if len(raw) > MAX_SKILL_READ_BYTES:
            return None
        return raw.decode("utf-8"), len(raw)
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _entry_from_file(
    path: Path,
    root: Path,
    *,
    available_tools: Optional[set[str]],
    available_toolsets: Optional[set[str]],
    session_platform: Optional[str],
    raw_budget: list[int],
) -> tuple[str, str, str, str] | None:
    """Return ``(bare_name, category, description, excerpt)`` for one visible file."""
    try:
        resolved_root = root.resolve()
        resolved_path = path.resolve()
        if not resolved_path.is_relative_to(resolved_root):
            return None
    except (OSError, RuntimeError, ValueError):
        return None
    read = _read_skill(resolved_path, MAX_RAW_READ_BYTES - raw_budget[0])
    if read is None:
        return None
    content, consumed = read
    raw_budget[0] += consumed
    if raw_budget[0] > MAX_RAW_READ_BYTES:
        return None

    from agent.skill_utils import (
        extract_skill_conditions,
        extract_skill_description,
        parse_frontmatter,
        skill_matches_environment,
        skill_matches_platform,
    )
    try:
        frontmatter, body = parse_frontmatter(content)
    except Exception:
        return None
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    if not skill_matches_platform(frontmatter) or not skill_matches_environment(frontmatter):
        return None
    from agent.prompt_builder import _skill_should_show
    conditions = extract_skill_conditions(frontmatter)
    if not _skill_should_show(conditions, available_tools, available_toolsets, session_platform):
        return None

    from agent.skill_utils import ORG_MIRROR_DIR_NAME
    relative_parts = resolved_path.relative_to(resolved_root).parts
    org_id = None
    if len(relative_parts) >= 3 and relative_parts[0] == ORG_MIRROR_DIR_NAME:
        org_id, relative_parts = relative_parts[1], relative_parts[2:]
    skill_name = resolved_path.parent.name
    bare_name = str(frontmatter.get("name", skill_name)).strip() or skill_name
    if not bare_name:
        return None
    if len(bare_name.encode("utf-8", errors="replace")) > MAX_NAME_BYTES:
        raise _SnapshotUnavailable
    category = "general" if len(relative_parts) < 2 else (
        "/".join(relative_parts[:-2]) if len(relative_parts) > 2 else relative_parts[0]
    )
    description = _bounded_text(
        extract_skill_description(frontmatter), max_bytes=MAX_DESCRIPTION_BYTES
    )
    if org_id:
        description = _bounded_text(
            f"[org-shared] {description}".strip(),
            max_bytes=MAX_DESCRIPTION_BYTES,
        )
    excerpt = _bounded_text(body, max_bytes=MAX_EXCERPT_BYTES, max_chars=MAX_EXCERPT_CHARS)
    return bare_name, category, description, excerpt


def _iter_root_candidates(root: Path, *, project: bool) -> Iterable[Path]:
    from agent.skill_utils import iter_project_skill_files, iter_skill_index_files

    if not root.is_dir():
        return ()
    return iter_project_skill_files(root) if project else iter_skill_index_files(root, "SKILL.md")


def build_skill_snapshot(
    skills_dir: Path,
    *,
    external_dirs: Sequence[Path] = (),
    project_dirs: Sequence[Path] = (),
    plugin_entries: Sequence[Mapping[str, Any]] = (),
    available_tools: Optional[set[str]] = None,
    available_toolsets: Optional[set[str]] = None,
    session_platform: Optional[str] = None,
) -> Optional[tuple[SkillDescriptor, ...]]:
    """Cold-build one roster or return ``None`` when the bounded publication is unavailable."""
    from agent.skill_utils import get_disabled_skill_names

    raw_budget = [0]
    disabled = get_disabled_skill_names(session_platform)
    visible: list[tuple[str, str, str, str, bool]] = []
    claimed: dict[str, bool] = {}

    roots: list[tuple[Path, bool]] = [(Path(root), True) for root in project_dirs]
    roots.append((Path(skills_dir), False))
    roots.extend((Path(root), False) for root in external_dirs)
    for root, is_project in roots:
        try:
            files = _iter_root_candidates(root, project=is_project)
            for path in files:
                try:
                    candidate = _entry_from_file(
                        Path(path), root, available_tools=available_tools,
                        available_toolsets=available_toolsets, session_platform=session_platform,
                        raw_budget=raw_budget,
                    )
                except _SnapshotUnavailable:
                    return None
                if candidate is None:
                    # Malformed or incompatible files are omitted; explicit size failures return an
                    # unavailable roster so a partial roster can never be mistaken for complete.
                    if raw_budget[0] >= MAX_RAW_READ_BYTES:
                        return None
                    continue
                bare_name, category, description, excerpt = candidate
                if bare_name in disabled:
                    continue
                if is_project:
                    # Project skills intentionally shadow profile/external skills under the canonical
                    # trusted precedence rule; the first trusted project directory wins.
                    if claimed.get(bare_name):
                        continue
                    claimed[bare_name] = True
                elif claimed.get(bare_name):
                    continue
                visible.append((bare_name, category, description, excerpt, is_project))
                if len(visible) > MAX_SNAPSHOT_ENTRIES:
                    return None
        except (OSError, RuntimeError):
            return None

    # A duplicate outside the intentional project override is ambiguous to skill_view. Omit every copy
    # rather than silently selecting one source or leaking a shadowed fallback into a plugin hint.
    counts: dict[str, int] = {}
    for name, _category, _description, _excerpt, is_project in visible:
        if not is_project:
            counts[name] = counts.get(name, 0) + 1
    ambiguous = {name for name, count in counts.items() if count > 1}
    visible = [entry for entry in visible if entry[0] not in ambiguous]

    for raw in plugin_entries:
        if not isinstance(raw, Mapping):
            continue
        qualified = str(raw.get("name") or "").strip()
        path = raw.get("path")
        if not qualified or not isinstance(path, (str, Path)):
            continue
        if qualified in disabled:
            continue
        plugin_path = Path(path)
        try:
            root = plugin_path.parent.parent
        except Exception:
            continue
        try:
            candidate = _entry_from_file(
                plugin_path, root, available_tools=available_tools,
                available_toolsets=available_toolsets, session_platform=session_platform,
                raw_budget=raw_budget,
            )
        except _SnapshotUnavailable:
            return None
        if candidate is None:
            continue
        _bare, _category, description, excerpt = candidate
        if len(qualified.encode("utf-8", errors="replace")) > MAX_NAME_BYTES:
            return None
        visible.append((qualified, "plugin", _bounded_text(raw.get("description") or description,
                       max_bytes=MAX_DESCRIPTION_BYTES), excerpt, False))
        if len(visible) > MAX_SNAPSHOT_ENTRIES:
            return None

    # Plugin-qualified identities share the same public namespace as every other descriptor.
    # A collision is ambiguous to skill_view, so publish neither copy rather than exposing two
    # descriptors with the same lookup key or silently choosing a source.
    final_counts: dict[str, int] = {}
    for name, _category, _description, _excerpt, _project in visible:
        final_counts[name] = final_counts.get(name, 0) + 1
    final_ambiguous = {name for name, count in final_counts.items() if count > 1}
    visible = [entry for entry in visible if entry[0] not in final_ambiguous]

    if len(visible) > MAX_SNAPSHOT_ENTRIES:
        return None
    metadata_size = 2
    for name, _category, description, excerpt, _project in visible:
        try:
            metadata_size += len(json.dumps(
                {"name": name, "description": description, "excerpt": excerpt},
                ensure_ascii=False, separators=(",", ":"),
            ).encode("utf-8")) + 1
        except (TypeError, ValueError):
            return None
        if metadata_size > MAX_METADATA_BYTES:
            return None
    descriptors = tuple(
        SkillDescriptor(
            name=name,
            description=description,
            excerpt=excerpt,
        )
        for name, category, description, excerpt, _project in sorted(visible, key=lambda row: (row[1], row[0]))
    )
    try:
        serialized = json.dumps(
            [{"name": item.name, "description": item.description, "excerpt": item.excerpt} for item in descriptors],
            ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    if len(serialized) > MAX_METADATA_BYTES:
        return None
    return descriptors


def snapshot_generation(home: Path, session_id: str, counter: int, entries: Sequence[SkillDescriptor]) -> str:
    payload = json.dumps(
        {
            "home": str(home.resolve()), "session": str(session_id), "counter": counter,
            "entries": [(entry.name, entry.description, entry.excerpt) for entry in entries],
        }, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
