---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

[OpenCode](https://opencode.ai) is the provider-agnostic coding worker covered here.

role: Hermes orchestrator for provider-agnostic OpenCode
do: run bounded or iterative coding/review jobs through terminal/process; isolate parallel work
inputs: OpenCode install/auth; repo/workdir; task prompt
outputs: code/review results, files, tests, session IDs
¬: `/exit` in OpenCode TUI; shared workdirs; assume shell and Hermes resolve same binary

## When to Use

- user explicitly requests OpenCode
- external agent should implement/refactor/review
- long-running progress-monitored or parallel isolated work

## Prerequisites

- install: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- auth: `opencode auth login` or provider env vars such as `OPENROUTER_API_KEY`
- verify: `opencode auth list` shows at least one provider
- git repo recommended for code tasks
- `pty=true` for interactive TUI; `opencode run` does not need PTY

## Binary Resolution

Shell and Hermes may choose different binaries/configs:

```text
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

Pin an explicit path if needed:

```text
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## One-Shot

```text
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach files:

```text
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Thinking output:

```text
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Force model:

```text
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Background

```text
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

Do not use `/exit`; OpenCode treats it as an agent-selector dialog, not exit.

### TUI Keys

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resume

After exit, use the printed ID:

```text
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue last session |
| `--session <id>` / `-s` | Continue specific session |
| `--agent <name>` | Choose build or plan agent |
| `--model provider/model` | Force model |
| `--format json` | Machine-readable output/events |
| `--file <path>` / `-f` | Attach file(s) |
| `--thinking` | Show thinking blocks |
| `--variant <level>` | Reasoning effort: high, max, minimal |
| `--title <name>` | Name session |
| `--attach <url>` | Attach to running OpenCode server |

## Procedure

1. `terminal(command="opencode --version")`; `terminal(command="opencode auth list")`.
2. Bounded → `opencode run '...'`; iterative → background `opencode` with PTY.
3. Monitor with `process(action="poll"|"log")`; answer via `process(action="submit", ...)`; exit with `process(action="write", data="\x03")` or `process(action="kill")`.
4. Review files/tests and summarize concrete results.

## PR Review

Built-in:

```text
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Isolated clone:

```text
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work

Use separate workdirs/worktrees:

```text
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Session / Cost

```text
terminal(command="opencode session list")
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Pitfalls

- interactive TUI needs `pty=true`; `run` does not
- `/exit` is invalid; Ctrl+C or kill
- PATH mismatch can select another binary/model config
- inspect `process(action="log", session_id="<id>")` before killing a stuck session
- no shared workdir across parallel sessions
- Enter may need two presses

## Verification

```text
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Pass iff output includes `OPENCODE_SMOKE_OK`, command exits without provider/model errors, and code tasks have expected files + passing tests.

## Rules

1. Prefer `opencode run` for one-shot automation.
2. Use interactive background mode only for iteration.
3. Scope every session to one repo/workdir.
4. Report progress for long tasks; report files, tests, and risks.
5. Exit interactive sessions Ctrl+C/kill, never `/exit`.
