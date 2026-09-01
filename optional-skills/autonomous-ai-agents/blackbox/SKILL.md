---
name: blackbox
description: Delegate coding tasks to the Blackbox AI multi-model CLI.
version: 1.0.1
author: Hermes Agent (Nous Research)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Blackbox, Multi-Agent, Judge, Multi-Model]
    related_skills: [claude-code, codex, hermes-agent]
---

# Blackbox CLI

role: Blackbox delegation operator
do: verify install/auth; choose one-shot or PTY; set workdir; run, monitor, resume, review; report changed files/results
inputs: coding prompt, project workdir, optional checkpoint/session, model set, output target
outputs: Blackbox result, monitored process state, checkpoint continuation, review note or changed workspace
¬: invoke without PTY; omit workdir; kill slow work without diagnosis; expose API keys; assume multi-model mode is free; mutate user worktree for isolated reviews

Delegate coding tasks to [Blackbox AI](https://www.blackbox.ai/) through the Hermes `terminal` tool. The npm package is `@blackbox_ai/blackbox-cli`, binary `blackbox`; it is a TypeScript coding agent that can dispatch Claude, Codex, Gemini, or Blackbox Pro and use a judge to select an implementation. Interactive sessions, headless one-shots, checkpointing, MCP, and vision-model switching are supported.

## When to Use

- user asks for Blackbox specifically
- multi-model implementation or judge workflow is useful
- interactive coding, one-shot coding, checkpoint resume, MCP, or vision switching
- isolated PR review or independent parallel issue work

## Prerequisites

- Node.js 20+
- install: `npm install -g @blackbox_ai/blackbox-cli` (binary `blackbox`)
- API key from [app.blackbox.ai/dashboard](https://app.blackbox.ai/dashboard)
- configure once: `blackbox configure`, then enter the key
- `pty=true` for every invocation; Blackbox is an interactive terminal app

## Procedure

### 1. One-shot task

```
terminal(command="blackbox --prompt 'Add JWT authentication with refresh tokens to the Express API'", workdir="/path/to/project", pty=true)
```

Scratch workspace:

```
terminal(command="cd $(mktemp -d) && git init && blackbox --prompt 'Build a REST API for todos with SQLite'", pty=true)
```

### 2. Background long task

```
# Start in background with PTY
terminal(command="blackbox --prompt 'Refactor the auth module to use OAuth 2.0'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Blackbox asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

Use `poll`/`log` before deciding a slow run is stuck. Report what changed after completion.

### 3. Checkpoint resume

After completion Blackbox prints a checkpoint tag. Resume it with a follow-up prompt:

```
# After a task completes, Blackbox shows a checkpoint tag
# Resume with a follow-up task:
terminal(command="blackbox --resume-checkpoint 'task-abc123-2026-03-06' --prompt 'Now add rate limiting to the endpoints'", workdir="~/project", pty=true)
```

### 4. PR review in a temporary clone

Do not mutate the active worktree:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && blackbox --prompt 'Review this PR against main. Check for bugs, security issues, and code quality.'", pty=true)
```

### 5. Parallel work

Use one workdir per independent task:

```
terminal(command="blackbox --prompt 'Fix the login bug'", workdir="/tmp/issue-1", background=true, pty=true)
terminal(command="blackbox --prompt 'Add unit tests for auth'", workdir="/tmp/issue-2", background=true, pty=true)

# Monitor all
process(action="list")
```

### 6. Multi-model and vision

Run `blackbox configure`, select multiple providers, and enable the Chairman/judge workflow when comparing outputs. For image input, Blackbox can switch VLMs:

- `"once"` — switch for current query
- `"session"` — switch for session
- `"persist"` — stay on current model

### 7. Token limit

Set the session limit in `.blackboxcli/settings.json`:

```json
{
  "sessionTokenLimit": 32000
}
```

## Session Commands

| Command | Effect |
|---------|--------|
| `/compress` | Shrink conversation history to save tokens |
| `/clear` | Wipe history and start fresh |
| `/stats` | View current token usage |
| `Ctrl+C` | Cancel current operation |

## Quick Reference

| Flag | Effect |
|------|--------|
| `--prompt "task"` (`-p`) | Non-interactive one-shot execution |
| `--resume-checkpoint "tag"` | Resume from a saved checkpoint |
| `--yolo` (`-y`) | Auto-approve all actions and model switches |
| `--vlm-switch-mode <mode>` | Image-handling: `once`, `session`, or `persist` |
| `-c, --checkpointing` | Enable checkpointing of file edits |
| `blackbox configure` | Change settings, providers, models |
| `blackbox update` | Update the CLI to the latest version |
| `blackbox mcp` | Manage MCP servers |
| `blackbox extensions` | Manage CLI extensions |
| `blackbox voice <action>` / `blackbox shortcut` | Configure voice input / the `b` shortcut |

## Pitfalls

- `pty=true` is mandatory; without it the CLI can hang.
- Use `workdir` so the agent edits the intended project.
- Background long runs; monitor with `process`; do not kill only because progress is slow.
- Multi-model mode consumes credits faster; Blackbox is credit-based.
- Verify `blackbox` is installed and configured before delegation.
- Review in a temporary clone; never let a review command alter the active worktree.

## Verification

```python
terminal(command="blackbox --version", pty=true)
terminal(command="blackbox configure", pty=true)
terminal(command="blackbox --prompt 'Print BLACKBOX_OK and exit'", workdir="/tmp", pty=true)
```

Confirm the version/configuration command succeeds, the one-shot returns, and the output contains `BLACKBOX_OK`. For long work, inspect the final workspace diff and report the result/checkpoint.
