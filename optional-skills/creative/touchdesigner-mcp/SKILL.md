---
name: touchdesigner-mcp
description: Control TouchDesigner via twozero MCP.
version: 1.1.0
author: kshitijk4poor
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [TouchDesigner, MCP, twozero, creative-coding, real-time-visuals, generative-art, audio-reactive, VJ, installation, GLSL]
    related_skills: [ascii-video, manim-video]

---

# TouchDesigner Integration (twozero MCP)

role: TouchDesigner/MCP operator
do: discover TD 2025.32 params/hints/network; build, wire, verify, display, record real-time visuals
inputs: network goal, OP types, GLSL/audio/media, local TouchDesigner + twozero.tox
outputs: working TD network, screenshots/video, explicit health/perf/errors
¬: guessed params; continued `tdAttributeError`; absolute callback paths; native-tool bypass; unverified black/zero-FPS output

## When to Use

- build, inspect, animate, audio-react, display, or record TouchDesigner networks through twozero MCP
- use for real-time visuals, VJ/installations, generative art, or GLSL/audio-reactive work

## Critical Rules

1. **NEVER guess parameter names.** Call `td_get_par_info` for the OP type FIRST. Training data is wrong for TD 2025.32.
2. **If `tdAttributeError` fires, STOP.** Call `td_get_operator_info` on the failing node before continuing.
3. **NEVER hardcode absolute paths** in script callbacks. Use `me.parent()` / `scriptOp.parent()`.
4. **Prefer native MCP tools over td_execute_python.** Use `td_create_operator`, `td_set_operator_pars`, `td_get_errors`, etc.; use `td_execute_python` only for complex multi-step logic.
5. **Call `td_get_hints` before building.** It returns OP-specific patterns.

## Architecture + Setup

```text
Hermes Agent -> MCP (Streamable HTTP) -> twozero.tox (port 40404) -> TD Python
```

36 native tools; free plugin, no payment/license (confirmed April 2026); context-aware (selected OP/current network). Health: `GET http://localhost:40404/mcp` returns JSON with instance PID, project name, TD version.

Automated setup, via `terminal`:

```bash
bash "${HERMES_HOME:-$HOME/.hermes}/skills/creative/touchdesigner-mcp/scripts/setup.sh"
```

Script: checks TD; downloads cached twozero.tox; adds `twozero_td` MCP server to Hermes config if missing; tests port 40404; reports manual steps.

One-time manual steps:

1. Drag `~/Downloads/twozero.tox` into TD network editor → click Install.
2. twozero icon → Settings → mcp → "auto start MCP" → Yes.
3. Restart Hermes session.

Verify:

```bash
nc -z 127.0.0.1 40404 && echo "twozero MCP: READY"
```

## Environment Notes

- Non-Commercial TD caps resolution at 1280×1280; use `outputresolution = 'custom'` with explicit width/height.
- codecs: `prores` (preferred macOS) or `mjpa`; H.264/H.265/AV1 require Commercial license
- always `td_get_par_info` before setting params

## Procedure

### 0. Discover

Before any build:

```
Call td_get_par_info with op_type for each type you plan to use.
Call td_get_hints with the topic you're building (e.g. "glsl", "audio reactive", "feedback").
Call td_get_focus to see where the user is and what's selected.
Call td_get_network to see what already exists.
```

No temp nodes/cleanup; this replaces the old discovery dance.

### 1. Clean + build

Cleanup and creation are **separate MCP calls**. Destroy/recreate same-named nodes in one `td_execute_python` script causes `Invalid OP object` errors.

```text
td_create_operator(type="noiseTOP", parent="/project1", name="bg", parameters={"resolutionw": 1280, "resolutionh": 720})
td_create_operator(type="levelTOP", parent="/project1", name="brightness")
td_create_operator(type="nullTOP", parent="/project1", name="out")
```

Bulk/wiring via `td_execute_python`:

```python
# td_execute_python script:
root = op('/project1')
nodes = []
for name, optype in [('bg', noiseTOP), ('fx', levelTOP), ('out', nullTOP)]:
    n = root.create(optype, name)
    nodes.append(n.path)
# Wire chain
for i in range(len(nodes)-1):
    op(nodes[i]).outputConnectors[0].connect(op(nodes[i+1]).inputConnectors[0])
result = {'created': nodes}
```

### 2. Set parameters

Native first:

```
td_set_operator_pars(path="/project1/bg", parameters={"roughness": 0.6, "monochrome": true})
```

Expressions/modes via script:

```python
op('/project1/time_driver').par.colorr.expr = "absTime.seconds % 1000.0"
```

### 3. Wire

No native wire tool; use `td_execute_python`:

```python
op('/project1/bg').outputConnectors[0].connect(op('/project1/fx').inputConnectors[0])
```

### 4. Verify

```
td_get_errors(path="/project1", recursive=true)
td_get_perf()
td_get_operator_info(path="/project1/out", detail="full")
```

### 5. Display/capture

```
td_get_screenshot(path="/project1/out")
```

Open a window:

```python
win = op('/project1').create(windowCOMP, 'display')
win.par.winop = op('/project1/out').path
win.par.winw = 1280; win.par.winh = 720
win.par.winopen.pulse()
```

## Native MCP Tool Reference

**Core:**

| Tool | What |
|------|------|
| `td_execute_python` | Arbitrary Python in TD; full API |
| `td_create_operator` | Create node with params + auto-positioning |
| `td_set_operator_pars` | Set params safely; validates |
| `td_get_operator_info` | One node: connections, params, errors |
| `td_get_operators_info` | Multiple nodes |
| `td_get_network` | Network structure |
| `td_get_errors` | Recursive errors/warnings |
| `td_get_par_info` | Param names for OP type |
| `td_get_hints` | Patterns/tips before building |
| `td_get_focus` | Open network/selection |

**Read/write:** `td_read_dat` (DAT text), `td_write_dat` (DAT text), `td_read_chop` (CHOP values), `td_read_textport` (console).

**Visual:** `td_get_screenshot`, `td_get_screenshots`, `td_get_screen_screenshot`, `td_navigate_to`.

**Search:** `td_find_op` (name/type), `td_search` (code/expressions/string params).

**System:** `td_get_perf`, `td_list_instances`, `td_get_docs`, `td_agents_md`, `td_reinit_extension`, `td_clear_textport`.

**Input:** `td_input_execute`, `td_input_status`, `td_input_clear`, `td_op_screen_rect`, `td_click_screen_point`, `td_screen_point_to_global`.

The table covers the 32 tools used in typical creative workflows. Remaining four (`td_project_quit`, `td_test_session`, `td_dev_log`, `td_clear_dev_log`) are admin/dev utilities; full 36-tool schemas: `references/mcp-tools.md`.

## Implementation Rules

**GLSL time:** no `uTDCurrentTime` in GLSL TOP. Query params, then Values page:

```python
# Call td_get_par_info(op_type="glslTOP") first to confirm param names
td_set_operator_pars(path="/project1/shader", parameters={"value0name": "uTime"})
# Then set expression via script:
# op('/project1/shader').par.value0.expr = "absTime.seconds"
# In GLSL: uniform float uTime;
```

Fallback = Constant TOP `rgba32float`; 8-bit clamps 0–1 and freezes shader.

Feedback TOP: `top` parameter reference, not direct input wire; "Not enough sources" resolves after first cook; "Cook dependency loop" warning is expected.

Resolution = `outputresolution = 'custom'`; large shaders can be written to `/tmp/file.glsl`, then loaded with `td_write_dat`/`td_execute_python`.

TD 2025.32 point access: `point.P[0]`, `point.P[1]`, `point.P[2]`, not `.x/.y/.z`.

Extensions: `ext0object` format `"op('./datName').module.ClassName(me)"` in CONSTANT mode; after `td_write_dat`, call `td_reinit_extension`.

Callbacks: `me.parent()`/`scriptOp.parent()` only. Cleaning: `list(root.children)` before iterating + `child.valid` check.

## Recording + Export

```python
# via td_execute_python:
root = op('/project1')
rec = root.create(moviefileoutTOP, 'recorder')
op('/project1/out').outputConnectors[0].connect(rec.inputConnectors[0])
rec.par.type = 'movie'
rec.par.file = '/tmp/output.mov'
rec.par.videocodec = 'prores'  # Apple ProRes — NOT license-restricted on macOS
rec.par.record = True   # start
# rec.par.record = False  # stop (call separately later)
```

H.264/H.265/AV1 need Commercial license; use `prores` macOS or `mjpa`. Frames:

```bash
ffmpeg -i /tmp/output.mov -vframes 120 /tmp/frames/frame_%06d.png
```

`TOP.save()` is useless for animation; MovieFileOut is required.

Before recording: (1) `td_get_perf`, FPS > 0; (2) `td_get_screenshot`, output not black; (3) audio cue first, delay recording 3 frames; (4) set output path before starting record, separate calls to avoid race.

## Audio-Reactive GLSL

```text
AudioFileIn CHOP (playmode=sequential)
  → AudioSpectrum CHOP (FFT=512, outputmenu=setmanually, outlength=256, timeslice=ON)
  → Math CHOP (gain=10)
  → CHOP to TOP (dataformat=r, layout=rowscropped)
  → GLSL TOP input 1 (spectrum texture, 256x2)

Constant TOP (rgba32float, time) → GLSL TOP input 0
GLSL TOP → Null TOP → MovieFileOut
```

Rules: AudioSpectrum `TimeSlice` ON; `outputmenu='setmanually'`, `outlength=256`; never Lag/Filter CHOP (timeslice expansion makes values ~`1e-06`); smooth in GLSL via `mix(prevValue, newValue, 0.3)`; CHOP to TOP `dataformat = 'r'`, `layout = 'rowscropped'`, 256x2 stereo and y=0.25 first channel; Math gain 10 (raw bass ~0.19); no Resample CHOP.

```glsl
// Input 0 = time (1x1 rgba32float), Input 1 = spectrum (256x2)
float iTime = texture(sTD2DInputs[0], vec2(0.5)).r;

// Sample multiple points per band and average for stability:
// NOTE: y=0.25 for first channel (stereo texture is 256x2, first row center is 0.25)
float bass = (texture(sTD2DInputs[1], vec2(0.02, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.05, 0.25)).r) / 2.0;
float mid  = (texture(sTD2DInputs[1], vec2(0.2, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.35, 0.25)).r) / 2.0;
float hi   = (texture(sTD2DInputs[1], vec2(0.6, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.8, 0.25)).r) / 2.0;
```

Complete build scripts/shader: `references/network-patterns.md`.

## Operator Families

| Family | Color | Python class / MCP type | Suffix |
|--------|-------|-------------|--------|
| TOP | Purple | noiseTOP, glslTOP, compositeTOP, levelTop, blurTOP, textTOP, nullTOP | TOP |
| CHOP | Green | audiofileinCHOP, audiospectrumCHOP, mathCHOP, lfoCHOP, constantCHOP | CHOP |
| SOP | Blue | gridSOP, sphereSOP, transformSOP, noiseSOP | SOP |
| DAT | White | textDAT, tableDAT, scriptDAT, webserverDAT | DAT |
| MAT | Yellow | phongMAT, pbrMAT, glslMAT, constMAT | MAT |
| COMP | Gray | geometryCOMP, containerCOMP, cameraCOMP, lightCOMP, windowCOMP | COMP |

## Security

- MCP localhost only, port 40404, no authentication: any local process can send commands.
- `td_execute_python` unrestricted in TD Python/filesystem as TD process user.
- `setup.sh` downloads twozero.tox from official 404zero.com; verify if concerned.
- skill sends no data outside localhost; MCP communication local.

## References

| File | Scope |
|---|---|
| `references/pitfalls.md` | Hard-won lessons from real sessions |
| `references/operators.md` | Operator families, params, and use cases |
| `references/network-patterns.md` | Audio-reactive, generative, GLSL, and instancing recipes |
| `references/mcp-tools.md` | Complete twozero MCP schemas |
| `references/python-api.md` | TD Python: `op()`, scripting, extensions |
| `references/troubleshooting.md` | Connection diagnostics and debugging |
| `references/glsl.md` | Uniforms, built-ins, and shader templates |
| `references/postfx.md` | Bloom, CRT, chromatic aberration, feedback glow |
| `references/layout-compositor.md` | HUD, panel grids, BSP-style layouts |
| `references/operator-tips.md` | Wireframe and feedback TOP setup |
| `references/geometry-comp.md` | Instancing, POP vs SOP, morphing |
| `references/audio-reactive.md` | Bands, beats, envelope following |
| `references/animation.md` | LFOs, timers, keyframes, easing, expressions |
| `references/midi-osc.md` | MIDI/OSC, TouchOSC, multi-machine sync |
| `references/particles.md` | POPs and particleSOP emission/forces/collisions |
| `references/projection-mapping.md` | Multi-window output, corner pin, mesh warp, edge blending |
| `references/external-data.md` | HTTP, WebSocket, MQTT, Serial, TCP, webserverDAT |
| `references/panel-ui.md` | Custom params, panel COMPs, controls, panelExecuteDAT |
| `references/replicator.md` | replicatorCOMP cloning, layouts, callbacks |
| `references/dat-scripting.md` | Execute DAT family |
| `references/3d-scene.md` | Lighting, shadows, IBL/cubemaps, cameras, PBR |
| `scripts/setup.sh` | Automated twozero setup |

> You're not writing code. You're conducting light.

## Pitfalls

- localhost MCP has no authentication; keep port 40404 private and treat `td_execute_python` as unrestricted code execution
- inspect operator info and parameter hints before setting values; do not guess names, types, or network paths
- verify cleanup, FPS, non-black output, audio length, and recording codec before reporting success

## Verification

- setup/port health verified; manual tox install/toggle/restart acknowledged
- every OP type had `td_get_par_info`; hints/focus/network inspected first
- cleanup/build/set/wire calls separated and native tools preferred
- errors, perf, full operator info, screenshot all checked
- FPS > 0, output non-black, recording path/codec/license valid
- audio chain uses timeslice/output length/dataformat rules; output opens and is playable
