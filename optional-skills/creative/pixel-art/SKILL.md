---
name: pixel-art
description: "Pixel art w/ era palettes (NES, Game Boy, PICO-8)."
version: 2.0.0
author: dodo-reach
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, pixel-art, arcade, snes, nes, gameboy, retro, image, video]
    category: creative
    credits:
      - "Hardware palettes and animation loops ported from Synero/pixel-art-studio (MIT) — https://github.com/Synero/pixel-art-studio"
---

# Pixel Art

role: pixel-art and short-animation operator
do: confirm era/scene; run pixel conversion; choose palette/block; optionally animate; inspect PNG/video; deliver files
inputs: source image, preset/palette/block, optional scene/duration/fps/seed/GIF, output paths
outputs: retro pixel-art PNG; optional MP4/GIF with effects; verification result
¬: skip style confirmation; use fractional/non-positive block/palette; claim hardware colors without preset; obscure source/artifact; omit ffprobe/image check

Convert an image into retro pixel art, then optionally animate it into a short MP4/GIF with era-appropriate effects. Scripts: `scripts/pixel_art.py` (photo→PNG, Floyd-Steinberg dithering) and `scripts/pixel_art_video.py` (PNG→MP4/GIF). Both are importable or runnable directly.

## When to Use

- source image to pixel art
- NES, Game Boy, PICO-8, C64, arcade, SNES, CRT, or other retro styling
- short looping rain/night/snow/particle animation
- posters, album covers, social posts, sprites, characters, avatars

## Prerequisites

- Python 3.9+
- Pillow: `pip install Pillow`
- `ffmpeg` on PATH for video; Hermes installs package support
- source image and output paths

## Procedure

### 1. Confirm style

Different presets produce different outputs; call `clarify` with four representative options unless the user named an era:

```python
clarify(
    question="Which pixel-art style do you want?",
    choices=[
        "arcade — bold, chunky 80s cabinet feel (16 colors, 8px)",
        "nes — Nintendo 8-bit hardware palette (54 colors, 8px)",
        "gameboy — 4-shade green Game Boy DMG",
        "snes — cleaner 16-bit look (32 colors, 4px)",
    ],
)
```

Named era such as `80s arcade`/`Gameboy` → skip `clarify`, use matching preset.

### 2. Offer animation

When video/GIF is requested or motion is useful, ask once:

```python
clarify(
    question="Want to animate it? Pick a scene or skip.",
    choices=[
        "night — stars + fireflies + leaves",
        "urban — rain + neon pulse",
        "snow — falling snowflakes",
        "skip — just the image",
    ],
)
```

At most two consecutive `clarify` calls: style, then scene. Skip both when style/scene are explicit.

### 3. Generate

Run `pixel_art()` first; if selected, pass its output to `pixel_art_video()`.

```python
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/pixel-art/scripts"))
from pixel_art import pixel_art
from pixel_art_video import pixel_art_video

# 1. Convert to pixel art
pixel_art("/path/to/photo.jpg", "/tmp/pixel.png", preset="nes")

# 2. Animate (optional)
pixel_art_video(
    "/tmp/pixel.png",
    "/tmp/pixel.mp4",
    scene="night",
    duration=6,
    fps=15,
    seed=42,
    export_gif=True,
)
```

CLI:

```bash
cd ~/.hermes/skills/creative/pixel-art/scripts

python pixel_art.py in.jpg out.png --preset gameboy
python pixel_art.py in.jpg out.png --preset snes --palette PICO_8 --block 6

python pixel_art_video.py out.png out.mp4 --scene night --duration 6 --gif
```

## Presets

| Preset | Era | Palette | Block | Best for |
|--------|-----|---------|-------|----------|
| `arcade` | 80s arcade | adaptive 16 | 8px | Bold posters, hero art |
| `snes` | 16-bit | adaptive 32 | 4px | Characters, detailed scenes |
| `nes` | 8-bit | NES (54) | 8px | True NES look |
| `gameboy` | DMG handheld | 4 green shades | 8px | Monochrome Game Boy |
| `gameboy_pocket` | Pocket handheld | 4 grey shades | 8px | Mono GB Pocket |
| `pico8` | PICO-8 | 16 fixed | 6px | Fantasy-console look |
| `c64` | Commodore 64 | 16 fixed | 8px | 8-bit home computer |
| `apple2` | Apple II hi-res | 6 fixed | 10px | Extreme retro, 6 colors |
| `teletext` | BBC Teletext | 8 pure | 10px | Chunky primary colors |
| `mspaint` | Windows MS Paint | 24 fixed | 8px | Nostalgic desktop |
| `mono_green` | CRT phosphor | 2 green | 6px | Terminal/CRT aesthetic |
| `mono_amber` | CRT amber | 2 amber | 6px | Amber monitor look |
| `neon` | Cyberpunk | 10 neons | 6px | Vaporwave/cyber |
| `pastel` | Soft pastel | 10 pastels | 6px | Kawaii / gentle |

Named palettes are in `scripts/palettes.py`; `references/palettes.md` lists 28. Override any preset:

```python
pixel_art("in.png", "out.png", preset="snes", palette="PICO_8", block=6)
```

## Animation Scenes

| Scene | Effects |
|-------|---------|
| `night` | Twinkling stars + fireflies + drifting leaves |
| `dusk` | Fireflies + sparkles |
| `tavern` | Dust motes + warm sparkles |
| `indoor` | Dust motes |
| `urban` | Rain + neon pulse |
| `nature` | Leaves + fireflies |
| `magic` | Sparkles + fireflies |
| `storm` | Rain + lightning |
| `underwater` | Bubbles + light sparkles |
| `fire` | Embers + sparkles |
| `snow` | Snowflakes + sparkles |
| `desert` | Heat shimmer + dust |

## Pipeline

Pixel conversion: boost contrast/color/sharpness → posterize tonal regions → downscale by `block` with `Image.NEAREST` → Floyd-Steinberg quantize against adaptive N-color or hardware palette → `Image.NEAREST` upscale. Quantize after downscale so dithering follows the final grid.

Video overlay: copy base frame each tick; draw stateless-per-frame particles; encode with ffmpeg `libx264 -pix_fmt yuv420p -crf 18`; optional GIF uses `palettegen` + `paletteuse`.

## Pitfalls

- palette keys are case-sensitive: `NES`, `PICO_8`, `GAMEBOY_ORIGINAL`
- sources under 100px wide collapse at 8-10px blocks; upscale first
- block/palette values must be positive integers
- particles are tuned for ~640x480; large images may need another seed/pass
- `mono_green`/`mono_amber` force `color=0.0`; retaining chroma can stripe smooth areas
- call `clarify` at most twice in a row

## Verification

- PNG exists at requested path
- square blocks are visible at selected block size
- color count matches preset; optionally `Image.open(p).getcolors()`
- MP4 is non-empty and opens with `ffprobe`; GIF exists when requested
- seed/scene/duration/fps are reported for reproducibility

## Attribution

Hardware palettes and procedural animation loops in `pixel_art_video.py` are ported from [pixel-art-studio](https://github.com/Synero/pixel-art-studio) (MIT). See `ATTRIBUTION.md`.
