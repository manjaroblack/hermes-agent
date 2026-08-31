---
name: claude-code
description: "Delegate coding to Claude Code CLI (features, PRs)."
version: 2.2.1
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Anthropic, Code-Review, Refactoring, PTY, Automation]
    related_skills: [codex, hermes-agent, opencode]
---

# Claude Code — Hermes Orchestration Guide

role: Claude Code orchestrator
do: delegate coding, review, refactoring, extraction, testing, and git work through Claude Code
i/o: terminal commands, files, JSON/stream output, git worktrees, tmux session state
¬: unbounded permissions/cost; interactive PTY without tmux; guessed auth; claiming completion from an unverified pane

[Claude Code](https://code.claude.com/docs/en/cli-reference) is Anthropic's autonomous coding-agent CLI. Claude Code v2.x reads files, writes code, runs shell commands, spawns subagents, and manages git workflows.

## When to Use

- delegate coding, refactoring, testing, review, or PR work to Claude Code
- choose print mode for one-shot automation or tmux PTY for multi-turn work

## Prerequisites

- install: `npm install -g @anthropic-ai/claude-code`
- OAuth: run `claude` once to log in (browser OAuth for Pro/Max), or set `ANTHROPIC_API_KEY`
- console/API billing: `claude auth login --console`
- Enterprise: `claude auth login --sso`
- status: `claude auth status` (JSON) or `claude auth status --text`
- health: `claude doctor`
- version: `claude --version` (v2.x+)
- update: `claude update` or `claude upgrade`

## Procedure

1. Verify install/auth, repository, scope, and explicit `workdir`.
2. Choose print mode for one-shot work or tmux PTY for multi-turn/dialog work.
3. Launch with bounded tools, permissions, turns, and budget.
4. Monitor real output; answer dialogs through tmux; inspect files/diff.
5. Run affected checks and report concrete results before completion.

## Choose an Orchestration Mode

### Print mode (`-p`) — preferred

One-shot, non-interactive, no PTY/prompts; cleanest automation path:

```
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

Use for one-shot fixes/features/refactors, CI/CD, JSON-schema extraction, piped input (`cat file | claude -p "analyze this"`), and any task with no follow-up. Print mode skips all workspace-trust and permission dialogs.

### Interactive PTY via tmux

Use for multi-turn refactor→review→fix→test loops, human decisions, exploration, or slash commands (`/compact`, `/review`, `/model`). tmux is required for reliable orchestration:

```
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")

# Wait for startup, then send your task
# (after ~3-5 seconds for the welcome screen)
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor the auth module to use JWT tokens' Enter")

# Monitor progress by capturing the pane
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")

# Send follow-up tasks
terminal(command="tmux send-keys -t claude-work 'Now add unit tests for the new JWT code' Enter")

# Exit when done
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

## Interactive Dialogs (Critical)

Claude may display up to two first-launch confirmations; handle through `tmux send-keys`.

### Workspace trust

```
❯ 1. Yes, I trust this folder    ← DEFAULT (just press Enter)
  2. No, exit
```

Handle with `tmux send-keys -t <session> Enter`.

### Permission bypass warning

Only with `--dangerously-skip-permissions`:

```
❯ 1. No, exit                    ← DEFAULT (WRONG choice!)
  2. Yes, I accept
```

Navigate down then Enter:

```
tmux send-keys -t <session> Down && sleep 0.3 && tmux send-keys -t <session> Enter
```

Robust sequence:

```
# Launch with permissions bypass
terminal(command="tmux send-keys -t claude-work 'claude --dangerously-skip-permissions \"your task\"' Enter")

# Handle trust dialog (Enter for default "Yes")
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")

# Handle permissions dialog (Down then Enter for "Yes, I accept")
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")

# Now wait for Claude to work
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -60")
```

Trust is cached after first acceptance for a directory; bypass warning recurs each use of `--dangerously-skip-permissions`.

## CLI Subcommands

| Subcommand | Purpose |
|------------|---------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start REPL with initial prompt |
| `claude -p "query"` | Print mode (non-interactive, exits when done) |
| `cat file \| claude -p "query"` | Pipe content as stdin context |
| `claude -c` | Continue most recent conversation in this directory |
| `claude -r "id"` | Resume session by ID or name |
| `claude auth login` | Sign in (`--console` API billing, `--sso` Enterprise) |
| `claude auth status` | Login status JSON (`--text` human-readable) |
| `claude mcp add <name> -- <cmd>` | Add MCP server |
| `claude mcp list` | List configured MCP servers |
| `claude mcp remove <name>` | Remove MCP server |
| `claude agents` | List configured agents |
| `claude doctor` | Installation/auto-updater health |
| `claude update` / `claude upgrade` | Update Claude Code |
| `claude remote-control` | Control from claude.ai/mobile |
| `claude install [target]` | Install native build (stable/latest/specific) |
| `claude setup-token` | Long-lived auth token (subscription required) |
| `claude plugin` / `claude plugins` | Manage plugins |
| `claude auto-mode` | Inspect auto-mode classifier config |

## Print Mode

### JSON result

```
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

Example shape:

```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed",
  "usage": { "input_tokens": 5, "output_tokens": 603, ... },
  "modelUsage": { "claude-sonnet-4-6": { "costUSD": 0.078, "contextWindow": 200000 } }
}
```

Track `session_id` for resumption, `num_turns`, `total_cost_usd`; detect `subtype`: `success`, `error_max_turns`, `error_budget`.

### Streaming JSON

```
terminal(command="claude -p 'Write a summary' --output-format stream-json --verbose --include-partial-messages", timeout=60)
```

Newline-delimited events; live text:

```
claude -p "Explain X" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Stream events include `system/api_retry` with `attempt`, `max_retries`, and `error` (`rate_limit`, `billing_error`).

### Bidirectional stream

```
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```

`--replay-user-messages` re-emits user messages on stdout.

### Pipe known content

```
# Pipe a file for analysis
terminal(command="cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1", timeout=60)

# Pipe multiple files
terminal(command="cat src/*.py | claude -p 'Find all TODO comments' --max-turns 1", timeout=60)

# Pipe command output
terminal(command="git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1", timeout=60)
```

### JSON schema

```
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

Read `structured_output`; Claude validates against the schema.

### Continue, resume, fork

```
# Start a task
terminal(command="claude -p 'Start refactoring the database layer' --output-format json --max-turns 10 > /tmp/session.json", workdir="/project", timeout=180)

# Resume with session ID
terminal(command="claude -p 'Continue and add connection pooling' --resume $(cat /tmp/session.json | python -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)

# Or resume the most recent session in the same directory
terminal(command="claude -p 'What did you do last time?' --continue --max-turns 1", workdir="/project", timeout=30)

# Fork a session (new ID, keeps history)
terminal(command="claude -p 'Try a different approach' --resume <id> --fork-session --max-turns 10", workdir="/project", timeout=120)
```

### Bare CI mode

```
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` skips hooks, plugins, MCP discovery, and CLAUDE.md; it requires `ANTHROPIC_API_KEY` (skips OAuth). Selective context:

| To load | Flag |
|---|---|
| System additions | `--append-system-prompt "text"` or `--append-system-prompt-file path` |
| Settings | `--settings <file-or-json>` |
| MCP | `--mcp-config <file-or-json>` |
| Agents | `--agents '<json>'` |

Fallback on overload (print only):

```
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```

## CLI Flags

### Session/environment

| Flag | Effect |
|---|---|
| `-p, --print` | Non-interactive one-shot |
| `-c, --continue` | Most recent current-directory conversation |
| `-r, --resume <id>` | Specific ID/name; picker without ID |
| `--fork-session` | New ID while resuming |
| `--session-id <uuid>` | Specific conversation UUID |
| `--no-session-persistence` | No disk session in print mode |
| `--add-dir <paths...>` | Additional working directories |
| `-w, --worktree [name]` | Isolated `.claude/worktrees/<name>` |
| `--tmux` | tmux for `--worktree` |
| `--ide` | Connect valid IDE |
| `--chrome` / `--no-chrome` | Chrome browser integration on/off |
| `--from-pr [number]` | Session linked to GitHub PR |
| `--file <specs...>` | Startup resources `file_id:relative_path` |

### Model/performance

| Flag | Effect |
|---|---|
| `--model <alias>` | `sonnet`, `opus`, `haiku`, or `claude-sonnet-4-6` |
| `--effort <level>` | `low`, `medium`, `high`, `xhigh`, `max` |
| `--max-turns <n>` | Print-mode loop limit |
| `--max-budget-usd <n>` | Print-mode dollar cap |
| `--fallback-model <model>` | Print-mode overload fallback |
| `--betas <betas...>` | Beta request headers; API-key users |

### Permission/safety

| Flag | Effect |
|---|---|
| `--dangerously-skip-permissions` | Auto-approve all tool use |
| `--allow-dangerously-skip-permissions` | Make bypass available, not default |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | Whitelist tools |
| `--disallowedTools <tools...>` | Blacklist tools |
| `--tools <tools...>` | Built-in override: `""`, `"default"`, or names |

### Output/input

| Flag | Effect |
|---|---|
| `--output-format <fmt>` | `text`, `json`, `stream-json` |
| `--input-format <fmt>` | `text` or `stream-json` |
| `--json-schema <schema>` | Structured JSON schema |
| `--verbose` | Full turn output |
| `--include-partial-messages` | Partial chunks; stream-json + print |
| `--replay-user-messages` | Replay user messages; bidirectional stream |

### Prompt/context

| Flag | Effect |
|---|---|
| `--append-system-prompt <text>` | Add to default prompt; preserves built-ins |
| `--append-system-prompt-file <path>` | Add file contents |
| `--system-prompt <text>` | Replace full prompt |
| `--system-prompt-file <path>` | Replace with file |
| `--bare` | Skip hooks/plugins/MCP/CLAUDE.md/OAuth |
| `--agents '<json>'` | Dynamic subagents |
| `--mcp-config <path>` | MCP JSON; repeatable |
| `--strict-mcp-config` | Only supplied MCP config |
| `--settings <file-or-json>` | Settings file/inline JSON |
| `--setting-sources <sources>` | `user`, `project`, `local` |
| `--plugin-dir <paths...>` | Session-only plugins |
| `--disable-slash-commands` | Disable skills/slash commands |

### Debug/team

| Flag | Effect |
|---|---|
| `-d, --debug [filter]` | Debug logs/filter such as `"api,hooks"`, `"!1p,!file"` |
| `--debug-file <path>` | File debug logs; enables debug |
| `--teammate-mode <mode>` | `auto`, `in-process`, `tmux` |
| `--brief` | Enable `SendUserMessage` |

### Tool patterns

```
Read                    # All file reading
Edit                    # File editing (existing files)
Write                   # File creation (new files)
Bash                    # All shell commands
Bash(git *)             # Only git commands
Bash(git commit *)      # Only git commit commands
Bash(npm run lint:*)    # Pattern matching with wildcards
WebSearch               # Web search capability
WebFetch                # Web page fetching
mcp__<server>__<tool>   # Specific MCP tool
```

## Settings, Memory, and Slash Commands

Settings priority (highest first): CLI flags; `.claude/settings.local.json` (personal/gitignored); `.claude/settings.json` (shared/git-tracked); `~/.claude/settings.json` (global).

```json
{
  "permissions": {
    "allow": ["Bash(npm run lint:*)", "WebSearch", "Read"],
    "ask": ["Write(*.ts)", "Bash(git push*)"],
    "deny": ["Read(.env)", "Bash(rm -rf *)"]
  }
}
```

CLAUDE.md hierarchy: `~/.claude/CLAUDE.md`; `./CLAUDE.md`; `.claude/CLAUDE.local.md`. Interactive `#` adds memory, e.g. `# Always use 2-space indentation`. Modular rules: `.claude/rules/*.md` team-shared and `~/.claude/rules/*.md` personal. Auto-memory: `~/.claude/projects/<project>/memory/`, max 25KB or 200 lines per project.

### Slash commands

| Command | Purpose |
|---|---|
| `/help` | All commands, custom/MCP included |
| `/compact [focus]` | Compress context; CLAUDE.md survives; e.g. `/compact focus on auth logic` |
| `/clear` | Wipe history |
| `/context` | Context grid + optimization tips |
| `/cost` | Per-model/cache token usage |
| `/resume` | Switch/resume session |
| `/rewind` | Revert conversation/code checkpoint |
| `/btw <question>` | Side question without context cost |
| `/status` | Version/connectivity/session |
| `/todos` | Conversation action items |
| `/exit` or `Ctrl+D` | End |
| `/review` | Code review |
| `/security-review` | Security analysis |
| `/plan [description]` | Plan mode |
| `/loop [interval]` | Recurring tasks |
| `/batch` | 5–30 worktree parallel changes |
| `/model [model]` | Switch model; arrows adjust effort |
| `/effort [level]` | `low`, `medium`, `high`, `xhigh`, `max` |
| `/init` | Create CLAUDE.md |
| `/memory` | Edit CLAUDE.md |
| `/config` | Interactive settings |
| `/permissions` | Tool permissions |
| `/agents` | Specialized subagents |
| `/mcp` | MCP management UI |
| `/add-dir` | Additional working dirs |
| `/usage` | Plan/rate limits |
| `/voice` | Push-to-talk; 20 languages; hold Space/release to send |
| `/release-notes` | Version release-notes picker |

Custom command: `.claude/commands/<name>.md` project-shared or `~/.claude/commands/<name>.md` personal:

```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

Use `/deploy production`; `$ARGUMENTS` receives input.

Skill auto-invocation uses `.claude/skills/` Markdown guides:

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```

### Keyboard

| Key | Action |
|---|---|
| `Ctrl+C` | Cancel input/generation |
| `Ctrl+D` | Exit |
| `Ctrl+R` | Reverse-search history |
| `Ctrl+B` | Background task |
| `Ctrl+V` | Paste image |
| `Ctrl+O` | Transcript/thinking mode |
| `Ctrl+G` or `Ctrl+X Ctrl+E` | External prompt editor |
| `Esc Esc` | Rewind conversation/code or summarize |
| `Shift+Tab` | Permission mode cycle: Normal → Auto-Accept → Plan |
| `Alt+P` | Model |
| `Alt+T` | Thinking |
| `Alt+O` | Fast Mode |
| `\\` + `Enter` | Quick newline |
| `Shift+Enter` | Newline |
| `Ctrl+J` | Newline |
| `!` | Direct bash (`!npm test`); `!` alone toggles shell mode |
| `@` | File/dir autocomplete; e.g. `@./src/api/` |
| `#` | Add CLAUDE.md memory; e.g. `# Use 2-space indentation` |
| `/` | Slash commands |

Use `ultrathink` in a prompt for maximum reasoning on that turn regardless of `/effort`.

## Review, Worktrees, and Parallel Tasks

Quick review:

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems. Be thorough.' --max-turns 1", timeout=60)
```

Deep review:

```
terminal(command="tmux new-session -d -s review -x 140 -y 40")
terminal(command="tmux send-keys -t review 'cd /path/to/repo && claude -w pr-review' Enter")
terminal(command="sleep 5 && tmux send-keys -t review Enter")  # Trust dialog
terminal(command="sleep 2 && tmux send-keys -t review 'Review all changes vs main. Check for bugs, security issues, race conditions, and missing tests.' Enter")
terminal(command="sleep 30 && tmux capture-pane -t review -p -S -60")
```

PR number:

```
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

Claude worktree:

```
terminal(command="claude -w feature-x --tmux", workdir="/path/to/repo")
```

Creates `.claude/worktrees/feature-x` + tmux; iTerm2 native panes when available; `--tmux=classic` for traditional tmux.

Parallel:

```
# Task 1: Fix backend
terminal(command="tmux new-session -d -s task1 -x 140 -y 40 && tmux send-keys -t task1 'cd ~/project && claude -p \"Fix the auth bug in src/auth.py\" --allowedTools \"Read,Edit\" --max-turns 10' Enter")

# Task 2: Write tests
terminal(command="tmux new-session -d -s task2 -x 140 -y 40 && tmux send-keys -t task2 'cd ~/project && claude -p \"Write integration tests for the API endpoints\" --allowedTools \"Read,Write,Bash\" --max-turns 15' Enter")

# Task 3: Update docs
terminal(command="tmux new-session -d -s task3 -x 140 -y 40 && tmux send-keys -t task3 'cd ~/project && claude -p \"Update README.md with the new API endpoints\" --allowedTools \"Read,Edit\" --max-turns 5' Enter")

# Monitor all
terminal(command="sleep 30 && for s in task1 task2 task3; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -5 2>/dev/null; done")
```

## Project Context + Agents

A useful `CLAUDE.md` is concrete:

```markdown
# Project: My API

## Architecture
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database, Redis cache
- pytest for testing with 90% coverage target

## Key Commands
- `make test` — run full test suite
- `make lint` — ruff + mypy
- `make dev` — start dev server on :8000

## Code Standards
- Type hints on all public functions
- Docstrings in Google style
- 2-space indentation for YAML, 4-space for Python
- Name test files with `.test.ts` suffix
- No wildcard imports
```

Specific instructions beat "Write good code"; include exact indentation, test naming, and commands.

Custom agents live `.claude/agents/` (project), `--agents` (session), `~/.claude/agents/` (personal), priority project → CLI → user:

```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Security-focused code review
model: opus
tools: [Read, Bash]
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication/authorization flaws
- Secrets in code
- Unsafe deserialization
```

Invoke `@security-reviewer review the auth module`.

Dynamic:

```
terminal(command="claude --agents '{\"reviewer\": {\"description\": \"Reviews code\", \"prompt\": \"You are a code reviewer focused on performance\"}}' -p 'Use @reviewer to check auth.py'", timeout=120)
```

Claude can chain agents: "Use @db-expert to optimize queries, then @security to audit the changes."

## Hooks

Configure `.claude/settings.json` or `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf'; then echo 'Blocked!' && exit 2; fi"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "echo 'Claude finished a response' >> /tmp/claude-activity.log"}]
    }]
  }
}
```

| Hook | When | Use |
|---|---|---|
| `UserPromptSubmit` | Before user prompt processing | validation/logging |
| `PreToolUse` | Before tool | security gate; exit 2 blocks |
| `PostToolUse` | After tool | format/lint |
| `Notification` | Permission/input wait | notification |
| `Stop` | Response finished | completion log |
| `SubagentStop` | Subagent complete | orchestration |
| `PreCompact` | Before context cleared | backup transcript |
| `SessionStart` | Session begins | load context, e.g. `git status` |

Hook env: `CLAUDE_PROJECT_DIR` (project), `CLAUDE_FILE_PATHS` (modified files), `CLAUDE_TOOL_INPUT` (JSON params).

Security hook:

```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|git push.*--force|:(){ :|:& };:'; then echo 'Dangerous command blocked!' && exit 2; fi"}]
  }]
}
```

## MCP

```
# GitHub integration
terminal(command="claude mcp add -s user github -- npx @modelcontextprotocol/server-github", timeout=30)

# PostgreSQL queries
terminal(command="claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb", timeout=30)

# Puppeteer for web testing
terminal(command="claude mcp add puppeteer -- npx @anthropic-ai/server-puppeteer", timeout=30)
```

| Flag | Scope | Storage |
|---|---|---|
| `-s user` | Global | `~/.claude.json` |
| `-s local` | Project personal | `.claude/settings.local.json` (gitignored) |
| `-s project` | Project team | `.claude/settings.json` (git-tracked) |

Print/CI:

```
terminal(command="claude --bare -p 'Query database' --mcp-config mcp-servers.json --strict-mcp-config", timeout=60)
```

`--strict-mcp-config` ignores all servers except supplied config. Reference resources as `@github:issue://123`.

Limits/tuning: 2KB tool descriptions/server instructions per server; results default-capped, `maxResultSizeChars` up to **500K**; `export MAX_MCP_OUTPUT_TOKENS=50000`; transports `stdio`, `http`, `sse`.

## Monitoring + Context

```
# Periodic capture to check if Claude is still working or waiting for input
terminal(command="tmux capture-pane -t dev -p -S -10")
```

Indicators: `❯` = waiting; `●` = actively using tools; `⏵⏵ bypass permissions on`; `◐ medium · /effort`; `ctrl+o to expand` = truncated tool output. `/context`: <70% normal; 70–85% consider `/compact`; >85% high hallucination risk → `/compact` or `/clear`.

## Environment Variables

| Variable | Effect |
|---|---|
| `ANTHROPIC_API_KEY` | API-key auth instead of OAuth |
| `CLAUDE_CODE_EFFORT_LEVEL` | Default `low`, `medium`, `high`, `max`, `auto` |
| `MAX_THINKING_TOKENS` | Thinking cap; `0` disables |
| `MAX_MCP_OUTPUT_TOKENS` | MCP output cap, e.g. `50000` |
| `CLAUDE_CODE_NO_FLICKER=1` | Alt-screen rendering |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Strip credentials from subprocesses |

## Cost/Performance

1. set `--max-turns` (5–10 start)
2. set `--max-budget-usd`; minimum about `$0.05` for prompt-cache creation
3. `--effort low` simple; `high`/`max` complex
4. `--bare` CI startup
5. restrict `--allowedTools`
6. `/compact` large interactive context
7. pipe known input
8. `--model haiku` simple; `--model opus` complex
9. `--fallback-model haiku` overload
10. new sessions for distinct tasks; sessions last 5 hours
11. `--no-session-persistence` in CI

## Pitfalls

1. Interactive mode requires tmux; `pty=true` may work, but tmux enables `capture-pane`/`send-keys`.
2. Bypass dialog defaults to `No, exit`; send Down then Enter. Print mode skips it.
3. `--max-budget-usd` minimum ≈`$0.05`; lower errors immediately.
4. `--max-turns` only print mode.
5. Claude may use `python` instead of `python`; missing `python` symlink can fail first command before self-correction.
6. `--continue` requires same directory.
7. `--json-schema` needs enough turns to read files first.
8. Trust dialog appears once per directory.
9. Kill completed tmux sessions: `tmux kill-session -t <name>`.
10. Slash commands such as `/commit` are interactive-only; print mode needs natural-language instruction.
11. `--bare` skips OAuth; requires `ANTHROPIC_API_KEY` or `apiKeyHelper`.
12. Context quality degrades above 70%; monitor and compact.

## Hermes Rules

1. print mode for single tasks
2. tmux for multi-turn interactive work
3. always set `workdir`
4. set print `--max-turns`
5. monitor with `tmux capture-pane -t <session> -p -S -50`
6. `❯` means waiting/done/question
7. clean tmux sessions
8. summarize Claude's work and changed files
9. inspect slow sessions; don't kill blindly
10. restrict with `--allowedTools`

## Verification

- auth/version/health checked before delegation
- chosen mode matches interaction need; `workdir`, timeout, turns, permissions, and cost cap explicit
- print JSON/stream parsed or tmux pane inspected to a terminal state
- changes/tests/git diff reviewed before reporting completion; tmux cleanup recorded
