---
name: ascii-video
description: "ASCII video: convert video/audio to colored ASCII MP4/GIF."
version: 1.0.0
author: SHL0MS, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Video, FFmpeg, Terminal-Art]
    related_skills: []
---

# ASCII Video Production

role: ASCII visual director + Python/ffmpeg implementer
do: turn video, audio, image, text, or generative input into layered colored ASCII MP4/GIF/image sequences or terminal output
inputs: source mode, creative brief, resolution/FPS, palette, scene map
outputs: self-contained Python project, rendered frames/clips, encoded media
¬: generic flat output; linear brightness multipliers; ffmpeg stderr pipe deadlock; unverified first render

## When to Use

- ASCII/text-art/terminal-style video or character animation
- retro text visualization, Matrix-style effect, ASCII audio visualizer
- video → ASCII; audio-reactive; generative; hybrid; lyrics/text/SRT; TTS narration

## Creative Standard

Art first; cinema is the standard. Before code, state mood, visual story, differentiator, and emotional arc. First render must be striking; generic/flat output is a failed concept. Combine/modify/invent beyond references; include one unrequested detail that elevates the piece. Scenes share color temperature, character palette logic, motion vocabulary, and layered composition. Never flat black or one grid; vary per scene with intentional color.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Video-to-ASCII** | Video file | ASCII recreation of source footage | `references/inputs.md` § Video Sampling |
| **Audio-reactive** | Audio file | Generative visuals driven by audio features | `references/inputs.md` § Audio Analysis |
| **Generative** | None (or seed params) | Procedural ASCII animation | `references/effects.md` |
| **Hybrid** | Video + audio | ASCII video with audio-reactive overlays | Both input refs |
| **Lyrics/text** | Audio + text/SRT | Timed text with visual effects | `references/inputs.md` § Text/Lyrics |
| **TTS narration** | Text quotes + TTS API | Narrated testimonial/quote video with typed text | `references/inputs.md` § TTS Integration |

## Stack

One self-contained Python script per project; no GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Python 3.10+, NumPy | Math, array ops, vectorized effects |
| Signal | SciPy | FFT, peak detection (audio modes) |
| Imaging | Pillow (PIL) | Font rasterization, frame decoding, image I/O |
| Video I/O | ffmpeg (CLI) | Decode input, encode output, mux audio |
| Parallel | concurrent.futures | N workers for batch/clip rendering |
| TTS | ElevenLabs API (optional) | Generate narration clips |
| Optional | OpenCV | Video frame sampling, edge detection |

## Pipeline

```text
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```

1. INPUT: decode video/audio/images or initialize no source.
2. ANALYZE: extract audio bands, luminance/edges, motion vectors.
3. SCENE_FN: render `uint8 H,W,3`; compose character grids through `_render_vf()` + blend modes; see `references/composition.md`.
4. TONEMAP: percentile adaptive brightness; see `references/composition.md` § Adaptive Tonemap.
5. SHADE: `ShaderChain` + `FeedbackBuffer`; see `references/shaders.md`.
6. ENCODE: raw RGB frames → ffmpeg H.264/GIF.

## Creative Controls

| Dimension | Options | Reference |
|-----------|---------|-----------|
| Character palette | density ramps, block elements, symbols, katakana, Greek, runes, braille, project-specific | `architecture.md` § Palettes |
| Color strategy | HSV, OKLAB/OKLCH, discrete RGB, generated harmony, monochrome, temperature | `architecture.md` § Color System |
| Background texture | sine fields, fBM, domain warp, voronoi, reaction-diffusion, cellular automata, video | `effects.md` |
| Primary effects | rings, spirals, tunnel, vortex, waves, interference, aurora, fire, SDFs, strange attractors | `effects.md` |
| Particles | sparks, snow, rain, bubbles, runes, orbits, boids, flow-field followers, trails | `effects.md` § Particles |
| Shader mood | CRT, clean modern, glitch, cinematic, dreamy, industrial, psychedelic | `shaders.md` |
| Grid density | xs(8px) through xxl(40px), mixed per layer | `architecture.md` § Grid System |
| Coordinate space | Cartesian, polar, tiled, rotated, fisheye, Möbius, domain-warped | `effects.md` § Transforms |
| Feedback | zoom tunnel, rainbow trails, ghost echo, rotating mandala, color evolution | `composition.md` § Feedback |
| Masking | circle, ring, gradient, text stencil, animated iris/wipe/dissolve | `composition.md` § Masking |
| Transitions | crossfade, wipe, dissolve, glitch cut, iris, mask reveal | `shaders.md` § Transitions |

Per scene: vary background (or compose 2–3), character palette, color strategy/hue, shader intensity (bloom at peaks, grain in quiet), and particle type. Invent at least one custom palette/effect/color set/particle set/transition.

## Workflow

### 1. Creative vision

Write mood/atmosphere; visual story; color world; character texture; differentiator; emotional arc. A chill lo-fi visualizer and glitch cyberpunk data stream require different choices.

### 2. Technical design

Choose mode; resolution (landscape 1920x1080 default, portrait 1080x1920, square 1080x1080) @ 24fps; hardware/quality profile from `references/optimization.md`; timestamped sections with independent configs; output MP4 default, GIF 640x360 @ 15fps, or PNG sequence.

### 3. Build one Python script

1. hardware detection + quality profile → `references/optimization.md`
2. input loader → `references/inputs.md`
3. feature analyzer: FFT, video luminance, or synthetic
4. multi-density grid + bitmap cache → `references/architecture.md`
5. multiple character palettes
6. HSV + discrete RGB + harmony generation
7. scene functions returning `canvas (uint8 H,W,3)` → `references/scenes.md`
8. adaptive tonemap → `references/composition.md`
9. `ShaderChain` + `FeedbackBuffer` → `references/shaders.md`
10. scene table + time dispatcher → `references/scenes.md`
11. N-worker clip renderer + ffmpeg pipes
12. main orchestration

### 4. Verify before full render

Render stills at key timestamps. Require `canvas.mean() > 8` for ASCII content; lower gamma if dark. Check scene coherence and match to the stated concept; return to vision if generic.

## Critical Implementation

Never brighten with `canvas * N`; it clips highlights. Use:

```python
def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.5])
    if hi - lo < 10: hi = lo + 10
    f = np.clip((f - lo) / (hi - lo), 0, 1) ** gamma
    return (f * 255).astype(np.uint8)
```

Order: `scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`. Gamma defaults: 0.75; solarize 0.55; posterize 0.50; bright scenes 0.85. Use `screen`, not `overlay`, for dark layers.

- macOS Pillow `textbbox()` has wrong height; use `font.getmetrics()`, `cell_height = ascent + descent`; see `references/troubleshooting.md`.
- never `stderr=subprocess.PIPE` for long ffmpeg; 64KB buffer can deadlock; redirect stderr to a file.
- validate Unicode palette at initialization; render each char and reject blank output.
- segmented quotes/scenes/chapters: separate clip files for parallel/selective rerender → `references/scenes.md`.

## Performance Targets

| Component | Budget |
|-----------|--------|
| Feature extraction | 1-5ms |
| Effect function | 2-15ms |
| Character render | 80-150ms (bottleneck) |
| Shader pipeline | 5-25ms |
| **Total** | ~100-200ms/frame |

## References

| File | Contents |
|------|----------|
| `references/architecture.md` | Grid system, resolution presets, font selection, 20+ palettes, HSV/OKLAB/discrete RGB/harmony, `_render_vf()`, `GridLayer` |
| `references/composition.md` | 20 blend modes, `blend_canvas()`, multi-grid, adaptive `tonemap()`, `FeedbackBuffer`, `PixelBlendStack`, masking/stencil |
| `references/effects.md` | value/hue fields, noise/fBM/domain warp, voronoi, reaction-diffusion, cellular automata, SDFs, attractors, particles, transforms, temporal coherence |
| `references/shaders.md` | `ShaderChain`, `_apply_shader_step()`, 38 shaders, audio scaling, transitions, tint presets, encoding, terminal rendering |
| `references/scenes.md` | scene protocol, `Renderer`, `SCENES`, `render_clip()`, beat cuts, parallel rendering, design patterns/examples/checklist |
| `references/inputs.md` | FFT/bands/beats, video sampling, image conversion, text/lyrics, ElevenLabs/TTS, voice assignment, mixing |
| `references/optimization.md` | hardware detection, quality profiles, vectorization, parallel rendering, memory, budgets |
| `references/troubleshooting.md` | NumPy broadcasting, blend pitfalls, multiprocessing/pickling, brightness, ffmpeg, fonts, common mistakes |

## Creative Divergence

Only when user requests experimental/creative/unique output; select and reason before code.

- Forced Connections: unrelated domain (weather, microbiology, architecture, fluid dynamics, textile weaving) → list visual/structural elements → map to characters/patterns → synthesize.
- Conceptual Blending: name two spaces (ocean waves + sheet music) → map crests/high notes, troughs/rests, foam/staccato → keep only interesting mappings → develop emergent blend properties.
- Oblique Strategies: draw one: `Honor thy error as a hidden intention` / `Use an old idea` / `What would your closest friend do?` / `Emphasize the flaws` / `Turn it upside down` / `Only a part, not the whole` / `Reverse`; interpret against challenge; apply before code.

## Pitfalls

- do not render the full piece before one representative frame, one transition, and one audio/encoding path work
- long ffmpeg stderr pipes can deadlock; use the documented file redirection path
- keep each scene's visual language coherent while making intentional variation visible

## Verification

- test frames render at key timestamps
- brightness, palette/font validity, ffmpeg encoding, output duration/format verified
- all scenes share visual language yet vary intentionally
- output passes concept/first-render review; no unresolved generic/flat result
