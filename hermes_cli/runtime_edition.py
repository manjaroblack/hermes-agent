"""Runtime Edition identity and fork-specific install defaults."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

RUNTIME_EDITION_NAME = "Runtime Edition"
RUNTIME_REPOSITORY = "manjaroblack/hermes-agent"
RUNTIME_DEFAULT_BRANCH = "local/runtime"
RUNTIME_REPOSITORY_SSH = f"git@github.com:{RUNTIME_REPOSITORY}.git"
RUNTIME_REPOSITORY_HTTPS = f"https://github.com/{RUNTIME_REPOSITORY}.git"

TYPESAFE_PLUGIN_NAME = "typesafe"
TYPESAFE_PLUGIN_REPOSITORY = "manjaroblack/hermes-typesafe"
TYPESAFE_PLUGIN_REPOSITORY_HTTPS = f"https://github.com/{TYPESAFE_PLUGIN_REPOSITORY}.git"
TYPESAFE_PLUGIN_REF = "0cbb7b3f61964467c97b5cfae7450571909c7040"


def _normalize_remote(url: str | None) -> str:
    """Return a credential-free ``host/path`` identity for a Git remote URL."""
    value = (url or "").strip()
    if value.startswith("git@") and ":" in value:
        host, path = value[4:].split(":", 1)
        value = f"https://{host}/{path}"
    elif re.match(r"^[^/@:]+/[^/]+(?:/[^/]+)?$", value):
        value = f"https://github.com/{value}"
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"{host}/{path}" if host and path else ""


def is_runtime_origin(url: str | None) -> bool:
    """True only for the public Runtime Edition fork origin."""
    return _normalize_remote(url) == f"github.com/{RUNTIME_REPOSITORY}"


def _git_config_path(project_root: Path) -> Path | None:
    """Locate a checkout's shared Git config without spawning a Git process."""
    git_path = project_root / ".git"
    if git_path.is_dir():
        return git_path / "config"
    if not git_path.is_file():
        return None
    try:
        gitdir_line = git_path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return None
    prefix, separator, raw_gitdir = gitdir_line.partition(":")
    if prefix.strip().lower() != "gitdir" or not separator:
        return None
    gitdir = Path(raw_gitdir.strip())
    if not gitdir.is_absolute():
        gitdir = (project_root / gitdir).resolve()
    commondir = gitdir / "commondir"
    if commondir.is_file():
        try:
            common = Path(commondir.read_text(encoding="utf-8").strip())
        except OSError:
            common = Path()
        if not common.is_absolute():
            common = (gitdir / common).resolve()
        return common / "config"
    return gitdir / "config"


def origin_url(project_root: Path) -> str | None:
    """Read ``remote.origin.url`` without invoking subprocesses or logging credentials."""
    config_path = _git_config_path(project_root)
    if config_path is None:
        return None
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    in_origin = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_origin = stripped.lower() == '[remote "origin"]'
            continue
        if not in_origin:
            continue
        match = re.match(r"url\s*=\s*(.*)$", stripped, flags=re.IGNORECASE)
        if not match:
            continue
        value = match.group(1).strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        return value or None
    return None


def default_update_branch(origin_url: str | None) -> str:
    """Select the update branch without changing upstream/other fork defaults."""
    return RUNTIME_DEFAULT_BRANCH if is_runtime_origin(origin_url) else "main"


__all__ = [
    "RUNTIME_DEFAULT_BRANCH",
    "RUNTIME_EDITION_NAME",
    "RUNTIME_REPOSITORY",
    "RUNTIME_REPOSITORY_HTTPS",
    "RUNTIME_REPOSITORY_SSH",
    "TYPESAFE_PLUGIN_NAME",
    "TYPESAFE_PLUGIN_REF",
    "TYPESAFE_PLUGIN_REPOSITORY",
    "TYPESAFE_PLUGIN_REPOSITORY_HTTPS",
    "default_update_branch",
    "is_runtime_origin",
    "origin_url",
]
