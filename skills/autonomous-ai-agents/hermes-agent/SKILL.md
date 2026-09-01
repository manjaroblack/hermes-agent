---
name: hermes-agent
description: "Use, configure, theme, extend, and orchestrate Hermes Agent."
version: 3.2.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, bots, bot-mode, features, themes, skins, desktop-plugins, tui-widgets, petdex, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

# Hermes Agent

role: Hermes Agent operations, configuration, and extension router
do: verify docs/repo; route matching reference; configure via CLI; spawn/orchestrate instances; preserve hard invariants
inputs: Hermes feature/config/provider/surface request; active profile; repository or docs facts
outputs: verified command/path/reference; configured or orchestrated Hermes workflow
¬: answer feature absence from memory; put settings in `.env`; hand-edit `config.yaml`; break prompt caching or message alternation; conflate client surface with process env

Hermes Agent is an open-source Nous Research framework for terminal, native
desktop, messaging, and IDE surfaces. It is in the same category as Claude Code
(Anthropic), Codex (OpenAI), and OpenClaw: autonomous coding/task-execution
agents using tool calling. It supports any LLM provider (OpenRouter, Anthropic,
OpenAI, Google, DeepSeek, xAI, local models, and 20+ others) and runs on Linux,
macOS, Windows, and WSL.

Hermes differentiators:

- **Self-improving skills** — save reusable procedures for future sessions.
- **Persistent memory** — retain identity, preferences, environment, lessons; pluggable backends.
- **Multi-platform gateway** — Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Matrix, Teams, Email, and more; full tools, not chat only.
- **Many surfaces** — CLI, Ink TUI, Electron desktop, web dashboard, ACP for VS Code/Zed/JetBrains.
- **Provider-agnostic** — swap models/providers; credential pools automatically rotate API keys.
- **Profiles** — independent configs, sessions, skills, memory.
- **Extensible/themeable** — plugins, MCP, custom tools, webhooks, cron, cross-surface skins, desktop plugins, TUI widgets, pet mascots.

**Hub:** body = identity, quick start, spawning/orchestration, hard invariants.
Everything else lives in references; **load the matching reference before
answering**; do not answer detail from this body alone.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## When to Use

- Hermes setup, configuration, providers, surfaces, skills, plugins, or orchestration
- any feature/command/settings question not answered here → fetch `llms.txt` first
- detail workflow → load the matching reference before answering

## Scope & Verification

Concise operating guide, not complete feature truth. An unmentioned feature,
command, or setting may exist; check live repo + official docs before a negative answer.

Good verification targets, cheapest first:

- **Every shipped feature:** `https://hermes-agent.nousresearch.com/docs/llms.txt`. Start here for "can Hermes do X?" / "how?"; generated every build, links answers, and is current. Fetch with `web_extract` or `curl -s https://hermes-agent.nousresearch.com/docs/llms.txt`; full set: `/docs/llms-full.txt`.
- CLI commands: `hermes --help`, `hermes <command> --help`, and `hermes_cli/main.py`
- Source tree: https://github.com/NousResearch/hermes-agent

Never answer "Hermes can't do that" from memory; the index makes negative answers checkable.

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

```
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

Profiles use `~/.hermes/profiles/<name>/` with the same layout. When a profile is active, resolve the real home from `$HERMES_HOME` — never hardcode `~/.hermes`.

## Routing Table — load the reference for the task

| User wants... | Load |
|---|---|
| **Anything not listed below — "can Hermes do X?", "how do I set up X?"** | **https://hermes-agent.nousresearch.com/docs/llms.txt** |
| Bots that chat, run routines, or message each other; the Bots tab | docs: `/user-guide/bot-mode` |
| CLI commands, subcommands, flags, "how do I run X" | `references/cli-reference.md` |
| In-session slash commands | `references/slash-commands.md` |
| Provider setup, API keys, OAuth | `references/providers-and-models.md` |
| config.yaml sections, toolsets, voice/STT/TTS | `references/configuration.md` |
| AGENTS.md / .hermes.md / CLAUDE.md project rules | `references/project-context-files.md` |
| Secret redaction, PII, approval modes, "reset permissions" | `references/security-privacy.md` |
| Delegation, cron, curator, kanban | `references/background-systems.md` |
| MCP servers (add, catalog, `hermes mcp`) | `references/native-mcp.md` |
| Webhook routes and event-driven runs | `references/webhooks.md` |
| A custom theme/skin ("synthwave theme", "change the gold ●") | `references/themes.md` + `templates/skin.yaml` |
| A desktop app UI element (pane, widget, ⌘K command, page) | `references/desktop-plugins.md` + `templates/plugin.js` |
| A live TUI panel or modal widget (ticker, clock, dashboard) | `references/tui-widgets.md` + `templates/clock.mjs` |
| Pet mascots — install, select, scale, diagnose | `references/petdex.md` |
| Windows-specific issues (keybinds, WinError 10106, BOM) | `references/windows-quirks.md` |
| Debugging: voice, tools missing, gateway, aux models | `references/troubleshooting.md` |
| Contributing code: adding tools, slash commands, tests | `references/contributor-guide.md` |
| delegate_task "capped at N" reports | `references/delegate-task-concurrency-diagnosis.md` |
| "Can app X use my Nous Portal subscription/OAuth?" | `references/portal-auth-for-third-party-apps.md` |
| Connecting a messaging platform (Telegram, Discord, Slack, WhatsApp, …) | docs: `/user-guide/messaging` |

The reference list is not the feature list; it covers topics needing more than
their docs page. For everything else, fetch `llms.txt` to map question → answer page.

Two theming rules without a reference: **apply skins yourself** with
`hermes config set display.skin <name>` (surfaces repaint within ~a second; do
not tell user to run `/skin`); **edit the ACTIVE skin** with
`hermes skin set <key> <hex>`; never fork `default` (palette/background reset).

## Spawning Additional Hermes Instances

Spawn additional Hermes processes as independent subprocesses: separate sessions,
tools, and environments.

### When to Use This vs delegate_task

| | `delegate_task` | Spawning `hermes` process |
|-|-----------------|--------------------------|
| Isolation | Separate conversation, shared process | Fully independent process |
| Duration | Minutes (bounded by parent loop) | Hours/days |
| Tool access | Subset of parent's tools | Full tool access |
| Interactive | No | Yes (PTY mode) |
| Use case | Quick parallel subtasks | Long autonomous missions |

### One-Shot Mode

```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)

# Background for long tasks:
terminal(command="hermes chat -q 'Set up CI/CD for ~/myapp'", background=true)
```

### Interactive PTY Mode (via tmux)

Hermes uses prompt_toolkit, which requires a real terminal. Use tmux for interactive spawning:

```
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

### Multi-Agent Coordination

```
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

### Session Resume

```
# Resume most recent session
terminal(command="tmux new-session -d -s resumed 'hermes --continue'", timeout=10)

# Resume specific session
terminal(command="tmux new-session -d -s resumed 'hermes --resume 20260225_143052_a1b2c3'", timeout=10)
```

### Tips

- **Quick subtasks:** prefer `delegate_task` (less overhead).
- **Code-editing agents:** use `-w` worktree mode (avoids conflicts).
- **One-shot:** set timeouts (complex tasks may take 5–10 minutes); use `hermes chat -q` for fire-and-forget.
- **Interactive:** use tmux; raw PTY has `\r`/`\n` issues with prompt_toolkit.
- **Scheduled:** use `cronjob` (delivery + retry).
- **"delegate_task is capped at N":** read `references/delegate-task-concurrency-diagnosis.md`; three real cap paths, otherwise the model self-limits and may rationalize it as a runtime cap.
- **External app + Nous Portal OAuth:** read `references/portal-auth-for-third-party-apps.md`; cover plugin-vs-app, Portal exposure, local-broker-proxy.

## Surfaces (quick orientation)

- **Desktop** (`hermes desktop` / `hermes gui`) — Electron macOS/Linux/Windows: streaming chat, sessions, Cmd+K, drag/drop, notifications, per-profile remote-gateway login; extend with `references/desktop-plugins.md`.
- **Dashboard** (`hermes dashboard`) — admin panel for channels, MCP, webhooks, memory, profiles, embedded `hermes --tui`; OAuth/token gate.
- **Ink TUI** (`hermes --tui` or `display.interface: tui`) — terminal UI with docked widgets; `references/tui-widgets.md`.
- **OpenAI-compatible proxy** (`hermes proxy`) — local API backed by signed-in OAuth provider; Codex CLI/Aider/Cline/scripts need no API key.

## Hard Invariants (never violate, regardless of what you loaded)

- **Never break prompt caching** — don't change past context, toolsets, or the system prompt mid-conversation. The only exception is context compression.
- **Message role alternation** — never two assistant or two user messages in a row; only `tool` results can repeat.
- **Secrets in `.env`, settings in `config.yaml`** — never tell a user to put a non-credential setting in `.env`.
- **Profile-safe paths** — `get_hermes_home()` in code, `$HERMES_HOME` when resolving paths in a session.
- **Never hand-edit `config.yaml` for the user** — use `hermes config set KEY VAL`; a stray indent can corrupt the file and break the live gateway.
