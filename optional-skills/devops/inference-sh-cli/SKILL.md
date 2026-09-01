---
name: inference-sh-cli
description: Run 150+ AI apps (image, video, LLM) via inference.sh CLI.
version: 1.0.0
author: okaris
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [AI, image-generation, video, LLM, search, inference, FLUX, Veo, Claude]
    related_skills: []
---

# inference.sh CLI

role: `infsh` cloud AI-app operator
do: verify/authenticate; search catalog; use exact app ID; pass JSON input; parse URLs; deliver media; report long-run/auth errors
inputs: desired app/category, prompt/query, local files, app-specific JSON, output media target
outputs: generated image/video/audio/search result URLs, inline `MEDIA:<url>` references
¬: guess app IDs; omit `--json`; expose keys; misescape JSON; claim long-running app complete before output

Run 150+ cloud AI apps without a GPU through the `infsh` CLI. All commands use Hermes `terminal`.

## When to Use

- FLUX/Reve/Seedream/Grok/Gemini image generation
- Veo/Wan/Seedance/OmniHuman video, avatar, lipsync
- inference.sh/`infsh` questions or unified provider access
- Tavily/Exa AI search

## Prerequisites

`infsh` installed and authenticated:

```bash
infsh me
```

Install/login:

```bash
curl -fsSL https://cli.inference.sh | sh
infsh login
```

Details: `references/authentication.md`.

## Procedure

### 1. Search first

Never guess IDs:

```bash
infsh app list --search flux
infsh app list --search video
infsh app list --search image
```

### 2. Run exact ID

Always request machine-readable output:

```bash
infsh app run <app-id> --input '{"prompt": "your prompt here"}' --json
```

### 3. Parse/deliver

Read JSON URLs; present generated media as `MEDIA:<url>`.

## App Recipes

### Images

```bash
# Search for image apps
infsh app list --search image

# FLUX Dev with LoRA
infsh app run falai/flux-dev-lora --input '{"prompt": "sunset over mountains", "num_images": 1}' --json

# Gemini image generation
infsh app run google/gemini-2-5-flash-image --input '{"prompt": "futuristic city", "num_images": 1}' --json

# Seedream (ByteDance)
infsh app run bytedance/seedream-5-lite --input '{"prompt": "nature scene"}' --json

# Grok Imagine (xAI)
infsh app run xai/grok-imagine-image --input '{"prompt": "abstract art"}' --json
```

### Video

```bash
# Search for video apps
infsh app list --search video

# Veo 3.1 (Google)
infsh app run google/veo-3-1-fast --input '{"prompt": "drone shot of coastline"}' --json

# Seedance (ByteDance)
infsh app run bytedance/seedance-1-5-pro --input '{"prompt": "dancing figure", "resolution": "1080p"}' --json

# Wan 2.5
infsh app run falai/wan-2-5 --input '{"prompt": "person walking through city"}' --json
```

### Local uploads

A local path in JSON is uploaded automatically:

```bash
# Upscale a local image
infsh app run falai/topaz-image-upscaler --input '{"image": "/path/to/photo.jpg", "upscale_factor": 2}' --json

# Image-to-video from local file
infsh app run falai/wan-2-5-i2v --input '{"image": "/path/to/image.png", "prompt": "make it move"}' --json

# Avatar with audio
infsh app run bytedance/omnihuman-1-5 --input '{"audio": "/path/to/audio.mp3", "image": "/path/to/face.jpg"}' --json
```

### Search/research and other catalogs

```bash
infsh app list --search search
infsh app run tavily/tavily-search --input '{"query": "latest AI news"}' --json
infsh app run exa/exa-search --input '{"query": "machine learning papers"}' --json
```

## Pitfalls

- IDs change; run `infsh app list --search <term>` first.
- `--json` is required for parseable URLs.
- auth failure → `infsh login` or verify `INFSH_API_KEY`.
- video apps can take 30-120s; use adequate terminal timeout and tell user.
- `--input` is a JSON string; escape nested quotes correctly.

## Verification

- `infsh me` proves auth
- search output supplies the exact app ID used
- run returns valid JSON and expected URL(s)
- local file inputs upload successfully
- media URL is delivered as `MEDIA:<url>`

## Reference Docs

- `references/authentication.md` — setup/login/API keys
- `references/app-discovery.md` — catalog search
- `references/running-apps.md` — inputs/output handling
- `references/cli-reference.md` — full CLI

## Preserved Source Examples

### Original example 1

```bash
# 3D generation
infsh app list --search 3d

# Audio / TTS
infsh app list --search tts

# Twitter/X automation
infsh app list --search twitter
```
