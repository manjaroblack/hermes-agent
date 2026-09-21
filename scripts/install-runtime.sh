#!/usr/bin/env bash
# Runtime Edition installer overlay for Linux, macOS, and WSL.
#
# This wrapper selects the fork and local/runtime branch, then delegates all
# platform/bootstrap behavior to the maintained installer in this checkout.
# Native Windows is intentionally not supported by this v1 overlay.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_REPO_SSH="git@github.com:manjaroblack/hermes-agent.git"
RUNTIME_REPO_HTTPS="https://github.com/manjaroblack/hermes-agent.git"
RUNTIME_BRANCH="local/runtime"
TYPESAFE_REPO_HTTPS="https://github.com/manjaroblack/hermes-typesafe.git"
TYPESAFE_REF="0cbb7b3f61964467c97b5cfae7450571909c7040"
UPSTREAM_REPO_HTTPS="https://github.com/NousResearch/hermes-agent.git"

DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            ;;
        --branch|-Branch|--branch=*|-Branch=*)
            printf 'Runtime Edition always tracks %s; do not override --branch.\n' "$RUNTIME_BRANCH" >&2
            exit 2
            ;;
    esac
done

if [ "$DRY_RUN" = true ]; then
    printf 'Runtime Edition installer (dry run)\n'
    printf 'Repository: %s\n' "$RUNTIME_REPO_HTTPS"
    printf 'Branch: %s\n' "$RUNTIME_BRANCH"
    printf 'TypeSafe plugin: %s @ %s\n' "$TYPESAFE_REPO_HTTPS" "$TYPESAFE_REF"
    printf 'Upstream: %s (fetch-only)\n' "$UPSTREAM_REPO_HTTPS"
    printf 'Supported hosts: Linux, macOS, WSL\n'
    printf 'Native Windows: unsupported by this v1 overlay\n'
    exit 0
fi

# These variables are consumed by the forked install.sh overlay. The plugin
# installer never reads, prompts for, logs, or writes TYPESAFE_API_KEY.
export HERMES_REPO_URL_SSH="$RUNTIME_REPO_SSH"
export HERMES_REPO_URL_HTTPS="$RUNTIME_REPO_HTTPS"
export HERMES_INSTALL_BRANCH="$RUNTIME_BRANCH"
export HERMES_RUNTIME_PLUGIN_REPO_HTTPS="$TYPESAFE_REPO_HTTPS"
export HERMES_RUNTIME_PLUGIN_REF="$TYPESAFE_REF"
export HERMES_RUNTIME_PLUGIN_NAME="typesafe"
export HERMES_UPSTREAM_REPO_HTTPS="$UPSTREAM_REPO_HTTPS"

exec bash "$SCRIPT_DIR/install.sh" "$@"
