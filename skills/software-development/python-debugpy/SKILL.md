---
name: python-debugpy
description: "Debug Python: pdb REPL + debugpy remote (DAP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [debugging, python, pdb, debugpy, breakpoints, dap, post-mortem]
    related_skills: [systematic-debugging, node-inspect-debugger]
---

# Python Debugger (pdb + debugpy)

role: Python debugger operator
do: choose pdb/debugpy; set breakpoints; step/inspect scopes/stacks; post-mortem; attach to processes/children; verify cleanup
inputs: script/test/process/PID, failing line/function, local/remote environment, debug port
outputs: paused-frame values, stack/locals, breakpoint evidence, DAP session or post-mortem findings
¬: debug through captured parallel runner; expose debugpy beyond localhost; leave `breakpoint()`/`set_trace()`; change code while diagnosing; assume `listen()` waits without `wait_for_client()`

Choose:

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add `breakpoint()` in source, run normally, get a REPL at that line. |
| **`python -m pdb`** | Existing script without source edits; quick inspection. |
| **`debugpy`** | Remote/headless/attach-to-running process; DAP scripting; long-lived gateway/daemon/PTY children. |

Start with `breakpoint()`; it is the cheapest working path.

## When to Use

- test traceback does not explain a wrong value
- step through mutation or a function
- long-running `hermes` gateway/`tui_gateway` cannot be cleanly restarted
- post-mortem exception locals
- Python `_SlashWorker` or PTY child is the bug site

Don't use when `print()`/`logging.debug` or `pytest -vv --tb=long --showlocals`
solves it in under a minute.

## Prerequisites

- Python 3; `debugpy` installed for remote paths
- single-process PTY for interactive pdb
- localhost debug port, PID, and source paths for attach
- Hermes `terminal`/`process` or an IDE DAP client as needed

## pdb Quick Reference

Inside `(Pdb)`:

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `j N` | jump to line N (same function only) |
| `l` / `ll` | list source around current line / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up / down in the stack |
| `a` | print args of the current function |
| `p expr` / `pp expr` | print / pretty-print expression |
| `display expr` | auto-print expr on every stop |
| `b file:line` | set breakpoint |
| `b func` | break on function entry |
| `b file:line, cond` | conditional breakpoint |
| `cl N` | clear breakpoint N |
| `tbreak file:line` | one-shot breakpoint |
| `!stmt` | execute arbitrary Python (assignments included) |
| `interact` | drop into full Python REPL in current scope (Ctrl+D to exit) |
| `q` | quit |

`interact` can import/call/mutate; locals are read-only by default, `!x = 42`
mutates from `(Pdb)`.

## Procedure

### 1. Local breakpoint

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Run normally; inspect locals at `breakpoint()`. Remove before commit:

```bash
rg -n 'breakpoint\(\)' --type py
```

### 2. Script under pdb (no source edit)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```

### 3. Pytest debugging

```bash
# Drop to pdb on failure (or on any raised exception):
scripts/run_tests.sh tests/path/to/test_file.py::test_name --pdb

# Drop to pdb at the START of the test:
scripts/run_tests.sh tests/path/to/test_file.py::test_name --trace

# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

`scripts/run_tests.sh` captures each file in a subprocess; interactive pdb does
not work under it. For interactive debugging only:

```bash
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

Raw pytest bypasses hermetic env; re-run wrapper before pushing.

### 4. Post-mortem

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Global hook:

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```

### 5. Remote debug with debugpy

Use for gateway, `tui_gateway`, daemons, or processes already misbehaving.

#### Setup

```bash
source <hermes-agent-repo>/.venv/bin/activate
pip install debugpy
```

#### Pattern A: source edit, wait at launch

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

#### Pattern B: no source edit

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

#### Pattern C: attach to running PID

```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Ptrace injection may be blocked by `/proc/sys/kernel/yama/ptrace_scope`:

```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

#### Terminal DAP client

Option 1, small one-off client:

```python
# /tmp/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

Option 2, attach with VS Code/Cursor/Zed:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "<hermes-agent-repo>" }
  ]
}
```

Option 3, terminal-friendly `remote-pdb`:

```bash
pip install remote-pdb
```

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

`remote-pdb` is preferable when DAP/IDE integration is unnecessary.

### 6. Hermes-specific processes

- tests: wrapper captures output; raw pytest for interactive pdb
- `run_agent.py`/CLI: add `breakpoint()` near suspect line; run `hermes`
- `tui_gateway` source edit:

  ```python
  # tui_gateway/server.py near the top of serve()
  import debugpy
  debugpy.listen(("127.0.0.1", 5678))
  debugpy.wait_for_client()
  ```

  `hermes --tui` appears frozen until attach/continue.
- `_SlashWorker`: `remote-pdb` in worker `exec`; persistent worker blocks first
  trigger, then later commands pass unless re-armed
- gateway: `remote-pdb` handler, or `debugpy --wait-for-client` on restart

## Pitfalls

- pdb under parallel/output-capturing runner hides prompt/hangs; use one-file raw pytest
- `breakpoint()` in CI/non-TTY hangs; never commit; pre-commit scan
- `PYTHONBREAKPOINT=0` disables breakpoints:

  ```bash
  echo $PYTHONBREAKPOINT
  ```

- `debugpy.listen` alone does not wait; add `wait_for_client()`
- hardened kernel/PID attach: `ptrace_scope=1`; use root workaround or launch under debugpy
- pdb debugs current thread only; use debugpy or `threading.settrace()` for threads
- asyncio `await` in pdb differs by Python version; Python 3.11/3.12 use
  `asyncio.run_coroutine_threadsafe` or `!stmt` + `asyncio.ensure_future`
- wrapper strips credentials and sets temporary HOME; raw debug to reproduce then wrapper verify
- pdb does not follow forks; each child needs breakpoint/set_trace; debug one process at a time

## Verification Checklist

- [ ] `python -c "import debugpy; print(debugpy.__version__)"` succeeds after install
- [ ] remote port listening: `ss -tlnp | grep 5678`
- [ ] first breakpoint hits; if not, check env/runner/attach timing
- [ ] `w`/`where` shows expected stack
- [ ] no debug calls remain:

  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```

## One-Shot Recipes

**"Why is this dict missing a key?"**

```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**"This test passes in isolation but fails in the suite."**

```bash
scripts/run_tests.sh tests/the_test.py   # confirm it fails under the isolated runner first
# For interactive debugging, or if it only fails WITH other tests:
source .venv/bin/activate
python -m pytest tests/ -x --pdb
# Now it pdb-traps at the exact failing test after state accumulated.
```

**"My async handler deadlocks."**

```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```

Trigger; `nc 127.0.0.1 4444`; then `w` and
`!import asyncio; asyncio.all_tasks()`.

**"Post-mortem on a crash in an Ink child process / subprocess."**

```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```
