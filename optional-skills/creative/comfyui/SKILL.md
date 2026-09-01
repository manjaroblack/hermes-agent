---
name: comfyui
description: Generate images, video, and audio via diffusion workflows.
version: 5.1.0
author: [kshitijk4poor, alt-glitch, purzbeats]
license: MIT
platforms: [macos, linux, windows]
compatibility: "Requires ComfyUI (local, Comfy Desktop, or Comfy Cloud) and comfy-cli (auto-installed via pipx/uvx by the setup script)."
prerequisites:
  commands: ["python"]
setup:
  help: "Run scripts/hardware_check.py FIRST to decide local vs Comfy Cloud; then scripts/comfyui_setup.sh auto-installs locally (or use Cloud API key for platform.comfy.org)."
metadata:
  hermes:
    tags:
      - comfyui
      - image-generation
      - stable-diffusion
      - flux
      - sd3
      - wan-video
      - hunyuan-video
      - creative
      - generative-ai
      - video-generation
    related_skills: [stable-diffusion]
    category: creative
---

# ComfyUI

role: ComfyUI lifecycle + workflow operator
do: choose local/cloud, install/launch/verify ComfyUI, inspect dependencies, execute workflows, monitor/download outputs
inputs: API-format workflow, params, optional image/audio/video, local server or Comfy Cloud
outputs: generated files + JSON status; verified server/models/dependencies
¬: execute editor-format JSON; expose API key to signed storage URL; trust unknown custom nodes/workflows; skip hardware/cloud decision

Use official `comfy-cli` for setup/lifecycle and direct REST/WebSocket + bundled scripts for execution.

## When to Use

- Stable Diffusion, SDXL, Flux, SD3 image generation
- workflow execution/chaining; ControlNet, inpaint, img2img
- queue/model/custom-node management
- AnimateDiff, Hunyuan, Wan video; AudioCraft/audio; 3D workflows

## Pack Map

References (`references/`): `official-cli.md` (every `comfy ...` command + flags); `rest-api.md` (local/cloud REST+WS, schemas); `workflow-format.md` (API JSON/nodes/params); `template-integrity.md` (`comfyui-workflow-templates` editor→API conversion, Reroute bypass, dotted dynamic keys `values.a`, `resize_type.width`, 302 redirects, one free-tier job, 1080p VRAM ceiling, Discord-compatible ffmpeg stitch; authored by [@purzbeats](https://github.com/purzbeats); load for official templates).

Scripts:

| Script | Purpose |
|---|---|
| `_common.py` | shared HTTP/cloud routing/node catalogs; do not run directly |
| `hardware_check.py` | GPU/VRAM/disk → local vs Cloud |
| `comfyui_setup.sh` | check + comfy-cli + install + launch + verify |
| `extract_schema.py` | controllable params + model deps |
| `check_deps.py` | running-server missing nodes/models |
| `auto_fix_deps.py` | check then `comfy node install`/`comfy model download` |
| `run_workflow.py` | inject params, submit, monitor, download via HTTP/WS |
| `run_batch.py` | N runs with sweeps, tier-bounded parallelism |
| `ws_monitor.py` | live WebSocket progress |
| `health_check.py` | CLI/server/models/smoke checklist |
| `fetch_logs.py` | prompt traceback/status |

Examples: SD1.5, SDXL, Flux Dev, SDXL img2img/inpaint, ESRGAN, AnimateDiff, Wan T2V under `workflows/`; see `workflows/README.md`.

## Two Layers

```text
┌─────────────────────────────────────────────────────┐
│ Layer 1: comfy-cli (official lifecycle tool)        │
│   Setup, server lifecycle, custom nodes, models     │
│   → comfy install / launch / stop / node / model    │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│ Layer 2: REST/WebSocket API + skill scripts         │
│   Workflow execution, param injection, monitoring   │
│   POST /api/prompt, GET /api/view, WS /ws           │
│   → run_workflow.py, run_batch.py, ws_monitor.py    │
└─────────────────────────────────────────────────────┘
```

CLI handles installation/server management; REST/WS scripts handle parameter injection, monitoring, output download.

## Quick Start

Detect:

```bash
# What's available?
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Can this machine run ComfyUI locally? (GPU/VRAM/disk check)
python scripts/hardware_check.py
```

Health:

```bash
python scripts/health_check.py
# → JSON: comfy_cli on PATH? server reachable? at least one checkpoint? smoke-test passes?
```

## Procedure

### 1. API-format workflow

Use JSON where every node has `class_type`. Sources: UI **Workflow → Export (API)** (new UI), legacy **Save (API Format)**, bundled workflows, or community downloads. Community editor format usually has top-level `nodes` + `links`; it is not executable. Load in UI and re-export. Scripts detect and explain.

### 2. Schema

```bash
python scripts/extract_schema.py workflow_api.json --summary-only
# → {"parameter_count": 12, "has_negative_prompt": true, "has_seed": true, ...}

python scripts/extract_schema.py workflow_api.json
# → full schema with parameters, model deps, embedding refs
```

### 3. Execute

```bash
# Local (defaults to http://127.0.0.1:8188)
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs

# Cloud (export API key once; uses correct /api routing automatically)
export COMFY_CLOUD_API_KEY="comfyui-..."
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs

# Real-time progress via WebSocket (requires `pip install websocket-client`)
python scripts/run_workflow.py \
  --workflow flux_dev.json \
  --args '{"prompt": "..."}' \
  --ws

# img2img / inpaint: pass --input-image to upload + reference automatically
python scripts/run_workflow.py \
  --workflow sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it watercolor", "denoise": 0.6}'

# Batch / sweep: 8 random seeds, parallel up to cloud tier limit
python scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3 \
  --output-dir ./outputs/batch
```

`seed: -1` or `--randomize-seed` without seed = fresh seed per run.

### 4. JSON result

```json
{
  "status": "success",
  "prompt_id": "abc-123",
  "outputs": [
    {"file": "./outputs/sdxl_00001_.png", "node_id": "9",
     "type": "image", "filename": "sdxl_00001_.png"}
  ]
}
```

## Decision Tree

| User says | Tool | Command |
|---|---|---|
| "install ComfyUI" | comfy-cli | `bash scripts/comfyui_setup.sh` |
| "start ComfyUI" | comfy-cli | `comfy launch --background` |
| "stop ComfyUI" | comfy-cli | `comfy stop` |
| "install X node" | comfy-cli | `comfy node install <name>` |
| "download X model" | comfy-cli | `comfy model download --url <url> --relative-path models/checkpoints` |
| "list installed models" | comfy-cli | `comfy model list` |
| "list installed nodes" | comfy-cli | `comfy node show installed` |
| "is everything ready?" | script | `health_check.py` (optionally `--workflow X --smoke-test`) |
| "what can I change in this workflow?" | script | `extract_schema.py W.json` |
| "check if W's deps are met" | script | `check_deps.py W.json` |
| "fix missing deps" | script | `auto_fix_deps.py W.json` |
| "generate an image" | script | `run_workflow.py --workflow W --args '{...}'` |
| "use this image" | script | `run_workflow.py --input-image image=./x.png ...` |
| "8 variations with random seeds" | script | `run_batch.py --count 8 --randomize-seed ...` |
| "show me live progress" | script | `ws_monitor.py --prompt-id <id>` |
| "fetch the error from job X" | script | `fetch_logs.py <prompt_id>` |
| "what's in the queue?" | REST | `curl http://HOST:8188/queue` or `--host https://cloud.comfy.org` |
| "cancel that" | REST | `curl -X POST http://HOST:8188/interrupt` |
| "free GPU memory" | REST | `curl -X POST http://HOST:8188/free` |

## Setup + Onboarding

When setup is requested, first ask local vs Cloud before install/hardware. Cloud = hosted RTX 6000 Pro, common models preinstalled, zero setup, API key; paid subscription required for workflows, free tier read-only. Local = free but hardware-bound.

Docs: https://docs.comfy.org/installation; CLI: https://docs.comfy.org/comfy-cli/getting-started; Cloud: https://docs.comfy.org/get_started/cloud; Cloud API: https://docs.comfy.org/development/cloud/overview.

Suggested choice prompt:

> "Do you want to run ComfyUI locally on your machine, or use Comfy Cloud?
>
> - **Comfy Cloud** — hosted on RTX 6000 Pro GPUs, all common models pre-installed,
>   zero setup. Requires an API key (paid subscription required to actually run
>   workflows; free tier is read-only). Best if you don't have a capable GPU.
> - **Local** — free, but your machine MUST meet the hardware requirements:
>   - NVIDIA GPU with **≥6 GB VRAM** (≥8 GB for SDXL, ≥12 GB for Flux/video), OR
>   - AMD GPU with ROCm support (Linux), OR
>   - Apple Silicon Mac (M1+) with **≥16 GB unified memory** (≥32 GB recommended).
>   - Intel Macs and machines with no GPU will NOT work — use Cloud instead.
>
> Which would you like?"

Routing: Cloud → Path A; Local → hardware check then B–E; Unsure → hardware check.

### Local hardware

```bash
python scripts/hardware_check.py --json
# Optional: also probe `torch` for actual CUDA/MPS:
python scripts/hardware_check.py --json --check-pytorch
```

| Verdict | Meaning | Action |
|---|---|---|
| `ok` | ≥8 GB discrete VRAM OR ≥32 GB Apple unified | local; use `comfy_cli_flag` |
| `marginal` | SD1.5 works; SDXL tight; Flux/video unlikely | light local or Path A Cloud |
| `cloud` | no GPU, <6 GB, <16 GB Apple unified, Intel Mac, Rosetta Python | Cloud unless explicit local force |

Report `wsl: true` (WSL2 NVIDIA passthrough) and `rosetta: true` (x86_64 Python on Apple Silicon; reinstall ARM64). If `cloud` + user wants local, show `notes` verbatim and ask switch vs force (OOM/slow); do not silently proceed.

### Paths

| Situation | Path |
|---|---|
| `verdict: cloud` from hardware check | A Cloud |
| no GPU/no commitment | A Cloud |
| Windows NVIDIA nontechnical | B Desktop |
| Windows NVIDIA technical | C Portable or D CLI |
| Linux any GPU | D CLI |
| macOS Apple Silicon | B Desktop or D CLI |
| headless/server/CI/agent | D CLI |

Automated path:

```bash
bash scripts/comfyui_setup.sh
# Or with overrides:
bash scripts/comfyui_setup.sh --m-series --port=8190 --workspace=/data/comfy
```

Script checks hardware, rejects local on `cloud` unless `--force-cloud-override`, chooses `comfy-cli` flag, prefers pipx/uvx over global pip.

### Path A: Cloud

1. Sign up: https://comfy.org/cloud
2. Key: https://platform.comfy.org/login
3. Set:

```bash
export COMFY_CLOUD_API_KEY="your-comfyui-key"
```

4. Run:

```bash
python scripts/run_workflow.py \
  --workflow workflows/flux_dev_txt2img.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs
```

Pricing: https://www.comfy.org/cloud/pricing. Concurrent: Free/Standard 1, Creator 3, Pro 5. Free API tier cannot run workflows, only browse; paid needed for `/api/prompt`, `/api/upload/*`, `/api/view`.

### Path B: Desktop

Windows/macOS beta; docs https://docs.comfy.org/installation/desktop; Windows NVIDIA https://download.comfy.org/windows/nsis/x64; macOS Apple Silicon https://comfy.org. Linux unsupported; use D.

### Path C: Portable

Windows only; docs https://docs.comfy.org/installation/comfyui_portable_windows. Download https://github.com/comfyanonymous/ComfyUI/releases; extract; run `run_nvidia_gpu.bat`; update `update/update_comfyui_stable.bat`.

### Path D: comfy-cli

```bash
# Recommended:
pipx install comfy-cli
# Or use uvx without installing:
uvx --from comfy-cli comfy --help
# Or (if pipx/uvx unavailable):
pip install --user comfy-cli
```

```bash
comfy --skip-prompt tracking disable
```

```bash
comfy --skip-prompt install --nvidia              # NVIDIA (CUDA)
comfy --skip-prompt install --amd                 # AMD (ROCm, Linux)
comfy --skip-prompt install --m-series            # Apple Silicon (MPS)
comfy --skip-prompt install --cpu                 # CPU only (slow)
comfy --skip-prompt install --nvidia --fast-deps  # uv-based dep resolution
```

Defaults `~/comfy/ComfyUI` Linux, `~/Documents/comfy/ComfyUI` macOS/Win; override `comfy --workspace /custom/path install`.

```bash
comfy launch --background                       # background daemon on :8188
comfy launch -- --listen 0.0.0.0 --port 8190    # LAN-accessible custom port
curl -s http://127.0.0.1:8188/system_stats      # health check
```

### Path E: Manual

For Ascend NPU, Cambricon MLU, Intel Arc, unsupported hardware; docs https://docs.comfy.org/installation/manual_install.

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130
pip install -r requirements.txt
python main.py
```

## Models + Nodes

```bash
# SDXL (general purpose, ~6.5 GB)
comfy model download \
  --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
  --relative-path models/checkpoints

# SD 1.5 (lighter, ~4 GB, good for 6 GB cards)
comfy model download \
  --url "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  --relative-path models/checkpoints

# Flux Dev fp8 (smaller variant, ~12 GB)
comfy model download \
  --url "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints

# CivitAI (set token first):
comfy model download \
  --url "https://civitai.com/api/download/models/128713" \
  --relative-path models/checkpoints \
  --set-civitai-api-token "YOUR_TOKEN"
```

List: `comfy model list`.

```bash
comfy node install comfyui-impact-pack             # popular utility pack
comfy node install comfyui-animatediff-evolved     # video generation
comfy node install comfyui-controlnet-aux          # ControlNet preprocessors
comfy node install comfyui-essentials              # common helpers
comfy node update all
comfy node install-deps --workflow=workflow.json   # install everything a workflow needs
```

Verify:

```bash
python scripts/health_check.py
# → comfy_cli on PATH? server reachable? checkpoints? smoke test?

python scripts/check_deps.py my_workflow.json
# → are this workflow's nodes/models/embeddings installed?

python scripts/run_workflow.py \
  --workflow workflows/sd15_txt2img.json \
  --args '{"prompt": "test", "steps": 4}' \
  --output-dir ./test-outputs
```

## Image Upload

```bash
python scripts/run_workflow.py \
  --workflow workflows/sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it cyberpunk", "denoise": 0.6}'
```

`--input-image` uploads then injects server filename into schema parameter `image`. Inpaint:

```bash
python scripts/run_workflow.py \
  --workflow workflows/sdxl_inpaint.json \
  --input-image image=./photo.png \
  --input-image mask_image=./mask.png \
  --args '{"prompt": "fill with flowers"}'
```

Manual REST:

```bash
curl -X POST "http://127.0.0.1:8188/upload/image" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
# Returns: {"name": "photo.png", "subfolder": "", "type": "input"}

# Cloud equivalent:
curl -X POST "https://cloud.comfy.org/api/upload/image" \
  -H "X-API-Key: $COMFY_CLOUD_API_KEY" \
  -F "image=@photo.png" -F "type=input" -F "overwrite=true"
```

## Cloud Contract

Base `https://cloud.comfy.org`; `X-API-Key` or `?token=KEY` WebSocket; scripts read `$COMFY_CLOUD_API_KEY`. `/api/view` 302s to signed URL; follow and strip `X-API-Key` before storage fetch. `/api/object_info`, `/api/queue`, `/api/userdata` = 403 free tier; `/history` → `/history_v2`; `/models/<folder>` → `/experiment/models/<folder>`; `clientId` WS ignored, filter `prompt_id` client-side; upload `subfolder` accepted but ignored (flat cloud namespace). Concurrent Free/Standard 1, Creator 3, Pro 5; `run_batch.py --parallel N` saturates tier.

## Queue + System

```bash
# Local
curl -s http://127.0.0.1:8188/queue | python -m json.tool
curl -X POST http://127.0.0.1:8188/queue -d '{"clear": true}'    # cancel pending
curl -X POST http://127.0.0.1:8188/interrupt                      # cancel running
curl -X POST http://127.0.0.1:8188/free \
  -H "Content-Type: application/json" \
  -d '{"unload_models": true, "free_memory": true}'

# Cloud — same paths under /api/, plus:
python scripts/fetch_logs.py --tail-queue --host https://cloud.comfy.org
```

## Pitfalls

1. API format only; editor `nodes`/`links` requires re-export via UI.
2. Live server required; `comfy launch --background`, verify `curl http://127.0.0.1:8188/system_stats`.
3. Model names case-sensitive + extension; `check_deps.py` fuzzy-matches, workflow uses canonical `comfy model list` name.
4. `class_type not found` = missing custom node; `check_deps.py` identifies package, `auto_fix_deps.py` installs.
5. No workspace → `comfy --workspace /path/to/ComfyUI <command>` or `comfy set-default /path/to/ComfyUI`.
6. Cloud free 403 for `/api/prompt`, `/api/view`, `/api/upload/*`, `/api/object_info`; scripts surface clear status.
7. Video/audio output nodes (`VHS_VideoCombine`, `SaveVideo`, etc.) auto timeout 900s vs 300s; override `--timeout 1800`.
8. Output filenames pass `safe_path_join`; never disable traversal protection.
9. Workflow JSON/custom nodes execute Python; inspect untrusted workflows like `eval`.
10. `seed: -1` or `--randomize-seed` yields fresh seed; actual seed logs stderr.
11. Disable first-run tracking with `comfy --skip-prompt tracking disable`; setup does it.

## Verification

Run `python scripts/health_check.py`, or confirm:

- `hardware_check.py` verdict `ok` or explicit Cloud choice
- `comfy --version` or `uvx --from comfy-cli comfy --help`
- `curl http://HOST:PORT/system_stats` JSON
- local `comfy model list` checkpoint OR cloud `/api/experiment/models/checkpoints`
- API-format workflow
- `check_deps.py` `is_ready: true` or cloud free-tier `node_check_skipped`
- small workflow completes; outputs are inside `--output-dir`
