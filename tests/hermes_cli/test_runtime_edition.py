"""Runtime Edition installer, identity, and fork-update contracts."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _checkout_with_origin(tmp_path: Path, origin: str) -> Path:
    repo = tmp_path / "hermes-agent"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "remote", "add", "origin", origin)
    return repo


def test_runtime_fork_update_defaults_to_local_runtime(tmp_path, monkeypatch):
    from hermes_cli import main as hermes_main
    from hermes_cli import main_install_repair

    repo = _checkout_with_origin(tmp_path, "git@github.com:manjaroblack/hermes-agent.git")
    monkeypatch.setattr(hermes_main, "PROJECT_ROOT", repo)

    assert main_install_repair._resolve_update_branch(SimpleNamespace(branch=None)) == "local/runtime"


def test_non_runtime_origin_keeps_main_default(tmp_path, monkeypatch):
    from hermes_cli import main as hermes_main
    from hermes_cli import main_install_repair

    repo = _checkout_with_origin(tmp_path, "git@github.com:NousResearch/hermes-agent.git")
    monkeypatch.setattr(hermes_main, "PROJECT_ROOT", repo)

    assert main_install_repair._resolve_update_branch(SimpleNamespace(branch=None)) == "main"


def test_explicit_update_branch_wins_for_runtime_fork(tmp_path, monkeypatch):
    from hermes_cli import main as hermes_main
    from hermes_cli import main_install_repair

    repo = _checkout_with_origin(tmp_path, "git@github.com:manjaroblack/hermes-agent.git")
    monkeypatch.setattr(hermes_main, "PROJECT_ROOT", repo)

    assert main_install_repair._resolve_update_branch(SimpleNamespace(branch="release")) == "release"


def test_version_label_identifies_runtime_edition(monkeypatch):
    from hermes_cli import banner

    monkeypatch.setattr(banner, "get_git_banner_state", lambda: None)

    assert "Runtime Edition" in banner.format_banner_version_label()


@pytest.mark.parametrize("extra_args", [(), ("--skip-setup",)])
def test_runtime_installer_dry_run_is_keyless_and_socket_independent(extra_args):
    script = ROOT / "scripts" / "install-runtime.sh"
    env = os.environ.copy()
    env.pop("TYPESAFE_API_KEY", None)
    env["HTTPS_PROXY"] = "http://127.0.0.1:1"
    env["HTTP_PROXY"] = "http://127.0.0.1:1"
    env["ALL_PROXY"] = "http://127.0.0.1:1"

    result = subprocess.run(
        ["bash", str(script), "--dry-run", *extra_args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    assert "manjaroblack/hermes-agent.git" in output
    assert "local/runtime" in output
    assert "0cbb7b3f61964467c97b5cfae7450571909c7040" in output
    assert "fetch-only" in output
    assert "TYPESAFE_API_KEY" not in output
    assert "Upstream: https://github.com/NousResearch/hermes-agent.git (fetch-only)" in output


def test_runtime_installer_rejects_branch_override():
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install-runtime.sh"), "--branch", "main"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "local/runtime" in (result.stdout + result.stderr)


def test_runtime_installer_manifest_includes_plugin_stage():
    script = ROOT / "scripts" / "install-runtime.sh"
    result = subprocess.run(
        ["bash", str(script), "--manifest"],
        cwd=ROOT,
        env={**os.environ, "HTTPS_PROXY": "http://127.0.0.1:1"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    stages = json.loads(result.stdout)["stages"]
    plugin_stage = next(stage for stage in stages if stage["name"] == "runtime-plugin")
    assert plugin_stage["needs_user_input"] is False


def test_runtime_plugin_stage_uses_public_launcher_and_keeps_checkout_clean(tmp_path):
    """The staged plugin install uses the user launcher, not an in-tree path."""
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required for the installer plugin stage")

    plugin_repo = tmp_path / "plugin-source"
    plugin_repo.mkdir()
    (plugin_repo / "plugin.yaml").write_text(
        "name: typesafe\nversion: '0.0.1'\nkind: standalone\n", encoding="utf-8")
    (plugin_repo / "pyproject.toml").write_text(
        "[build-system]\nrequires = []\nbuild-backend = 'build_backend'\nbackend-path = ['.']\n",
        encoding="utf-8")
    (plugin_repo / "build_backend.py").write_text(
        """
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

NAME = 'fixture_plugin'
VERSION = '0.0.1'
DIST_INFO = f'{NAME}-{VERSION}.dist-info'


def _metadata(root):
    path = Path(root) / DIST_INFO
    path.mkdir(parents=True, exist_ok=True)
    (path / 'METADATA').write_text(
        f'Metadata-Version: 2.1\\nName: {NAME}\\nVersion: {VERSION}\\n', encoding='utf-8')
    (path / 'WHEEL').write_text(
        'Wheel-Version: 1.0\\nGenerator: fixture\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n',
        encoding='utf-8')
    return DIST_INFO


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    return _metadata(metadata_directory)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    filename = f'{NAME}-{VERSION}-py3-none-any.whl'
    target = Path(wheel_directory) / filename
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        archive.writestr(f'{DIST_INFO}/METADATA', f'Metadata-Version: 2.1\\nName: {NAME}\\nVersion: {VERSION}\\n')
        archive.writestr(
            f'{DIST_INFO}/WHEEL',
            'Wheel-Version: 1.0\\nGenerator: fixture\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n',
        )
        archive.writestr(f'{DIST_INFO}/RECORD', '')
    return filename
""".lstrip(),
        encoding="utf-8")
    _git(plugin_repo, "init", "-q")
    _git(plugin_repo, "add", ".")
    _git(
        plugin_repo,
        "-c", "user.name=Hermes Test",
        "-c", "user.email=hermes-test@example.invalid",
        "commit", "-qm", "fixture",
    )
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=plugin_repo, text=True).strip()

    home = tmp_path / "home"
    install_dir = tmp_path / "install"
    (home / "bin").mkdir(parents=True)
    (home / ".local" / "bin").mkdir(parents=True)
    install_dir.mkdir()
    (home / "bin" / "uv").symlink_to(uv)
    launcher = home / ".local" / "bin" / "hermes"
    launcher.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' \"$*\" > \"$HERMES_HOME/enable-args\"\n",
        encoding="utf-8")
    launcher.chmod(0o755)

    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "HERMES_HOME": str(home),
        "HERMES_RUNTIME_PLUGIN_REPO_HTTPS": plugin_repo.as_uri(),
        "HERMES_RUNTIME_PLUGIN_REF": revision,
        "HERMES_RUNTIME_PLUGIN_NAME": "typesafe",
        "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
    })
    venv = subprocess.run(
        [uv, "venv", str(install_dir / "venv"), "--python", "3.11"],
        env=env, capture_output=True, text=True, check=False,
    )
    assert venv.returncode == 0, venv.stderr

    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "install.sh"), "--dir", str(install_dir),
         "--hermes-home", str(home), "--stage", "runtime-plugin", "--json"],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    frame = next(json.loads(line) for line in reversed(result.stdout.splitlines()) if line.startswith("{"))
    assert frame == {"ok": True, "stage": "runtime-plugin", "skipped": False}
    assert (home / "enable-args").read_text(encoding="utf-8").strip() == (
        "plugins enable typesafe --no-allow-tool-override")

    target = home / "plugins" / "typesafe"
    assert target.is_dir()
    assert subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip() == revision
    assert not list(target.rglob("*.egg-info"))
    metadata = json.loads((home / "plugins" / ".install-metadata.json").read_text(encoding="utf-8"))
    assert metadata["typesafe"] == {"pinned": True, "revision": revision, "source": plugin_repo.as_uri()}
    installed = subprocess.check_output(
        [str(install_dir / "venv" / "bin" / "python"), "-c",
         "from importlib.metadata import version; print(version('fixture-plugin'))"],
        text=True,
    ).strip()
    assert installed == "0.0.1"
