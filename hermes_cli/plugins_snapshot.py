"""Session-scoped publication for immutable plugin skill rosters."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence


class PluginSnapshotMixin:
    """Manager-local snapshot lifecycle; cold work never runs in hook dispatch."""

    home_path: Path
    _plugin_skills: dict[str, dict[str, Any]]
    _skill_snapshots: dict[tuple[str, str], Any]
    _skill_snapshot_counter: int

    def _snapshot_key(self, session_id: Optional[str]) -> tuple[str, str] | None:
        session = str(session_id or "").strip()
        if not session:
            return None
        # ``home_path`` is captured by PluginManager at construction. Keep this
        # lookup purely in-memory: ``skills_snapshot()`` runs on hook deadlines
        # and must not resolve/stat the filesystem.
        return str(self.home_path), session

    def get_skills_snapshot(self, session_id: Optional[str] = None):
        """Return a published snapshot without filesystem access."""
        from hermes_cli.plugin_runtime import current_plugin_session

        if not session_id:
            session_id = current_plugin_session()
        key = self._snapshot_key(session_id)
        return self._skill_snapshots.get(key) if key is not None else None

    def publish_skills_snapshot(
        self,
        session_id: str,
        *,
        skills_dir: Path | None = None,
        external_dirs: Sequence[Path] | None = None,
        project_dirs: Sequence[Path] | None = None,
        available_tools: set[str] | None = None,
        available_toolsets: set[str] | None = None,
        session_platform: str | None = None,
    ):
        """Build and publish one coherent roster outside any hook deadline."""
        key = self._snapshot_key(session_id)
        if key is None:
            return None
        from agent.skill_snapshot import build_skill_snapshot, snapshot_generation
        from hermes_constants import reset_hermes_home_override, set_hermes_home_override

        root = Path(skills_dir) if skills_dir is not None else self.home_path / "skills"
        token = set_hermes_home_override(str(self.home_path))
        try:
            if external_dirs is None or project_dirs is None:
                from agent.skill_utils import get_all_skills_dirs, get_project_skills_dirs
                if external_dirs is not None:
                    resolved_external = list(external_dirs)
                elif skills_dir is None:
                    # Keep create_dir and configured external directories in the
                    # same precedence order as prompt_builder/skills_tool.
                    resolved_external = list(get_all_skills_dirs()[1:])
                else:
                    resolved_external = []
                resolved_project = list(project_dirs) if project_dirs is not None else list(get_project_skills_dirs())
            else:
                resolved_external = list(external_dirs)
                resolved_project = list(project_dirs)
            plugin_entries = []
            for qualified, entry in self._plugin_skills.items():
                plugin_entries.append({
                    "name": qualified,
                    "path": entry.get("path"),
                    "description": entry.get("description", ""),
                })
            entries = build_skill_snapshot(
                root, external_dirs=resolved_external, project_dirs=resolved_project,
                plugin_entries=plugin_entries, available_tools=available_tools,
                available_toolsets=available_toolsets, session_platform=session_platform,
            )
        except Exception:
            entries = None
        finally:
            reset_hermes_home_override(token)
        if entries is None:
            self._skill_snapshots.pop(key, None)
            return None
        self._skill_snapshot_counter += 1
        snapshot = __import__("agent.skill_snapshot", fromlist=["SkillRosterSnapshot"]).SkillRosterSnapshot(
            generation=snapshot_generation(self.home_path, str(session_id), self._skill_snapshot_counter, entries),
            entries=tuple(entries),
        )
        self._skill_snapshots[key] = snapshot
        return snapshot

    def invalidate_skills_snapshot(self, session_id: str | None = None) -> None:
        """Immediately revoke one session's roster, or all rosters for this home."""
        if session_id is None:
            home = str(self.home_path)
            for key in [key for key in self._skill_snapshots if key[0] == home]:
                self._skill_snapshots.pop(key, None)
            return
        key = self._snapshot_key(session_id)
        if key is not None:
            self._skill_snapshots.pop(key, None)

    def _existing_skill_snapshot_sessions(self) -> tuple[str, ...]:
        home = str(self.home_path)
        return tuple(key[1] for key in self._skill_snapshots if key[0] == home)

    def _republish_existing_skill_snapshots(self, session_ids: Sequence[str] | None = None) -> None:
        """Rebuild invalidated sessions after an out-of-hook supported registry change."""
        from hermes_cli.plugin_runtime import current_plugin_session

        if current_plugin_session() is not None:
            return
        sessions = tuple(session_ids) if session_ids is not None else self._existing_skill_snapshot_sessions()
        for session_id in sessions:
            self.publish_skills_snapshot(session_id)

    def refresh_skills_snapshot(self, session_id: str, **kwargs: Any):
        """Explicit supported refresh: revoke before rebuilding."""
        self.invalidate_skills_snapshot(session_id)
        return self.publish_skills_snapshot(session_id, **kwargs)
