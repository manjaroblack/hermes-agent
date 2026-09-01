---
name: node-inspect-debugger
description: "Debug Node.js via --inspect + Chrome DevTools Protocol CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, nodejs, node-inspect, cdp, breakpoints, ui-tui]
    related_skills: [systematic-debugging, python-debugpy]
---

# Node.js Inspect Debugger

role: Node/V8 inspector operator
do: launch/attach `node inspect`; set breakpoints; step; inspect stack/scopes/expressions; automate CDP; capture heap/CPU profiles; debug Hermes UI/tests
inputs: Node script/process PID or inspector URL, source/line/function, optional TypeScript/tsx target
outputs: paused-frame values, call stacks, breakpoint results, profile/heap artifacts
¬: expose inspector beyond localhost; attach wrong process; assume TS lines map to emitted JS; leave paused targets/debug artifacts; use heavy debugger for a one-minute log problem

Use Node's built-in V8 inspector from terminal for real breakpoints, stepping,
call-stack/scope inspection, and expression evaluation. `node inspect` is zero
install and preferred for quick work; `ndb`/CDP via `chrome-remote-interface`
suits scripted or non-interactive sessions.

## When to Use

- Node test intermediate state or async call path needs inspection
- `ui-tui` Ink crashes/behaves incorrectly
- `tui_gateway` child/UI Node portions misbehave
- closure/local value is inaccessible to logging
- attach for CPU profile or heap snapshot

Don't use when `console.log` solves it in under a minute.

## Prerequisites

- Node.js; `tsx` when debugging TypeScript
- optional `chrome-remote-interface` (not in `ui-tui/package.json`)
- Hermes `terminal` with PTY/background `process` for interactive REPL

## Procedure

### 1. Start `node inspect`

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

`debug>` commands:

| Command | Action |
|---|---|
| `c` or `cont` | continue |
| `n` or `next` | step over |
| `s` or `step` | step into |
| `o` or `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint at file.js line 42 |
| `sb(42)` | set breakpoint at line 42 of current file |
| `sb('functionName')` | break when function is called |
| `cb('file.js', 42)` | clear breakpoint |
| `breakpoints` | list all breakpoints |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 lines of source around current position |
| `watch('expr')` | evaluate expr on every pause |
| `watchers` | show watched expressions |
| `repl` | drop into REPL in current scope (Ctrl+C to exit REPL) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill the script |
| `.exit` | quit debugger |

In `repl`, any JS expression can access locals/closure variables; Ctrl+C returns
to `debug>`.

### 2. Attach to a running process

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

Start with inspector from launch:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

TypeScript:

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

### 3. Script CDP

Install dependency and start target:

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

Save driver as `/tmp/cdp-debug.js`:

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    // Evaluate an expression in the paused frame
    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  // Set a breakpoint by URL regex + line
  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,       // 0-indexed
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

```bash
node /tmp/cdp-debug.js
```

Keep project clean with throwaway install:

```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js
```

### 4. Debug Hermes `ui-tui`

Single Ink component:

```bash
cd <hermes-agent-repo>/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

Then:

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

At pause, `repl` can inspect `props`, state refs, `useInput` values.

Running `hermes --tui`:

```bash
# 1. Launch TUI
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)

# 2. Enable inspector on that Node PID
kill -SIGUSR1 "$TUI_PID"

# 3. Find the WS URL
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'

# 4. Attach
node inspect ws://127.0.0.1:9229/<uuid>
```

Typing in the TUI continues execution; breakpoints pause it. `_SlashWorker` and
PTY workers are Python → use `python-debugpy`; only Ink, TUI client, and tsx-run
tests use this skill.

### 5. Debug Vitest

```bash
cd <hermes-agent-repo>/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

Attach, set `sb('src/app/foo.tsx', 42)`, `cont`. Use
`--no-file-parallelism` (vitest) or `--runInBand` (jest); one worker is
inspectable.

### 6. Capture heap/CPU

From CDP driver, swap `Debugger` for `HeapProfiler`/`Profiler`:

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
// Open /tmp/cpu.cpuprofile in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Pitfalls

- TS breakpoints target emitted JS; use `dist/*.js`, or sourcemaps with a CDP
  client; `node inspect` CLI does not follow sourcemaps
- `--inspect` does not pause; late attach can miss breakpoints; use `--inspect-brk`
- default port 9229 collides; use `--inspect=0` and inspect `/json/list`
- parent inspector does not inspect children; `NODE_OPTIONS='--inspect-brk'` can
  propagate, but children need unique ports (auto-increment with `--inspect`)
- Ctrl+C while target paused leaves it paused; `cont` or kill target
- interactive `node inspect` needs `terminal(pty=true)` or background `process`
- `--inspect=0.0.0.0:9229` exposes arbitrary code execution; bind localhost
- chrome-remote-interface is not a project dependency; install throwaway

## Verification Checklist

- [ ] `/json/list` returns the intended target
- [ ] first breakpoint hits; otherwise check `--inspect-brk`/attach timing
- [ ] paused source file is correct; mismatch indicates sourcemap issue
- [ ] `exec process.pid`/`repl` confirms intended PID
- [ ] profiles saved only where intended; target resumed/terminated

## One-Shot Recipes

**"Why is this variable undefined at line X?"**

```bash
node --inspect-brk script.js &
node inspect -p $!
# debug>
sb('script.js', X)
cont
# paused. Now:
repl
> myVariable
> Object.keys(this)
```

**"What's the call path into this function?"**

```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**"This async chain hangs — where?"**

```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```
