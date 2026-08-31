---
name: hermes-agent
description: "Use, configure, theme, extend, and orchestrate Hermes Agent."
version: 3.1.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, themes, skins, desktop-plugins, tui-widgets, petdex, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

role: Hermes operator
do: verify, configure, theme, extend, orchestrate, and troubleshoot Hermes surfaces
inputs: user goal + live repo/docs; load matching reference before detail answers
outputs: verified Hermes configuration, commands, skills, plugins, sessions, or UI artifacts
¬: infer feature absence from this overview; put settings in `.env`; mutate prompt/toolsets mid-conversation

Hermes Agent is an open-source Nous Research framework for terminal, native desktop, messaging, IDE, TUI, dashboard, and ACP use. It supports OpenRouter, Anthropic, OpenAI, Google, DeepSeek, xAI, local, and 20+ providers across Linux, macOS, Windows, and WSL.

## When to Use

- configure, operate, extend, theme, or troubleshoot Hermes Agent
- answer questions about CLI, gateway, profiles, skills, plugins, models, or UI surfaces

## Capabilities

- skills: reusable self-improving procedures
- memory: persistent identity, preferences, environment details, and lessons; pluggable backends
- gateway: Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Matrix, Teams, Email, and more with full tools
- surfaces: CLI, Ink TUI, Electron desktop, web dashboard, ACP for VS Code/Zed/JetBrains
- provider agnostic: swap models/providers; credential pools rotate keys
- profiles: independent configs, sessions, skills, memory
- extensions: plugins, MCP, custom tools, webhooks, cron, skins, desktop UI plugins, TUI widgets, pet mascots

This is a hub. Identity, quick start, spawning, and invariants live here; load the matching reference before answering details. Docs: https://hermes-agent.nousresearch.com/docs/

## Scope + Verification

This overview is not a complete source of truth. If a command/setting is absent here and references, inspect live CLI/source/docs before a negative answer.

- CLI: `hermes --help`, `hermes <command> --help`, `hermes_cli/main.py`
- docs: https://hermes-agent.nousresearch.com/docs/
- source: https://github.com/NousResearch/hermes-agent

## Procedure

1. Match the request to a capability and load its routed reference.
2. Verify current commands/settings against docs, live CLI, or source before acting.
3. Execute on the requested surface without crossing profile, secret, or cache boundaries.
4. Confirm the resulting state and report the real check/output.

## Quick Start

```bash
# Install (shell installer — sets up uv, Python, the venv, and the launcher)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Interactive chat (default surface; set display.interface: tui to launch the Ink TUI instead)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard  /  pick model+provider  /  health check
hermes setup
hermes model
hermes doctor

# Other surfaces
hermes desktop                 # launch the native desktop app (alias: hermes gui)
hermes dashboard               # web admin panel + embedded chat
hermes proxy                   # OpenAI-compatible local proxy backed by your OAuth provider
```

## Key Paths

```text
~/.hermes/config.yaml       Main configuration (settings — never secrets)
~/.hermes/.env              API keys and secrets ONLY (under $HERMES_HOME if set)
$HERMES_HOME/skills/        Installed skills
~/.hermes/skins/            Custom themes (see references/themes.md)
~/.hermes/desktop-plugins/  Desktop app UI plugins (see references/desktop-plugins.md)
~/.hermes/tui-widgets/      TUI widget apps (see references/tui-widgets.md)
~/.hermes/pets/             Installed pet mascots (see references/petdex.md)
~/.hermes/state.db          Canonical session store (SQLite + FTS5)
~/.hermes/sessions/         Gateway routing index, request dumps, *.jsonl transcripts
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout. Active profile resolves real home from `$HERMES_HOME`; never hardcode `~/.hermes` in code.

## Reference Routing

| User wants... | Load |
|---|---|
| CLI commands, subcommands, flags, "how do I run X" | `references/cli-reference.md` |
| In-session slash commands | `references/slash-commands.md` |
| Provider setup, API keys, OAuth | `references/providers-and-models.md` |
| config.yaml sections, toolsets, voice/STT/TTS | `references/configuration.md` |
| AGENTS.md / .hermes.md / CLAUDE.md project rules | `references/project-context-files.md` |
| Secret redaction, PII, approval modes, "reset permissions" | `references/security-privacy.md` |
| Delegation, cron, curator, kanban | `references/background-systems.md` |
| MCP servers, catalog, `hermes mcp` | `references/native-mcp.md` |
| Webhook routes + event-driven runs | `references/webhooks.md` |
| custom theme/skin | `references/themes.md` + `templates/skin.yaml` |
| desktop pane/widget/⌘K/page | `references/desktop-plugins.md` + `templates/plugin.js` |
| live TUI panel/modal | `references/tui-widgets.md` + `templates/clock.mjs` |
| pet mascot install/select/scale/diagnose | `references/petdex.md` |
| Windows keybinds, WinError 10106, BOM | `references/windows-quirks.md` |
| debugging voice/tools/gateway/aux models | `references/troubleshooting.md` |
| contributing tools/slash commands/tests | `references/contributor-guide.md` |
| delegate_task "capped at N" | `references/delegate-task-concurrency-diagnosis.md` |
| external app + Nous Portal subscription/OAuth | `references/portal-auth-for-third-party-apps.md` |

Apply skins yourself: `hermes config set display.skin <name>`; surfaces repaint live within ~a second. To tweak one color, edit active skin: `hermes skin set <key> <hex>`. Never fork `default`; it drops the palette and resets background. Do not tell users to run `/skin` for this operation.

## Spawn Additional Hermes Instances

Independent subprocesses have separate sessions, tools, and environments.

| | `delegate_task` | spawned `hermes` |
|-|-----------------|------------------|
| Isolation | separate conversation, shared process | fully independent process |
| Duration | minutes, parent-loop bounded | hours/days |
| Tool access | parent subset | full tool access |
| Interactive | no | yes, PTY |
| Use | quick parallel subtasks | long autonomous missions |

### One-shot / background

```text
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY via tmux

Hermes uses prompt_toolkit; interactive spawning needs a real terminal. Use tmux:

```text
# Start
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes'", timeout=10)

# Wait for startup, then send a message
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)

# Read output
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)

# Send follow-up
terminal(command="tmux send-keys -t agent1 'Add rate limiting middleware' Enter", timeout=5)

# Exit
terminal(command="tmux send-keys -t agent1 '/exit' Enter && sleep 2 && tmux kill-session -t agent1", timeout=10)
```

### Parallel agents

```text
# Agent A: backend
terminal(command="tmux new-session -d -s backend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t backend 'Build REST API for user management' Enter", timeout=15)

# Agent B: frontend
terminal(command="tmux new-session -d -s frontend -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t frontend 'Build React dashboard for user management' Enter", timeout=15)

# Check progress, relay context between them
terminal(command="tmux capture-pane -t backend -p | tail -30", timeout=5)
terminal(command="tmux send-keys -t frontend 'Here is the API schema from the backend agent: ...' Enter", timeout=5)
```

### Resume

```text
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

Tips: prefer `delegate_task` for quick work; use `-w` worktree mode for editing agents; set one-shot timeouts; use `hermes chat -q` fire-and-forget; tmux avoids raw PTY `\r`/`\n` issues; use `cronjob` for scheduled work. For delegate cap reports load `references/delegate-task-concurrency-diagnosis.md` (three real cap paths; absent one means model self-limiting). For Portal/OAuth questions load `references/portal-auth-for-third-party-apps.md` and walk plugin-vs-app, Portal exposure, local broker proxy.

## Surfaces

- Desktop (`hermes desktop` / `hermes gui`): native Electron macOS/Linux/Windows; streaming chat, sessions, Cmd+K, files, notifications, per-profile remote gateway; extend via `references/desktop-plugins.md`.
- Dashboard (`hermes dashboard`): admin panel for channels, MCP, webhooks, memory, profiles, embedded `hermes --tui`; OAuth/token gate.
- Ink TUI (`hermes --tui` or `display.interface: tui`): terminal UI with dock widgets; `references/tui-widgets.md`.
- Proxy (`hermes proxy`): local OpenAI API backed by signed-in OAuth provider; usable by Codex, Aider, Cline, scripts without an API key.

## Hard Invariants

- prompt cache sacred: never change past context, toolsets, or system prompt mid-conversation; context compression only exception
- role alternation: never adjacent assistant or user messages; tool results may repeat
- `.env` secrets only; behavioral settings in `config.yaml`
- profile-safe paths: code uses `get_hermes_home()`; session resolution uses `$HERMES_HOME`
- never hand-edit user `config.yaml`; use `hermes config set KEY VAL`

## Pitfalls

- do not confuse CLI, TUI, dashboard, Desktop, gateway, and proxy contracts; verify the selected surface first
- do not hardcode `~/.hermes`; profile isolation is part of the runtime contract
- do not mutate a live conversation's system prompt, toolset, or prior messages to add capability

## Verification

- selected Hermes surface, profile, and working directory are explicit
- command output or file changes are inspected rather than inferred
- cache, role-alternation, secret/config, and profile-path invariants remain intact
