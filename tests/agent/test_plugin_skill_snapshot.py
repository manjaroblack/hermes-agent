"""Behavior contracts for the in-memory plugin skill roster snapshot."""

import json
import os
import socket
from pathlib import Path
from types import SimpleNamespace
from urllib import request as urllib_request

import pytest

from agent.skill_snapshot import build_skill_snapshot
from hermes_cli.plugin_runtime import plugin_callback_scope
from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest


def _context(manager):
    return PluginContext(
        PluginManifest(name="snapshot-plugin", version="1.0.0", source="test"), manager
    )


def _write_skill(root, name, description, *, body="excerpt", extra=""):
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n{extra}---\n{body}\n",
        encoding="utf-8",
    )
    return path


def test_snapshot_is_immutable_and_hot_reads_do_not_touch_disk(tmp_path, monkeypatch):
    home = tmp_path / "home"
    skills = home / "skills" / "testing" / "demo"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A bounded demo skill.\n---\n\n"
        "Use this excerpt when testing snapshots.\n",
        encoding="utf-8",
    )
    manager = PluginManager(scope_key=str(home))
    manager._discovered = True
    published = manager.publish_skills_snapshot("session-1")
    assert published is not None
    context = _context(manager)
    with plugin_callback_scope("session-1"):
        snapshot = context.skills_snapshot()

    assert snapshot is published
    assert snapshot.generation
    assert snapshot.entries[0].name == "demo"
    assert snapshot.entries[0].description == "A bounded demo skill."
    assert "Use this excerpt" in snapshot.entries[0].excerpt
    assert all("/" not in value for value in (snapshot.entries[0].name, snapshot.entries[0].description))
    with pytest.raises((AttributeError, TypeError)):
        snapshot.entries[0].name = "changed"
    with pytest.raises((AttributeError, TypeError)):
        snapshot.entries[0].__dict__["name"] = "changed"

    def poison(*_args, **_kwargs):
        raise AssertionError("hot snapshot read performed filesystem I/O")

    monkeypatch.setattr(Path, "read_text", poison)
    monkeypatch.setattr(Path, "resolve", poison)
    monkeypatch.setattr(Path, "open", poison)
    monkeypatch.setattr(Path, "stat", poison)
    monkeypatch.setattr(Path, "is_file", poison)
    monkeypatch.setattr(Path, "is_dir", poison)
    monkeypatch.setattr(Path, "mkdir", poison)
    monkeypatch.setattr(os, "walk", poison)
    monkeypatch.setattr(os, "scandir", poison)
    monkeypatch.setattr(socket, "socket", poison)
    monkeypatch.setattr(socket, "create_connection", poison)
    monkeypatch.setattr(urllib_request, "urlopen", poison)
    with plugin_callback_scope("session-1"):
        assert context.skills_snapshot() is snapshot


def test_snapshot_invalidation_revokes_stale_roster_until_republished(tmp_path):
    home = tmp_path / "home"
    skill = home / "skills" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: demo\ndescription: old\n---\nold excerpt\n", encoding="utf-8")
    manager = PluginManager(scope_key=str(home))
    manager._discovered = True
    first = manager.publish_skills_snapshot("session-1")
    manager.invalidate_skills_snapshot("session-1")

    assert first is not None
    assert manager.get_skills_snapshot("session-1") is None

    skill.write_text("---\nname: demo\ndescription: new\n---\nnew excerpt\n", encoding="utf-8")
    second = manager.publish_skills_snapshot("session-1")
    assert second is not None
    assert second.generation != first.generation
    assert second.entries[0].description == "new"


def test_plugin_skill_registration_republishes_existing_sessions(tmp_path):
    home = tmp_path / "home"
    skill = home / "skills" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
    plugin_skill = tmp_path / "plugin" / "SKILL.md"
    plugin_skill.parent.mkdir()
    plugin_skill.write_text("---\nname: remote\ndescription: remote\n---\n", encoding="utf-8")

    manager = PluginManager(scope_key=str(home))
    manager._discovered = True
    manager.publish_skills_snapshot("session-1")
    context = _context(manager)
    context.register_skill("remote", plugin_skill, "remote")

    refreshed = manager.get_skills_snapshot("session-1")
    assert refreshed is not None
    assert {entry.name for entry in refreshed.entries} >= {"demo", "snapshot-plugin:remote"}


def test_snapshots_are_scoped_to_manager_home_and_session(tmp_path):
    home_a = tmp_path / "a"
    home_b = tmp_path / "b"
    for home, name in ((home_a, "a-skill"), (home_b, "b-skill")):
        path = home / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"---\nname: {name}\ndescription: {name}\n---\n", encoding="utf-8")

    manager_a = PluginManager(scope_key=str(home_a))
    manager_b = PluginManager(scope_key=str(home_b))
    manager_a._discovered = manager_b._discovered = True
    manager_a.publish_skills_snapshot("session")
    manager_b.publish_skills_snapshot("session")

    with plugin_callback_scope("session"):
        snapshot_a = _context(manager_a).skills_snapshot()
        snapshot_b = _context(manager_b).skills_snapshot()
    assert snapshot_a is not None and snapshot_a.entries[0].name == "a-skill"
    assert snapshot_b is not None and snapshot_b.entries[0].name == "b-skill"
    assert manager_a.get_skills_snapshot("other-session") is None


def test_snapshot_reuses_visibility_precedence_and_namespaces(tmp_path, monkeypatch):
    profile = tmp_path / "profile-skills"
    external_a = tmp_path / "external-a"
    external_b = tmp_path / "external-b"
    project = tmp_path / "project-skills"
    plugin_skill = tmp_path / "plugin" / "skills" / "remote" / "SKILL.md"

    def write_skill(root, name, description, *, body="excerpt", extra=""):
        path = root / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: {description}\n{extra}---\n{body}\n",
            encoding="utf-8",
        )
        return path

    write_skill(profile, "overridden", "profile")
    write_skill(profile, "ambiguous", "profile copy")
    write_skill(profile, "disabled", "disabled")
    write_skill(project, "overridden", "trusted project")
    write_skill(external_a, "ambiguous", "external a")
    write_skill(external_b, "ambiguous", "external b")
    plugin_skill.parent.mkdir(parents=True)
    plugin_skill.write_text("---\nname: remote\ndescription: plugin file\n---\nplugin excerpt\n", encoding="utf-8")

    from agent import skill_utils
    monkeypatch.setattr(skill_utils, "get_disabled_skill_names", lambda _platform=None: {"disabled"})
    monkeypatch.setattr(skill_utils, "is_quarantined_project_skill", lambda _path: False)

    snapshot = build_skill_snapshot(
        profile,
        external_dirs=[external_a, external_b],
        project_dirs=[project],
        plugin_entries=[{"name": "snapshot-plugin:remote", "path": plugin_skill}],
        session_platform="linux",
    )

    assert snapshot is not None
    by_name = {entry.name: entry for entry in snapshot}
    assert by_name["overridden"].description == "trusted project"
    assert "ambiguous" not in by_name
    assert "disabled" not in by_name
    assert by_name["snapshot-plugin:remote"].description == "plugin file"


def test_snapshot_over_descriptor_cap_is_unavailable(tmp_path):
    skills = tmp_path / "skills"
    for index in range(513):
        write = skills / f"skill-{index}" / "SKILL.md"
        write.parent.mkdir(parents=True)
        write.write_text(
            f"---\nname: skill-{index}\ndescription: bounded\n---\nexcerpt\n",
            encoding="utf-8",
        )

    assert build_skill_snapshot(skills) is None


def test_snapshot_over_per_skill_read_cap_is_unavailable(tmp_path):
    skill = tmp_path / "skills" / "oversized" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: oversized\ndescription: bounded\n---\n" + "x" * (32 * 1024),
        encoding="utf-8",
    )

    assert build_skill_snapshot(skill.parents[1]) is None


def test_snapshot_over_whole_publication_raw_read_cap_is_unavailable(tmp_path):
    skills = tmp_path / "skills"
    target_size = 32_700

    for index in range(64):
        path = skills / f"skill-{index}" / "SKILL.md"
        path.parent.mkdir(parents=True)
        header = f"---\nname: skill-{index}\ndescription: bounded\n---\n"
        path.write_bytes((header + "x" * (target_size - len(header))).encode("utf-8"))

    within_cap = build_skill_snapshot(skills)
    assert within_cap is not None and len(within_cap) == 64

    path = skills / "skill-64" / "SKILL.md"
    path.parent.mkdir(parents=True)
    header = "---\nname: skill-64\ndescription: bounded\n---\n"
    path.write_bytes((header + "x" * (target_size - len(header))).encode("utf-8"))

    assert build_skill_snapshot(skills) is None


def test_snapshot_over_serialized_metadata_cap_is_unavailable(tmp_path):
    skills = tmp_path / "skills"
    description = "d" * 512
    excerpt = "😀" * 700
    for index in range(512):
        path = skills / f"skill-{index}" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            f"---\nname: skill-{index}\ndescription: {description}\n---\n{excerpt}",
            encoding="utf-8",
        )

    assert build_skill_snapshot(skills) is None


def test_snapshot_and_system_prompt_serialize_full_three_roster_in_stable_order(
    tmp_path, monkeypatch
):
    from agent import prompt_builder, skill_utils

    profile = tmp_path / "profile"
    project = tmp_path / "project"
    external = tmp_path / "external"
    _write_skill(profile, "a-profile", "profile description", body="profile excerpt")
    _write_skill(project, "b-project", "project description", body="project excerpt")
    _write_skill(external, "c-external", "external description", body="external excerpt")

    monkeypatch.setattr(skill_utils, "get_disabled_skill_names", lambda _platform=None: set())
    monkeypatch.setattr(skill_utils, "is_quarantined_project_skill", lambda _path: False)
    monkeypatch.setattr(prompt_builder, "get_disabled_skill_names", lambda _platform=None: set())
    monkeypatch.setattr(prompt_builder, "_current_session_platform_hint", lambda: "linux")
    monkeypatch.setattr(
        prompt_builder, "_skills_prompt_snapshot_path", lambda: tmp_path / "prompt-snapshot.json"
    )
    prompt_builder.clear_skills_system_prompt_cache(clear_snapshot=True)

    entries = build_skill_snapshot(
        profile, external_dirs=[external], project_dirs=[project], session_platform="linux"
    )
    prompt = prompt_builder._build_skills_system_prompt_inner(
        profile,
        [external],
        available_tools=None,
        available_toolsets=None,
        compact_categories=None,
        project_dirs=[project],
    )

    assert entries is not None
    assert tuple(entry.name for entry in entries) == (
        "a-profile",
        "b-project",
        "c-external",
    )
    assert prompt.count("- a-profile: profile description") == 1
    assert prompt.count("- b-project: [project] project description") == 1
    assert prompt.count("- c-external: external description") == 1
    assert (
        prompt.index("- a-profile")
        < prompt.index("- b-project")
        < prompt.index("- c-external")
    )
    assert "[project] project description" in prompt


def test_snapshot_rejects_profile_file_and_directory_symlink_escapes(tmp_path):
    skills = tmp_path / "skills"
    outside = tmp_path / "outside"
    _write_skill(skills, "visible", "visible", body="safe excerpt")
    escaped_file = _write_skill(outside, "escaped-file", "escaped", body="outside secret")
    escaped_dir = outside / "escaped-dir"
    _write_skill(outside, "escaped-dir", "escaped directory", body="outside directory secret")

    file_link = skills / "file-link" / "SKILL.md"
    file_link.parent.mkdir(parents=True)
    file_link.symlink_to(escaped_file)
    (skills / "dir-link").symlink_to(escaped_dir, target_is_directory=True)

    entries = build_skill_snapshot(skills)

    assert entries is not None
    assert [entry.name for entry in entries] == ["visible"]
    serialized = json.dumps(
        [(entry.name, entry.description, entry.excerpt) for entry in entries]
    )
    assert "outside secret" not in serialized
    assert "outside directory secret" not in serialized


def test_project_quarantine_and_org_user_project_merge_use_canonical_visibility(
    tmp_path, monkeypatch
):
    from agent import skill_utils
    from tools import skills_guard

    profile = tmp_path / "profile"
    project = tmp_path / "project"
    _write_skill(profile, "personal", "personal")
    org_root = profile / skill_utils.ORG_MIRROR_DIR_NAME
    org_root.mkdir(parents=True)
    (org_root / skill_utils.ORG_ACTIVE_MARKER).write_text("org-1", encoding="utf-8")
    _write_skill(org_root / "org-1", "shared", "shared")
    _write_skill(project, "project-safe", "project safe")
    _write_skill(project, "project-dangerous", "project dangerous")

    skill_utils._PROJECT_QUARANTINE_CACHE.clear()

    def scan_skill_cached(skill_dir, **_kwargs):
        verdict = "dangerous" if skill_dir.name == "project-dangerous" else "safe"
        return SimpleNamespace(verdict=verdict, summary=verdict), {}

    monkeypatch.setattr(skills_guard, "scan_skill_cached", scan_skill_cached)
    entries = build_skill_snapshot(profile, project_dirs=[project])

    assert entries is not None
    by_name = {entry.name: entry for entry in entries}
    assert set(by_name) == {"personal", "project-safe", "shared"}
    assert by_name["shared"].description == "[org-shared] shared"
    assert "project-dangerous" not in by_name


def test_malformed_frontmatter_is_bounded_and_generation_hash_tracks_excerpt(
    tmp_path,
):
    from agent.skill_snapshot import snapshot_generation

    skills = tmp_path / "skills"
    path = skills / "fallback" / "SKILL.md"
    path.parent.mkdir(parents=True)
    body = "😀" * 900
    path.write_text(
        "---\nname: fallback\ndescription: " + "é" * 400 + "\ninvalid: [\n---\n" + body,
        encoding="utf-8",
    )

    entries = build_skill_snapshot(skills)

    assert entries is not None and len(entries) == 1
    entry = entries[0]
    assert entry.name == "fallback"
    assert len(entry.description.encode("utf-8")) <= 512
    assert len(entry.excerpt) == 700
    assert len(entry.excerpt.encode("utf-8")) == 2_800
    first = snapshot_generation(tmp_path, "session", 1, entries)
    same = snapshot_generation(tmp_path, "session", 1, entries)
    changed = snapshot_generation(
        tmp_path,
        "session",
        1,
        (type(entry)(entry.name, entry.description, entry.excerpt[:-1]),),
    )
    assert len(first) == 64
    assert first == same
    assert changed != first


def test_snapshot_name_and_plugin_namespace_caps_are_fail_closed(tmp_path):
    skills = tmp_path / "skills"
    exact = skills / "exact" / "SKILL.md"
    exact.parent.mkdir(parents=True)
    exact.write_text(
        f"---\nname: {'n' * 128}\ndescription: exact\n---\nbody\n",
        encoding="utf-8",
    )
    exact_entries = build_skill_snapshot(skills)
    assert exact_entries is not None and exact_entries[0].name == "n" * 128

    exact.write_text(
        f"---\nname: {'n' * 129}\ndescription: too long\n---\nbody\n",
        encoding="utf-8",
    )
    assert build_skill_snapshot(skills) is None

    plugin = tmp_path / "plugin" / "demo" / "SKILL.md"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("---\nname: demo\ndescription: demo\n---\nbody\n", encoding="utf-8")
    assert build_skill_snapshot(
        tmp_path / "empty",
        plugin_entries=[{"name": "p" * 129, "path": plugin}],
    ) is None


def test_snapshot_applies_disabled_state_to_qualified_plugin_skill_names(
    tmp_path, monkeypatch
):
    from agent import skill_utils

    plugin = tmp_path / "plugin" / "demo" / "SKILL.md"
    plugin.parent.mkdir(parents=True)
    plugin.write_text(
        "---\nname: demo\ndescription: plugin demo\n---\nbody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        skill_utils,
        "get_disabled_skill_names",
        lambda _platform=None: {"snapshot-plugin:demo"},
    )

    entries = build_skill_snapshot(
        tmp_path / "empty",
        plugin_entries=[{"name": "snapshot-plugin:demo", "path": plugin}],
    )

    assert entries == ()


def test_snapshot_never_publishes_duplicate_canonical_skill_identities(tmp_path):
    skills = tmp_path / "skills"
    _write_skill(skills, "local-copy", "local", body="local body")
    local = skills / "local-copy" / "SKILL.md"
    local.write_text(
        "---\nname: snapshot-plugin:demo\ndescription: local\n---\nlocal body\n",
        encoding="utf-8",
    )
    plugin = tmp_path / "plugin" / "demo" / "SKILL.md"
    plugin.parent.mkdir(parents=True)
    plugin.write_text(
        "---\nname: demo\ndescription: plugin\n---\nplugin body\n",
        encoding="utf-8",
    )

    entries = build_skill_snapshot(
        skills,
        plugin_entries=[{"name": "snapshot-plugin:demo", "path": plugin}],
    )

    assert entries is None or sum(
        entry.name == "snapshot-plugin:demo" for entry in entries
    ) <= 1


def test_snapshot_refresh_changes_generation_without_mutating_frozen_system_bytes(tmp_path):
    home = tmp_path / "home"
    skill = _write_skill(home / "skills", "demo", "old", body="old excerpt")
    manager = PluginManager(scope_key=str(home))
    manager._discovered = True
    first = manager.publish_skills_snapshot("session")
    agent = SimpleNamespace(_cached_system_prompt="frozen\nbyte-stable\nsystem prompt")
    prompt_bytes = agent._cached_system_prompt.encode("utf-8")

    skill.write_text(
        "---\nname: demo\ndescription: new\n---\nnew excerpt\n",
        encoding="utf-8",
    )
    second = manager.refresh_skills_snapshot("session")

    assert first is not None and second is not None
    assert second.generation != first.generation
    assert second.entries[0].description == "new"
    assert agent._cached_system_prompt.encode("utf-8") == prompt_bytes


def test_supported_skill_cache_invalidation_republishes_active_snapshots(
    tmp_path, monkeypatch
):
    from agent import prompt_builder
    from hermes_cli import plugins

    home = tmp_path / "home"
    skill = _write_skill(home / "skills", "demo", "old", body="old excerpt")
    manager = PluginManager(scope_key=str(home))
    manager._discovered = True
    first = manager.publish_skills_snapshot("session")
    assert first is not None
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(plugins, "_plugin_manager", manager)
    monkeypatch.setattr(plugins, "_plugin_managers_by_home", {home.resolve(): manager})
    monkeypatch.setattr(
        prompt_builder, "_skills_prompt_snapshot_path", lambda: tmp_path / "prompt-snapshot.json"
    )

    skill.write_text(
        "---\nname: demo\ndescription: supported refresh\n---\nnew excerpt\n",
        encoding="utf-8",
    )
    prompt_builder.clear_skills_system_prompt_cache(clear_snapshot=True)

    refreshed = manager.get_skills_snapshot("session")
    assert refreshed is not None
    assert refreshed.generation != first.generation
    assert refreshed.entries[0].description == "supported refresh"
