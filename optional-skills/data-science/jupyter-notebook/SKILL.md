---
name: jupyter-notebook
description: "Iterative Python via live Jupyter kernel (hamelnb)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [jupyter, notebook, repl, data-science, exploration, iterative]
    category: data-science
---

# Jupyter Notebook (hamelnb live kernel)

role: stateful Jupyter kernel operator
do: discover/start server; create session; execute incremental Python; inspect variables/cells; edit notebook; restart/run all when requested; diagnose transport/timeouts
inputs: notebook path, Python code, variable/cell name, server/port, timeout
outputs: persistent kernel state, structured JSON, edited notebook/outputs, verification result
¬: use for one-shot Hermes-tool scripts; omit `--compact`; assume kernel exists; put subcommand flags after sub-subcommand; expose auth-disabled server beyond localhost; treat websocket timeout as kernel failure without REST check

Use the hamelnb live-kernel script for a **stateful Python REPL**: variables, imports, and objects persist across executions. Prefer `execute_code` for stateless Hermes-tool scripts and `terminal` for shell/build/install/git/process work.

## When to Use

- iterative exploration, DataFrames, ML/API inspection
- “try this and check” workflows
- complex code built incrementally in a live notebook

| Tool | Use When |
|------|----------|
| **This skill** | Iterative exploration, state across steps, data science, ML, "let me try this and check" |
| `execute_code` | One-shot scripts needing hermes tool access (web_search, file ops). Stateless. |
| `terminal` | Shell commands, builds, installs, git, process management |

## Prerequisites

- `uv`: `which uv`
- JupyterLab: `uv tool install jupyterlab`
- running Jupyter server

```
SCRIPT="$HOME/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py"
```

Clone only when absent. The script path is the default shown above.

```
git clone https://github.com/hamelsmu/hamelnb.git ~/.agent-skills/hamelnb
```

## Procedure

### 1. Start/discover server

Prepare the notebook directory and discover existing servers:

```
mkdir -p ~/notebooks
```

```
uv run "$SCRIPT" servers
```

If no suitable loopback server exists, start one:

```
jupyter-lab --no-browser --port=8888 --notebook-dir=$HOME/notebooks \
  --IdentityProvider.token='' --ServerApp.password='' > /tmp/jupyter.log 2>&1 &
sleep 3
```

The headless server disables token/password for local agent access; keep it loopback-only. REST-only fresh server needs `--ServerApp.disable_check_xsrf=True` or POST `/api/sessions` fails with `'_xsrf' argument missing from POST`.

### 2. Create a scratch session

Create a minimal `scratch.ipynb` with one empty code cell, then:

```
curl -s -X POST http://127.0.0.1:8888/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"path":"scratch.ipynb","type":"notebook","name":"scratch.ipynb","kernel":{"name":"python"}}'
```

### 3. Discover and execute

All commands return JSON; always use `--compact`:

```
uv run "$SCRIPT" execute --path <notebook.ipynb> --code '<python code>' --compact
```

```
uv run "$SCRIPT" execute --path scratch.ipynb --code $'import os\nfiles = os.listdir(".")\nprint(f"Found {len(files)} files")' --compact
```

Kernel state persists. The kernel Python is JupyterLab's Python; install packages in that environment.

### 4. Inspect/edit

```
# View current cells
uv run "$SCRIPT" contents --path <notebook.ipynb> --compact

# Insert a new cell
uv run "$SCRIPT" edit --path <notebook.ipynb> insert \
  --at-index <N> --cell-type code --source '<code>' --compact

# Replace cell source (use cell-id from contents output)
uv run "$SCRIPT" edit --path <notebook.ipynb> replace-source \
  --cell-id <id> --source '<new code>' --compact

# Delete a cell
uv run "$SCRIPT" edit --path <notebook.ipynb> delete --cell-id <id> --compact
```

Inspect live variables without dumping full objects:

```
uv run "$SCRIPT" variables --path <notebook.ipynb> list --compact
uv run "$SCRIPT" variables --path <notebook.ipynb> preview --name <varname> --compact
```

Flags such as `--path` precede the sub-subcommand: `variables --path nb.ipynb list`.

### 5. Clean verification

Only when requested or needed to prove top-to-bottom execution:

```
uv run "$SCRIPT" restart-run-all --path <notebook.ipynb> --save-outputs --compact
```

```
uv run "$SCRIPT" servers --compact
uv run "$SCRIPT" notebooks --compact
```

## Timeout and Transport

- default per execution: 30s; long/heavy work: `--timeout 120` (initial setup/heavy compute: 60+)
- first execution after server start may timeout while kernel initializes; retry once
- occasional post-restart websocket timeout: retry once
- consistent message `Websocket execution may already have reached the kernel, so auto fallback was skipped` means REST can show `execution_state=idle` + incremented `execution_count` while reply channel is broken; use `--transport zmq`
- errors are JSON with traceback; inspect `ename`/`evalue`

## Pitfalls

- no live session → create via REST before execute
- `--compact` omission wastes tokens
- server's Python, not arbitrary shell Python, owns packages
- disabling token/password is acceptable only for loopback local server
- restart-run-all resets live state; do not use for routine incremental work

## Verification

- `servers --compact` finds active server and `notebooks --compact` finds target
- execute returns JSON and state survives a second call
- variables/contents reflect real kernel/notebook state
- JSON errors are read, not mistaken for success
- requested restart/run-all has saved outputs and top-to-bottom success
