---
name: kanban-video-orchestrator
description: Plan and run multi-agent video production pipelines.
version: 1.0.0
author: [SHL0MS, alt-glitch]
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [video, kanban, multi-agent, orchestration, production-pipeline]
    related_skills: [ascii-video, manim-video, p5js, comfyui, touchdesigner-mcp, pixel-art, ascii-art, songwriting-and-ai-music, heartmula, songsee, youtube-content, claude-design, excalidraw, architecture-diagram, concept-diagrams, baoyu-comic, baoyu-infographic, humanizer, gif-search, meme-generation]
    credits: |
      The single-project workspace layout, profile-config patching pattern,
      SOUL.md-per-profile model, TEAM.md task-graph convention, and
      `--workspace dir:/abs/path` discipline are adapted from alt-glitch's
      original multi-agent video pipeline at
      https://github.com/NousResearch/kanban-video-pipeline.
---

# Kanban Video Orchestrator

role: multi-agent video pipeline director
do: discover brief; design role team/tool matrix; generate/run setup; hand off director task; monitor/intervene; preserve shared workspace/tenant; verify keys and artifacts
inputs: video brief, duration/platform/aspect, style/audio/assets, deadline/deliverables, project path, available skills
outputs: `brief.md`, profile/team setup, `TEAM.md`, Kanban task graph, monitored specialist artifacts, deliverable status
¬: use for one-shot conversion/static/audio-only work; skip discovery/brief confirmation; clone fixed team; split workspaces; omit tenant; let director execute; fire missing-key tasks; over-decompose; claim rendered output without evidence

Wrap a video request—from a 15-second teaser through a narrative short/music video/ASCII loop—in a Hermes Kanban pipeline of specialized profiles. This skill orchestrates; it does not render. Rendering happens inside the board using matching skills/tools (`ascii-video`, `manim-video`, `p5js`, `comfyui`, `touchdesigner-mcp`, `songwriting-and-ai-music`, `heartmula`, external APIs, or Python + PIL + ffmpeg).

## When to Use

- video needs multiple specialist roles or review gates
- style, scenes, audio, assets, and rendering need coordinated task graph
- user requests a Kanban-driven production pipeline

## When Not to Use

- one continuous procedural project with no specialists → write code directly
- one-shot media conversion → use ffmpeg
- static image, GIF, or audio-only output → matching specific skill
- one existing skill fits cleanly, e.g. pure `ascii-video` → use it directly

## Procedure

Follow the workflow below in order.

## Workflow

```
DISCOVER  →  BRIEF  →  TEAM DESIGN  →  SETUP  →  EXECUTE  →  MONITOR
```

### 1. Discover

Always start with three baseline questions:

- what is the video? one-sentence brief
- how long? `5-30s` teaser / `30-90s` short / `90s-3min` explainer / `3-10min` film / longer
- aspect ratio + target platform? `1:1` / `9:16` / `16:9`; X, IG, YouTube, internal, etc.

Classify style and ask only needed follow-ups, 2-4 at a time; adapt after answers and assume only what the user implies. Intake banks: `references/intake.md`.

### 2. Brief

Write `brief.md` from `assets/brief.md.tmpl`, then show it for confirmation. It is the downstream contract:

1. concept: one-sentence pitch + emotional north star
2. scope: duration, aspect, platform, deadline
3. style: references, brand constraints, tone
4. scenes: beat-by-beat durations/content/target tool
5. audio: narration/music/SFX/silent per scene
6. deliverables: format, resolution, alternates (vertical/GIF/etc.)

### 3. Team design

Compose, do not clone. Director always exists; usually 4-7 profiles selected from actual brief needs. Use `references/role-archetypes.md` and `references/tool-matrix.md` for roles and skill/toolset mapping.

### 4. Setup

Generate/run `setup.sh`; `scripts/bootstrap_pipeline.py` generates it from brief + team-design JSON. It must:

1. create `~/projects/video-pipeline/<slug>/`
2. copy assets to `taste/`, `audio/`, `assets/`
3. create profiles via `hermes profile create --clone`
4. write per-profile `SOUL.md` personality + role
5. configure toolsets, `always_load` skills, cwd
6. write `brief.md`, `TEAM.md`, taste content
7. fire initial `hermes kanban create` assigned to director

Setup structure and shared-workspace rule: `references/kanban-setup.md`.

### 5. Execute

After `setup.sh`, give monitoring commands:

```bash
hermes kanban watch --tenant <project-tenant>     # live events
hermes kanban list  --tenant <project-tenant>     # board snapshot
hermes dashboard                                   # visual board UI
```

Director decomposes and routes specialists through Kanban; it does not render.

### 6. Monitor/intervene

Poll `kanban list`; inspect RUNNING tasks exceeding expected duration with `kanban show <id>` and check heartbeats. Standard interventions:

1. `kanban_comment` specific feedback
2. create a rerun task with original as parent
3. adjust brief scope and let director redecompose

Playbook: `references/monitoring.md`.

## Critical Rules

1. **Discovery before action:** three baseline questions before brief/team.
2. **Brief-fit team:** music needs beat analysis; narrative needs writer; use `references/role-archetypes.md`.
3. **One workspace/project:** all profiles share `workspace_kind="dir"`, `workspace_path="<absolute project path>"`; tasks pass artifacts via shared filesystem + structured handoffs.
4. **Tenant every project:** use project tenant such as `--tenant <project-slug>` to isolate board/dashboard.
5. **Respect existing skills:** renderer loads matching skill via task `--skill <name>` or profile `always_load`; do not rederive it.
6. **Director never executes:** director's `SOUL.md` forbids concrete work; every task becomes `hermes kanban create` to a specialist. Kanban guidance reinforces this.
7. **Smallest useful graph:** a 30-second product video does not need 20 tasks; parallelize only where useful and expose review gates.
8. **Verify API keys first:** TTS/image/image-to-video workers need keys in `${HERMES_HOME:-~/.hermes}/.env` or secret store; setup `check_key` aborts cleanly instead of consuming a task slot.

## File Map

```
SKILL.md                            ← this file (workflow + rules)
references/
  intake.md                         ← discovery question banks per style
  role-archetypes.md                ← role library (writer, designer, animator, …)
  tool-matrix.md                    ← skill + toolset mapping per role
  kanban-setup.md                   ← setup script structure & profile config
  monitoring.md                     ← watch + intervene patterns
  examples.md                       ← six worked pipelines
assets/
  brief.md.tmpl                     ← brief skeleton
  setup.sh.tmpl                     ← setup script skeleton
  soul.md.tmpl                      ← profile personality skeleton
scripts/
  bootstrap_pipeline.py             ← generate setup.sh from brief + team JSON
  monitor.py                        ← polling + intervention helpers
```

Worked examples (narrative, product, music, math, ASCII, real-time installation): `references/examples.md`.

## Pitfalls

- no baseline discovery → bad brief cascades through graph
- fixed/cloned team misses style-specific roles
- separate workspaces break artifact handoffs
- missing tenant cross-pollinates ongoing projects
- director executing bypasses review/routing; keep it decomposition-only
- missing external key wastes a worker; check before firing
- stale/long-running task needs heartbeat and intervention, not silent waiting

## Verification

- baseline questions answered; confirmed `brief.md` covers concept/scope/style/scenes/audio/deliverables
- team matches scenes and tool matrix; director assigned but non-executing
- all task creates use absolute shared `dir:` workspace + project tenant
- required keys validated before task launch
- board/dashboard monitoring commands work
- each downstream artifact has structured handoff and user-visible status
- final files/format/resolution/alternates match brief
