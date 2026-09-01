---
name: antigravity-cli
description: "Operate the Antigravity CLI (agy): plugins, auth, sandbox."
version: 0.2.0
author: Tony Simons (asimons81), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Antigravity, CLI, Auth, Plugins, Sandbox]
    related_skills: [grok, codex, claude-code, hermes-agent]
---

# Antigravity CLI (`agy`)

role: Antigravity CLI/operator backend
do: install/version/help; separate wrapper vs TUI slash surface; run one-shot/PTY/background/resume/worktree; inspect auth/sandbox/plugins/logs; bound plain-text runs; report
inputs: coding/review prompt, project cwd, model, approval/sandbox mode, conversation ID, plugin/settings path
outputs: plain-text `agy` result, changed workspace, plugin/auth state, logs/diagnostics
¬: authenticate through Hermes; confuse shell wrapper with TUI; expect JSON/max-turns; skip `--print-timeout`; expose credentials; put agy on Kanban as coordinator; leave PTY/tmux/processes

Run all `agy` commands through Hermes `terminal`; inspect Antigravity files/logs with `read_file`. This skill is procedure/reference, not a Hermes network wrapper; Antigravity owns OS-keyring/browser auth.

## When to Use

- install/update/smoke-test `agy`
- non-interactive `agy --print`/`-p` work
- auth, sandbox, permissions, plugin state
- settings, keybindings, conversations, logs
- coding work or Gemini-family third-opinion review

## Mental Model

Two distinct surfaces:

1. **Shell wrapper:** `agy help`, `agy install`, `agy plugin`, `agy update`, `agy changelog`.
2. **Interactive TUI slash commands:** `/config`, `/permissions`, `/skills`, `/agents`, etc.; only inside running `agy` session.

`agy help` lists wrapper commands, not slash commands.

## Prerequisites

- binary on PATH: `command -v agy && agy --version`
- no Hermes env/API key; Antigravity auth uses OS keyring/browser sign-in
- `pty=true` for interactive TUI; tmux for capture/monitoring

## Procedure

### 1. Install/check

```
terminal(command="agy --version")
terminal(command="agy help")
terminal(command="agy plugin list")
terminal(command="agy --print 'Summarize the repo in 3 bullets'", workdir="/path/to/project")
```

### 2. One-shot (preferred)

```
terminal(command="agy -p 'Review this diff for bugs and security issues' --model 'Gemini 3.1 Pro (High)'", workdir="/path/to/repo", timeout=300)
```

`-p` runs non-interactively and exits. Use `agy models` for exact display names such as `Gemini 3.1 Pro (High)` and `Claude Opus 4.6 (Thinking)`. Repeat `--add-dir` for extra context roots.

### 3. Long/background run

```
terminal(command="agy -p 'Implement the change described in TASK.md and run the tests' --dangerously-skip-permissions", workdir="/path/to/repo", background=true, notify_on_complete=true)
# then: process(action="poll"/"log"/"wait", session_id=<id>)
```

Bound the outer `terminal` timeout; permission bypass is intentional autonomous write authority, not default.

### 4. Interactive PTY + tmux

```python
terminal(command="tmux new-session -d -s agy-work -x 140 -y 40")
terminal(command="tmux send-keys -t agy-work 'cd /path/to/project && agy -i' Enter")
terminal(command="sleep 5 && tmux capture-pane -t agy-work -p -S -50")
terminal(command="tmux send-keys -t agy-work '/quit' Enter && sleep 1 && tmux kill-session -t agy-work")
```

Resume with `--continue`/`-c` or `--conversation <id>`.

### 5. Parallel worktrees

Create one git worktree per independent sub-issue, run one background `agy -p` per worktree, then collect/review. Bound concurrency to machine/review capacity; do not overlap writes to one worktree.

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main
```

### 6. Output/bounds

- `agy -p` is plain text only; no `--output-format json`, session/cost/turn envelope
- parse stdout directly
- no `--max-turns`; bound with `--print-timeout` (default `5m`, e.g. `20m`) plus outer `terminal timeout=`

### 7. Orchestration boundary

Antigravity is an execution backend/third-opinion reviewer, not a first-class coordinator. Do not create a Kanban card for `agy` or treat it as a coordination layer; the assigned worker chooses it versus Codex/Claude/direct tools. Use explicitly when requested, configured, or for a cross-check.

## Core Paths

| Item | Path |
|---|---|
| binary | `agy` |
| app data | `~/.gemini/antigravity-cli/` |
| settings | `~/.gemini/antigravity-cli/settings.json` |
| keybindings | `~/.gemini/antigravity-cli/keybindings.json` |
| logs | `~/.gemini/antigravity-cli/log/cli-*.log` |
| conversations | `~/.gemini/antigravity-cli/conversations/` |
| brain | `~/.gemini/antigravity-cli/brain/` |
| history | `~/.gemini/antigravity-cli/history.jsonl` |
| plugin staging | `~/.gemini/antigravity-cli/plugins/<plugin_name>/` |

Use `read_file` for these paths.

## Quick Reference

### Wrapper

`agy changelog`; `agy help`; `agy install`; `agy plugin`/`agy plugins`; `agy update`.

### Flags

`--add-dir`; `--continue`/`-c`; `--conversation`; `--dangerously-skip-permissions`; `--print`/`-p`; `--print-timeout`; `--prompt`; `--prompt-interactive`/`-i`; `--sandbox`; `--log-file`; `--version`.

### Plugin

`agy plugin --help`: `list`, `import [source]`, `install <target>`, `uninstall <name>`, `enable <name>`, `disable <name>`, `validate [path]`, `link <mp> <target>`, `help`.

Install flags: `--dir`, `--skip-aliases`, `--skip-path`.

### TUI slash commands

Conversation: `/resume` (`/switch`), `/rewind` (`/undo`), `/rename <name>`, `/clear`, `/fork`, `/reset`, `/new`.

Settings/tools: `/config`, `/settings`, `/permissions`, `/model`, `/keybindings`, `/statusline`, `/tasks`, `/skills`, `/mcp`, `/open <path>`, `/usage`, `/logout`, `/agents`.

Helpers: `@` path autocomplete; `esc esc` clears prompt when not streaming; `!` runs terminal command; `?` help.

## Settings/Auth/Plugins

Common settings: `allowNonWorkspaceAccess`, `colorScheme`, `permissions.allow`, `trustedWorkspaces`. Permission modes: `request-review`, `always-proceed`, `strict`, `proceed-in-sandbox`. `enableTerminalSandbox` defaults `false`; launch `--sandbox`/`--dangerously-skip-permissions` can override current session.

Auth: OS keyring first; no session→browser Google sign-in; SSH prints URL and expects auth code; `/logout` removes saved credentials. On WSL token storage is file-based. Plugins stage under `~/.gemini/antigravity-cli/plugins/<plugin_name>/` and can bundle skills/agents/rules/MCP/hooks; empty `agy plugin list` is valid.

## Pitfalls

- `agy --version` is safe non-interactive; `agy version` is interactive and can fail without TTY
- first failure location: `~/.gemini/antigravity-cli/log/cli-*.log`
- persistent JSON settings differ from launch-time overrides
- `~/.gemini/antigravity-cli/bin/agentapi` wraps `agy agentapi`
- workspace identity may depend on launch directory and `.antigravitycli` marker
- no JSON output/result envelope; do not parse a JSON object unlike Claude Code
- use `--print-timeout`, not nonexistent `--max-turns`
- plain output can be long; set outer timeout and monitor background process

## Verification

Through `terminal` (and `read_file` for files):

1. `command -v agy`
2. `agy --version`
3. `agy help`
4. `agy plugin list`
5. read `settings.json`
6. read latest `cli-*.log`
7. read `keybindings.json` if relevant

A smoke prompt returns plain text; requested project diff/tests/logs are inspected; any PTY/tmux/background process is stopped.

## Support

- `references/cli-docs.md` — condensed getting-started, usage, and feature notes
