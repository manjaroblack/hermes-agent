"""The GUI installer must run the script from the commit it is installing."""

import subprocess
from pathlib import Path

HELPER = Path(__file__).resolve().parent / "e2e-assets" / "stage-served-install-scripts.sh"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_stage_served_install_scripts_uses_the_requested_rev(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "e2e@example.com")
    _git(repo, "config", "user.name", "e2e")
    scripts = repo / "scripts"
    scripts.mkdir()
    (scripts / "install.sh").write_text("echo old-sh\n", encoding="utf-8")
    (scripts / "install.ps1").write_text("# old-ps1\n", encoding="utf-8")
    _git(repo, "add", "scripts")
    _git(repo, "commit", "-m", "old")
    old = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()

    (scripts / "install.sh").write_text("echo new-sh\n", encoding="utf-8")
    (scripts / "install.ps1").write_text("# new-ps1\n", encoding="utf-8")
    _git(repo, "add", "scripts")
    _git(repo, "commit", "-m", "new")

    work = tmp_path / "work"
    work.mkdir()
    root = subprocess.check_output(
        ["bash", str(HELPER), str(repo), old, str(work)], text=True
    ).strip()

    staged = Path(root)
    assert staged == work / "install-script-root"
    assert (staged / "scripts" / "install.sh").read_text(encoding="utf-8") == "echo old-sh\n"
    ps1 = (staged / "scripts" / "install.ps1").read_bytes()
    assert ps1.startswith(b"\xef\xbb\xbf")
    assert ps1[3:] == b"# old-ps1\n"
