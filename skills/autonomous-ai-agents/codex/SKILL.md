---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

[OpenAI Codex CLI](https://github.com/openai/codex) is the external coding worker covered here.

role: Hermes orchestrator for OpenAI Codex
do: delegate feature, refactor, review, and batch-fix work through terminal/process
inputs: git repo + task prompt; Codex CLI + OpenAI API key or Codex OAuth
outputs: code changes, review findings, commits/PRs when explicitly requested
¬: run outside git; interactive invocation without PTY; assume absent `OPENAI_API_KEY` means absent OAuth

## When to Use

- build features; refactor; review PRs; fix batches of issues
- user explicitly wants Codex or an external coding worker

## Prerequisites

- install: `npm install -g @openai/codex`
- auth: `OPENAI_API_KEY` or Codex CLI OAuth credentials from its login flow
- run inside a git repository; Codex refuses non-repo directories
- use `pty=true` in terminal calls; Codex is interactive

Hermes itself: `model.provider: openai-codex` uses Hermes-managed Codex OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. Standalone Codex CLI OAuth may live at `~/.codex/auth.json`; a missing `OPENAI_API_KEY` alone is not proof auth is missing.

## One-Shot

```text
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

Scratch repo:

```text
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Long Tasks

```text
# Start in background with PTY
terminal(command="codex exec --sandbox workspace-write 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--sandbox workspace-write` (`-s`) | Sandboxed; auto-approves file changes in workspace; recommended auto-build mode |
| `--dangerously-bypass-approvals-and-sandbox` | No sandbox/approvals; fastest, most dangerous; `--yolo` hidden alias |
| `--sandbox danger-full-access` | No Codex sandbox; useful when host service breaks bubblewrap |

`--full-auto` is deprecated; it still works but the live CLI recommends `--sandbox workspace-write`.

## Hermes Gateway Caveat

From a Hermes gateway/service context (for example Telegram-driven sessions), `workspace-write` may fail although it works in an interactive shell. Symptoms include bubblewrap/user-namespace errors: `setting up uid map: Permission denied` or `loopback: Failed RTM_NEWADDR: Operation not permitted`.

Use:

```text
codex exec --sandbox danger-full-access "<task>"
```

Then use process boundaries as the safety layer: explicit `workdir`, clean git status, narrow prompt, `git diff`, targeted tests, and confirmation before broad commits.

## PR Reviews

Clone into a temporary directory:

```text
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```text
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --sandbox workspace-write exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --sandbox workspace-write exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```text
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Procedure

1. Read the request; choose one-shot `codex exec` vs background interactive.
2. Verify git repo, Codex install/auth, and explicit `workdir`.
3. Launch with `pty=true`; use `--sandbox workspace-write` for builds unless gateway bubblewrap requires `danger-full-access`.
4. Monitor background IDs with `process(action="poll"|"log")`; answer prompts with `submit`; do not kill slow work without evidence.
5. Inspect diff, run targeted tests, and report concrete files/results.

## Rules

1. Always `pty=true` for Codex terminal calls.
2. Git repo required; use `mktemp -d && git init` for scratch.
3. `exec` for one-shots (`codex exec "prompt"`); `--sandbox workspace-write` for builds.
4. Background long tasks use `background=true` + `process` monitoring.
5. Parallel Codex processes are allowed when each has an isolated worktree.

## Pitfalls

- `--full-auto` still grants write access; use only in a disposable or explicitly approved worktree.
- Background workers can outlive the parent turn; poll them and inspect the resulting diff before reporting completion.
- Never run parallel workers against one mutable worktree; use separate worktrees or read-only review commands.

## Verification

- command ran with a real PTY and explicit workdir
- worker exit state and changed files are known
- targeted tests/lint ran after edits; review output contains concrete results
