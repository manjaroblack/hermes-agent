---
name: grok
description: "Delegate coding to xAI Grok Build CLI (features, PRs)."
version: 0.1.1
author: Matt Maximo (MattMaximo), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Grok, xAI, Code-Review, Refactoring, Automation]
    related_skills: [codex, claude-code, hermes-agent]
---

# Grok Build CLI — Hermes Orchestration Guide

role: Grok Build delegation/operator
do: install/authenticate; choose headless or PTY; set cwd; bound/approve runs; parse output; resume UUID sessions; review diffs; report results
inputs: coding/review prompt, project cwd, model, session UUID, approval mode, output format
outputs: plain/JSON/streaming-JSON result, changed workspace, review note, resumable session
¬: assume Hermes xAI auth covers Grok; omit `--no-auto-update`; auto-approve read-only review; overlap worktrees; expose API keys; guess flags; leave tmux sessions

Delegate coding through the Hermes `terminal` tool to [Grok Build](https://docs.x.ai/build/overview), the xAI autonomous coding agent CLI (`grok`). It can read/write files, run shell commands, spawn subagents, and manage git. Modes: interactive TUI, headless `-p`, and ACP JSON-RPC. Prefer headless one-shots; use PTY for TUI.

## When to Use

- features, refactors, PR reviews, batch issue fixes
- a Codex/Claude-like coding backend with Grok/xAI desired
- read-only audit or multi-model/third-opinion work

## Prerequisites

- preferred install: `npm install -g @xai-official/grok`
- official fallback: `curl -fsSL https://x.ai/cli/install.sh | bash` (x.ai may be Cloudflare-walled)
- subscription auth: `grok login` → browser OAuth → `~/.grok/auth.json`; requires SuperGrok or X Premium+ and no per-token API billing
- check auth: `~/.grok/auth.json` or `grok --no-auto-update -p "Say ok."`
- TUI logout/login: `/logout`, `/login`
- no git repo required for ordinary runs; git recommended for PR/commit work
- auto-reads `CLAUDE.md`, `.claude/` skills/agents/MCP/hooks/rules, and `AGENTS.md`

API-key fallback only when subscription login is unavailable: set `XAI_API_KEY` for pay-as-you-go via `api.x.ai`; subscription `grok login` is the intended path.

## Procedure

### 1. Headless one-shot (preferred)

```
terminal(command="grok --no-auto-update -p 'Add a dark mode toggle to settings'", workdir="/path/to/project", timeout=180)
```

Always pass `--no-auto-update` in automation. Use headless for one-shot coding, CI/CD, scripts, structured parsing, and tasks without multi-turn conversation.

### 2. Interactive PTY/TUI

```
# Launch in a tmux session for capture-pane monitoring
terminal(command="tmux new-session -d -s grok-work -x 140 -y 40")
terminal(command="tmux send-keys -t grok-work 'cd /path/to/project && grok' Enter")

# Wait for startup, then send a task
terminal(command="sleep 5 && tmux send-keys -t grok-work 'Refactor the auth module to use JWT' Enter")

# Monitor progress
terminal(command="sleep 15 && tmux capture-pane -t grok-work -p -S -50")

# Exit when done
terminal(command="tmux send-keys -t grok-work '/quit' Enter && sleep 1 && tmux kill-session -t grok-work")
```

Use `pty=true` for direct interactive launches. `--no-alt-screen` gives inline output without fullscreen takeover; headless remains cleaner.

### 3. Headless flags/output

| Flag | Effect |
|------|--------|
| `-p, --single <PROMPT>` | Send one prompt, run headless, exit |
| `-m, --model <MODEL>` | Choose a model |
| `-s, --session-id <UUID>` | Assign a **NEW** valid UUID to a fresh conversation (must not already exist). Does **not** resume — use `--resume`/`--continue` for that. Only valid with `--resume`/`--continue` when paired with `--fork-session` |
| `-r, --resume [<UUID>]` | Resume an existing session by its UUID (or the most recent if omitted) |
| `-c, --continue` | Continue the most recent session in the current directory |
| `--fork-session` | When resuming, create a new session ID instead of reusing the original |
| `--max-turns <N>` | Cap the maximum number of agent turns |
| `--cwd <PATH>` | Set the working directory |
| `--output-format <FMT>` | `plain` (default), `json`, or `streaming-json` |
| `--always-approve` | Auto-approve all tool executions (the `--full-auto` / `--yolo` equivalent) |
| `--no-alt-screen` | Run inline, no fullscreen TUI takeover |
| `--no-auto-update` | Skip background update checks (use in all automation; hidden from `--help` but still works) |

Output modes: `plain` human text; `json` one final object; `streaming-json` newline-delimited events.

```
# Structured result for parsing
terminal(command="grok --no-auto-update -p 'List all TODO comments in src/' --output-format json", workdir="/project", timeout=120)

# Auto-approve for autonomous building
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the database layer and run the tests'", workdir="/project", timeout=300)
```

### 4. Background and continuation

```
# Start headless in background
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the auth module'", workdir="/project", background=true, notify_on_complete=true)
# Returns session_id

# Monitor
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Kill if needed
process(action="kill", session_id="<id>")
```

Sessions are UUID-keyed. `--session-id` starts a new UUID; `--resume` takes an existing UUID; `--continue` uses the latest in cwd.

```bash
SID=$(uuidgen)
```

```
# Start a session with a self-assigned UUID (must be a valid, unused UUID)
SID=$(uuidgen)
terminal(command="grok --no-auto-update -s $SID -p 'Start refactoring the database layer' --always-approve", workdir="/project", timeout=240)

# Resume that exact session later by its UUID
terminal(command="grok --no-auto-update -r $SID -p 'Now add connection pooling' --always-approve", workdir="/project", timeout=180)

# Or just continue the most recent session in this directory (no UUID needed)
terminal(command="grok --no-auto-update -c -p 'What did you change last time?'", workdir="/project", timeout=60)
```

### 5. Read-only audit → Markdown

1. Prepare stable input with Hermes `read_file`/`write_file`; snapshot relevant context into temp files.
2. Omit `--always-approve`; demand `markdown only, no preamble`.
3. Save stdout with `write_file`.

```
grok --no-auto-update -p "Read /tmp/current.md and /tmp/inventory.md. Produce markdown only, no preamble. Output a clean note titled 'Cleanup Review'." --output-format plain
```

For rewrites demand: `Return ONLY the full revised markdown document. No intro, no explanation, no code fences. Start immediately with '# Title'.` Verify first lines before overwrite.

### 6. PR review

Quick review:

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | grok --no-auto-update -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'", timeout=120)
```

Clone-to-temp, no active repo mutation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && grok --no-auto-update -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'", pty=true, timeout=300)
```

After inspecting and approving review text, post it explicitly:

```
terminal(command="gh pr comment 42 --body '<review text>'", workdir="/path/to/repo")
```

### 7. Parallel issue fixing

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Grok headless in each (background)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, notify_on_complete=true)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, notify_on_complete=true)

# Monitor
process(action="list")

# After completion: push and open PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Useful Commands

| Command | Purpose |
|---------|---------|
| `grok` | Start the interactive TUI |
| `grok -p "query"` | Headless one-shot |
| `grok login` / `grok logout` | Sign in / out (SuperGrok / X Premium+ OAuth) |
| `grok inspect` | Show what Grok discovered in cwd: config sources, instructions, skills, plugins, hooks, MCP servers |
| `grok agent stdio` | Run as an ACP agent over JSON-RPC (for IDE/tool integration) |
| `grok update` | Update the CLI (needs the `x.ai` host; skip in automation) |

TUI-only commands: `/model <name>`, `/always-approve`, `/plan`, `/context`, `/compact`, `/resume`, `/sessions`, `/fork`, `/usage`, `/quit`; `Shift+Tab` cycles modes. Plan mode blocks writes except session plan file.

## Config

`~/.grok/config.toml`:

```toml
[cli]
auto_update = false          # skip background update checks persistently

[ui]
permission_mode = "ask"      # or "always-approve" to skip tool prompts by default

[models]
default = "grok-build-0.1"
```

Use global config, not project `.grok/config.toml`; `permission_mode` replaces legacy `approval_mode`/`yolo = true`.

## Pitfalls

- `grok login` requires SuperGrok/X Premium+; confirm subscription before `XAI_API_KEY` fallback.
- Hermes `x_search` OAuth and Grok CLI `~/.grok/auth.json` are separate; one does not prove the other.
- `--no-auto-update` avoids unreachable `x.ai`/`storage.googleapis.com` update checks.
- npm install avoids Cloudflare-walled x.ai installer.
- `--always-approve` can mutate; omit for read-only reviews/audits.
- headless `-p` skips TUI dialogs; TUI needs `pty=true` and preferably tmux.
- `--no-alt-screen` avoids garbled inline capture.
- no repo is needed generally; use `mktemp -d && git init` for scratch commit tasks.
- clean tmux with `tmux kill-session -t <name>`.

## Rules for Hermes Agents

1. prefer headless `-p`; use JSON output when parsing
2. set `workdir` or `--cwd`
3. pass `--no-auto-update` every automated invocation
4. `--always-approve` only for intentional autonomous writes
5. background long jobs with notification and monitor `process`
6. tmux for multi-turn TUI
7. verify Grok auth independently; do not assume Hermes xAI auth
8. report Grok changes and remaining work

## Verification

- `grok --no-auto-update -p "Say ok."` returns successfully after auth
- requested mode/format is used; JSON parses only JSON lines/objects as documented
- output workspace diff, tests, or review note inspected
- no read-only review had auto-approval
- UUID resume/continue targets intended session
- background/tmux processes are terminated after completion
