---
name: unreal-mcp
description: Automate Unreal Engine editor scenes, actors, and renders.
version: 1.0.0
requires: Unreal Editor 5.8+ with the Unreal MCP plugin enabled and its server running
author: Hermes Agent
license: MIT
tags: [unreal, unreal-engine, ue5, 3d, mcp, scenes, cinematics, lighting, gamedev]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [unreal, unreal-engine, ue5, 3d, mcp, scenes, cinematics, lighting, gamedev]
    related_skills: []
---

# Unreal Engine MCP Skill

role: Unreal live-editor technical/art director
do: start/configure editor MCP; discover live toolsets; inspect scene; sequence serial calls; build/save; capture/analyze; report paths and state
inputs: Unreal project/brief, editor state, target scene/actors/materials/camera/render, tool schemas
outputs: saved level/actors/materials/camera, screenshots/renders, queried state, concrete report
¬: use stale tool schemas; batch overlapping MCP calls; assume empty scene; expose localhost server; ignore failed result bodies; leave unsaved/modal state; claim success without visual/structural verification

Companion for the `unreal-engine` Hermes MCP catalog entry. Epic's experimental Unreal MCP plugin (`ModelContextProtocol`) runs inside Unreal Editor and exposes typed tools. This skill covers discovery, safe sequencing, scene craft, and visual verification; the user only needs to launch the editor.

## When to Use

- build/dress a level; spawn/move/delete actors
- lighting, atmosphere, materials, cameras, cinematics, screenshots/renders
- import/place assets; inspect scene/UI; automation tests; editor scripting

Do not use for DCC mesh modeling/sculpting (use Blender then import) or Unreal C++ project source (normal terminal code work).

## Prerequisites

### Editor side, once

1. Unreal Editor **5.8+**, project open. macOS needs full Xcode + accepted license; otherwise first launch exits.
2. Edit > Plugins → enable **Unreal MCP**; Toolset Registry dependency auto-enables; restart if prompted.
3. Also enable **AllToolsets**. Unreal MCP supplies no tools itself; AllToolsets supplies SceneTools, ActorTools, MaterialInstanceTools, ObjectTools, etc.
4. Edit > Editor Preferences > General > Model Context Protocol → enable **Auto Start Server**. Default `http://127.0.0.1:8000/mcp`; port/path configurable; name=`unreal-mcp`. Manual start: `ModelContextProtocol.StartServer` in editor console (backtick).

### Hermes side, once

```bash
hermes mcp install unreal-engine
```

This writes `mcp_servers.unreal-engine` HTTP config for `http://127.0.0.1:8000/mcp` and probes the live server. Run while editor/server are up. If port/path changed, update `url` under `mcp_servers.unreal-engine` in `~/.hermes/config.yaml`.

Do not use `ModelContextProtocol.GenerateClientConfig` for Hermes; it writes `.mcp.json` files for other clients.

### Every session

1. Launch editor, wait for project load, confirm Output Log bind or run `ModelContextProtocol.StartServer`.
2. Start Hermes; tools appear as `mcp_unreal_engine_*`. Missing tools → correct start order, then new Hermes session.
3. Call `mcp_unreal_engine_list_toolsets` and confirm output.

## Tool Surface: Discover, Never Guess

Default **tool-search mode** advertises three meta-tools:

| Hermes tool | Purpose |
|---|---|
| `mcp_unreal_engine_list_toolsets` | Names + descriptions of every registered toolset |
| `mcp_unreal_engine_describe_toolset` | Full JSON schemas for one named toolset's tools |
| `mcp_unreal_engine_call_tool` | Invoke a named tool with arguments, get the result |

Discovery order:

1. `list_toolsets` → project-dependent capability groups; use fully qualified names verbatim, e.g. `editor_toolset.toolsets.scene.SceneTools`, `EditorToolset.EditorAppToolset`.
2. `describe_toolset` for needed group; schemas are contract, never guess params.
3. `call_tool` with qualified `toolset_name`, short tool name (`find_actors`, not dotted), schema-matching args.

Cache for the session; re-list only after plugin/toolset changes or `RefreshTools`.

Alternative eager mode (Editor Preferences → `Enable Tool Search` off) exposes each tool as `mcp_unreal_engine_<tool>` and discovers at install/config time. Tool-search is default and keeps schemas out of every call.

Full toolset/plugin config: `references/tool-surface.md`.

## Procedure

Execute the operating loop below for every live-editor change.

## Operating Loop

1. **Inspect first.** List toolsets; query level/scene state before edits. In unfamiliar projects check project Agent Skills with `call_tool` → `AgentSkillToolset.ListSkills`; matching project skill overrides generic defaults.
2. **One logical step/call.** Tools run serially on the game thread. For 5+ homogeneous operations, one `ProgrammaticToolset.execute_tool_script` may batch server-side; see `references/advanced-workflows.md`.
3. **Never overlap MCP calls.** Do not batch multiple `mcp_unreal_engine_*` calls in one turn; Hermes concurrency can deadlock/fail the game thread. Await each result.
4. **Read every result.** Tool failures may be in response body without protocol exception. Anything not explicit success → stop/diagnose. Read values back after writes; some paths silently no-op.
5. **Verify each milestone.** Re-query changed actors/properties; capture viewport screenshot when composition matters; inspect with `vision_analyze`.
6. **Save often.** Edits are in-memory; MCP edits may not undo reliably. Save before/after bulk changes and every milestone.
7. **Report concrete facts.** Actor labels, `/Game/...` asset paths, capture/render file locations.

### World conventions

- units=centimeters; Z-up; X-forward; rotations=degrees (Roll X, Pitch Y, Yaw Z)
- human eye≈165cm; door≈210×90cm; numeric craft tables=`references/scene-craft.md`
- package paths: `/Game/Folder/Asset.Asset`; engine primitives: `/Engine/BasicShapes/Cube.Cube`
- actor labels are visible/non-unique; actor names are internal/unique; resolve by label/class then keep returned handle
- read existing sun intensity before choosing lux/candela/Kelvin; template worlds can be calibrated around `intensity: 10`; physical values may blow them out; see `references/scene-craft.md` and `references/pitfalls.md` #12b

## Plain English → Scene

1. Extract subject, mood, time, interior/exterior, style, deliverable. Ask at most one clarification round; do not bounce Unreal jargon back.
2. Plan: environment shell → major blocking → lighting/atmosphere → materials → detail → camera → capture/render. Use a todo list for multi-step builds.
3. Execute one milestone at a time; screenshot each.
4. Art-direct: silhouette readable, light direction/intensity believable, horizon not dead-center, scale against human reference; fix before next milestone.
5. Deliver screenshots/renders as files (`MEDIA:` path) plus short saved-state summary.

Worked builds in `references/recipes.md`: exterior daylight, moody interior, golden-hour render, asset import/placement.

## Reference Files

| Reference | Contents |
|---|---|
| `references/tool-surface.md` | Shipped toolsets catalog, discovery protocol detail, plugin console commands/CVars/flags, screenshot & capture paths, MCP Inspector debugging, extending with custom Python/C++ toolsets |
| `references/advanced-workflows.md` | Sophisticated workflows, live-verified: ProgrammaticToolset batching, Blueprint DSL authoring loop (create→DSL→compile→spawn), PIE test sessions, Sequencer orientation (140 tools), LogsToolset self-debugging, automation testing, semantic asset search, config settings, per-situation decision table |
| `references/scene-craft.md` | Numeric cheat sheet: physical light intensities, color temperatures, exposure/EV100, fog densities, mood recipes (noon/golden hour/overcast/night/interior), scale tables, content path conventions |
| `references/recipes.md` | End-to-end worked builds with exact call sequences |
| `references/pitfalls.md` | Setup, runtime, and workflow pitfalls with fixes — read before your first session and whenever something misbehaves |

## Pitfalls

- editor/server must start before Hermes; missing tools usually means wrong order
- one call at a time; game-thread calls freeze editor UI; warn for long operations
- modal editor dialog can stall indefinitely; ask user to inspect/dismiss
- default MCP call timeout is 120s; raise `mcp_servers.unreal-engine.timeout` in `~/.hermes/config.yaml` for imports/saves/renders
- after toolset hot reload/plugin enable, run `ModelContextProtocol.RefreshTools` and re-list; new C++ `UFUNCTION`s need full editor restart
- plugin is experimental; live `describe_toolset` schema wins over examples/docs
- server is unauthenticated by design; keep loopback-only, never bind wider
- data sent through plugin to connected LLM service is Licensed Technology under UE EULA §6(e); surface provider-training responsibility when asked

## Verification

- `list_toolsets` returns toolsets at session start
- scene/level queried before first edit
- each milestone's actors/properties re-queried and screenshot reviewed against brief
- level/dirty packages saved after each milestone and at end
- screenshot/render paths exist and are reported as absolute paths
- editor has no pending modal/unsaved surprise; user knows exactly what changed
