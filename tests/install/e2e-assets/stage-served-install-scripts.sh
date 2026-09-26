#!/usr/bin/env bash
# Stage scripts/install.sh and scripts/install.ps1 from one git rev.
#
# Hermes-Setup otherwise downloads
# https://raw.githubusercontent.com/NousResearch/hermes-agent/<ref>/scripts/install.*
# An unpinned build uses ref "main". Upstream main's script now requires
# pm/lock.json. The commits this fork serves do not contain that file, so
# the GUI legs fail inside python-deps / venv before any update runs.
#
# Point HERMES_SETUP_DEV_REPO_ROOT at the printed directory. The published
# installer then runs the script from the same commit serve.git is cloning.
#
# Usage: stage-served-install-scripts.sh <repo> <rev> <work-root>
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: stage-served-install-scripts.sh <repo> <rev> <work-root>" >&2
  exit 2
fi

repo="$1"
rev="$2"
work="$3"
root="$work/install-script-root"

rm -rf "$root"
mkdir -p "$root"
git -C "$repo" archive --format=tar "$rev" scripts/install.sh scripts/install.ps1 \
  | tar -x -C "$root"

ps1="$root/scripts/install.ps1"
sh="$root/scripts/install.sh"
if [ ! -f "$ps1" ] || [ ! -f "$sh" ]; then
  echo "error: $rev is missing scripts/install.ps1 or scripts/install.sh" >&2
  exit 1
fi

# Hermes-Setup runs install.ps1 with `powershell -File`. PowerShell 5.1
# decodes a BOM-less file as the ANSI code page (#67193). The network
# download path adds this BOM; the dev-checkout path does not.
bom="$(od -An -t x1 -N 3 "$ps1" | tr -d ' \n')"
if [ "$bom" != "efbbbf" ]; then
  tmp="$ps1.tmp"
  printf '\357\273\277' > "$tmp"
  cat "$ps1" >> "$tmp"
  mv "$tmp" "$ps1"
fi

printf '%s\n' "$root"
