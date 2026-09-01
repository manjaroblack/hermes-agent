---
name: openhands
description: Delegate coding to OpenHands CLI (model-agnostic, LiteLLM).
version: 0.1.0
author: Tim Koepsel (xzessmedia), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Coding-Agent, OpenHands, Model-Agnostic, LiteLLM]
    related_skills: [claude-code, codex, opencode, hermes-agent]
---

# OpenHands CLI

role: OpenHands headless delegation operator
do: install/verify; select LiteLLM model; set env; run JSONL task; resume conversation; inspect events; report outcome
inputs: task prompt or file, project workdir, LiteLLM model/API/base URL, optional conversation ID
outputs: JSONL events, changed workspace, resumable conversation, verified finish message
¬: use interactive UI from Hermes; omit `--override-with-envs`; guess unsupported flags; parse banner/stderr as JSON; expose API keys

Delegate batch or one-shot coding to [OpenHands CLI](https://github.com/All-Hands-AI/OpenHands) through `terminal`. It is model-agnostic through LiteLLM (OpenAI, Anthropic, OpenRouter, DeepSeek, Ollama, vLLM, and others). This skill uses headless mode; Hermes does not drive the interactive textual UI.

## When to Use

- user requests OpenHands specifically
- multi-step file edits and shell commands in a workspace
- non-Anthropic/non-OpenAI model routing through LiteLLM

For Claude-native work prefer `claude-code`; for OpenAI-native work prefer `codex`; for Hermes-native subagents use `delegate_task`.

## Prerequisites

1. Python 3.12+ and `uv`:

   ```python
   terminal(command="uv tool install openhands --python 3.12")
   ```

   Verify with `openhands --version` (CLI 1.16.0 / SDK v1.21.0 at time of writing).
2. Model environment for `--override-with-envs`:

   ```bash
   export LLM_MODEL=openrouter/openai/gpt-4o-mini
   export LLM_API_KEY=$OPENROUTER_API_KEY
   export LLM_BASE_URL=https://openrouter.ai/api/v1
   ```

   LiteLLM forms: OpenRouter `openrouter/<vendor>/<model>` (e.g. `openrouter/anthropic/claude-sonnet-4.5`); native Anthropic `anthropic/claude-sonnet-4-5`; native OpenAI `openai/gpt-4o-mini`.
3. Suppress the banner for machine output:

   ```bash
   export OPENHANDS_SUPPRESS_BANNER=1
   ```

## Procedure

### One-shot

Always use `--headless --json --override-with-envs --exit-without-confirmation`:

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Add error handling to all API calls in src/'",
  workdir="/path/to/project",
  timeout=600
)
```

### Background

```
terminal(command="<same as above>", workdir="/path/to/project", background=true, notify_on_complete=true)
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")
```

### Resume

Each run prints an undashed `Conversation ID: <32-hex>` plus a dashed `Hint: openhands --resume <dashed-uuid>`. Resume with the dashed ID:

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=... openhands --headless --json --override-with-envs --exit-without-confirmation --resume <dashed-uuid> -t 'Now fix the bug you found'",
  workdir="/path/to/project"
)
```

## Supported Flags

Verified against OpenHands CLI 1.16.0; anything absent here is not a CLI flag.

| Flag | Effect |
|------|--------|
| `--headless` | No UI, requires `-t` or `-f`. Auto-approves all actions (no `--llm-approve` in this mode). |
| `--json` | JSONL event stream (requires `--headless`). |
| `-t TEXT` | Task prompt. |
| `-f PATH` | Read task from file. |
| `--resume [ID]` | Resume conversation. No ID → list recent. |
| `--last` | Resume most recent (with `--resume`). |
| `--override-with-envs` | Apply `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` env vars. Without this, OpenHands uses `~/.openhands/settings.json` and ignores the env. |
| `--exit-without-confirmation` | Don't show the "are you sure" exit dialog. |
| `--always-approve` / `--yolo` | Auto-approve every action (default in `--headless`). |
| `--llm-approve` | LLM-based security gate (interactive only — does NOT work in headless). |
| `--version` / `-v` | Print version and exit. |

No `--model`, `--max-iterations`, `--workspace`, `--sandbox`, or `--sandbox-type` flags. Model=`LLM_MODEL`; workspace=`terminal` `workdir`; sandbox/runtime=`RUNTIME` and `SANDBOX_VOLUMES`.

## JSON Event Schema

`--json --headless` emits JSONL plus non-JSON status/banner lines (`Initializing agent...`, `Agent is working`, `Agent finished`, final summary, `Goodbye!`, `Conversation ID:`, `Hint:`). Parse stdout line-by-line and keep lines beginning with `{`; LiteLLM/Authlib warnings go to stderr.

- `MessageEvent`: user/agent text; `source`=`user` or `agent`.
- `ActionEvent`: selected tool; inspect `tool_name` (`file_editor`, `terminal`, `finish`) and `action.kind` (`FileEditorAction`, `TerminalAction`, `FinishAction`).
- `ObservationEvent`: tool result; `observation.is_error` is the success flag; `source`=`environment`.
- `FinishAction`: final text in `action.message`.

## Pitfalls

- stderr may print `bedrock-runtime`, `sagemaker-runtime`, and Authlib warnings; noise, not necessarily failure. Filter only when presenting results.
- `OPENHANDS_SUPPRESS_BANNER=1` avoids ASCII banner pollution.
- Without `--override-with-envs`, env model/key/base URL are ignored and `~/.openhands/settings.json` may trigger first-run setup/hang.
- LiteLLM slug must match the endpoint: OpenRouter uses `openrouter/openai/gpt-4o-mini`; native Anthropic uses `anthropic/claude-sonnet-4-5`; wrong slug can yield a cryptic 400.
- `pip install openhands-ai` is the legacy V0 SDK; use `uv tool install openhands --python 3.12`; no maintained conda package.
- Resume with the dashed ID from the final hint, not the undashed display ID.
- Headless ignores `--llm-approve`; passing it causes argparse failure.
- Windows requires WSL upstream; frontmatter is gated `[linux, macos]`.
- `~/.openhands/conversations/<id>/` grows per run; clean it after batches.
- `uv tool install` isolates the roughly 200-package install from the project.

## Verification

```
terminal(
  command="OPENHANDS_SUPPRESS_BANNER=1 LLM_MODEL=openrouter/openai/gpt-4o-mini LLM_API_KEY=$OPENROUTER_API_KEY LLM_BASE_URL=https://openrouter.ai/api/v1 openhands --headless --json --override-with-envs --exit-without-confirmation -t 'Print the string OPENHANDS_OK to stdout via the terminal tool.'",
  workdir="/tmp",
  timeout=120
)
```

Working output is JSONL ending in a `FinishAction` whose `action.message` mentions `OPENHANDS_OK`.

## Related

- [OpenHands GitHub](https://github.com/All-Hands-AI/OpenHands)
- [OpenHands CLI command reference](https://docs.openhands.dev/openhands/usage/cli/command-reference)
- sibling skills: `claude-code`, `codex`, `opencode`, `hermes-agent`
