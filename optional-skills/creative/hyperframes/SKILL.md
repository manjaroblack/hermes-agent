---
name: hyperframes
description: Render MP4/WebM videos from HTML compositions.
version: 1.0.0
author: heygen-com
license: Apache-2.0
platforms: [linux, macos, windows]
prerequisites:
  commands: [node, ffmpeg, npx]
metadata:
  hermes:
    tags: [creative, video, animation, html, gsap, motion-graphics]
    related_skills: [manim-video, meme-generation]
    category: creative
    requires_toolsets: [terminal]
---

# HyperFrames

role: deterministic HTML-to-video production operator
do: plan hero frames; define DESIGN.md; scaffold; layout; animate GSAP timelines; add media/transitions; lint/validate/inspect; render; inspect output; clean preview workers
inputs: narrative/URL/script, HTML/CSS/JS composition, media, duration/fps/quality/format, visual identity
outputs: MP4/WebM, optional captions/audio, animation map, validation evidence
¬: generic visual identity; infinite repeats; nondeterministic clocks/randomness; async timeline construction; jump cuts; visible caption leaks; leave preview workers running; claim render without media/ffprobe checks

HTML is the source of truth: `data-*` timing, GSAP timeline animation, CSS appearance. HyperFrames captures frames and encodes MP4/WebM through FFmpeg.

Use `manim-video` for mathematical/geometric explainers; use HyperFrames for motion graphics, talking-head captions, product tours, social overlays, shader transitions, and real audio/video media.

## When to Use

- render a video from text, script, website, HTML/CSS/JS, or real media
- title cards, lower thirds, typography, TTS/captions, audio-reactive visuals
- scene transitions, social overlays, website-to-video, deterministic animation

Do not use for pure math/equation animation (`manim-video`), image/meme generation, or live conferencing/streaming.

## Prerequisites

- Node.js >=22, FFmpeg, `npx`; run `npx hyperframes doctor`
- one-time setup script and Chrome headless shell
- `references/` files as needed

## Quick Reference

```bash
npx hyperframes init my-video               # scaffold a project
cd my-video
npx hyperframes lint                        # validate before preview/render
npx hyperframes preview                     # live-reload preview (long-lived server, port 3002)
npx hyperframes render --output final.mp4   # render to MP4
npx hyperframes doctor                      # diagnose environment issues
```

`preview` is long-lived Next.js and keeps Chrome workers open; stop it after review. Render flags: `--quality draft|standard|high`, `--fps 24|30|60`, `--format mp4|webm`, `--docker`, `--strict`. Full CLI: `references/cli.md`.

## Setup

```bash
bash "$(dirname "$(find ~/.hermes/skills -path '*/hyperframes/SKILL.md' 2>/dev/null | head -1)")/scripts/setup.sh"
```

The script verifies Node >=22/FFmpeg, installs `hyperframes@>=0.4.2`, pre-caches Puppeteer `chrome-headless-shell` for `HeadlessExperimental.beginFrame`, then runs `doctor`. Setup failures: `references/troubleshooting.md`.

## Procedure

### 1. Plan and pass the visual identity gate

Define narrative arc, key moments, emotional beats; tracks/durations; colors/fonts/motion character; and each scene's hero frame.

**Hard gate before any composition HTML:**

1. `DESIGN.md` exists → follow exact colors, fonts, motion rules, and “What NOT to Do”.
2. User named a style → create minimal `DESIGN.md` with `## Style Prompt`, `## Colors` (3-5 role-labeled hexes), `## Typography` (1-2 families), `## What NOT to Do` (3-5 anti-patterns).
3. Neither → ask mood (explosive/cinematic/fluid/technical/chaotic/warm), light/dark canvas, and brand colors/fonts/references; write `DESIGN.md`.

Reject generic `#333`, `#3b82f6`, or `Roboto` defaults unless explicitly required. Every composition palette/type traces to `DESIGN.md` or user direction.

### 2. Scaffold

```bash
npx hyperframes init my-video --non-interactive
```

Templates: `blank`, `warm-grain`, `play-mode`, `swiss-grid`, `vignelli`, `decision-tree`, `kinetic-type`, `product-promo`, `nyt-graph`. Optional `--example <name>`, `--video clip.mp4`, `--audio track.mp3`.

### 3. Layout before animation

Build static HTML+CSS for the hero frame first. `.scene-content` fills the scene (`width:100%; height:100%; padding:Npx`, `display:flex`, `gap`); use padding, not `position: absolute; top: Npx` on content containers, which overflows when content grows. After visual approval, add `gsap.from()` entrances to CSS position and `gsap.to()` exits from it. See `references/composition.md`.

### 4. Build deterministic GSAP timelines

Every composition:

- registers `window.__timelines["<composition-id>"] = tl`
- starts paused: `gsap.timeline({ paused: true })`
- uses finite repeats; never `repeat: -1`; calculate `repeat: Math.ceil(duration / cycleDuration) - 1`
- avoids `Math.random()`, `Date.now()`, wall-clock logic; use seeded PRNG for pseudo-randomness
- constructs synchronously; no `async`/`await`, `setTimeout`, or Promises around timeline construction

GSAP API: `references/gsap.md`.

### 5. Transition scenes

For multi-scene output:

1. always add a transition, never a jump cut
2. add entrance animation to every scene element (`gsap.from(...)`)
3. do not add exits except final scene; transition is the exit
4. final scene may fade out

Install shaders with `npx hyperframes add <transition-name>`; list with `npx hyperframes add --list`. Do not mix CSS and shader transitions in one composition.

### 6. Media features

- **Audio:** separate `<audio>`; video=`muted playsinline`.
- **TTS:** `npx hyperframes tts "Script text" --voice af_nova --output narration.wav`; list `--list`. Voice prefix: `a`/`b` English, `e` Spanish, `f` French, `j` Japanese, `z` Mandarin; `--lang` overrides. Non-English phonemization needs `espeak-ng`.
- **Captions:** `npx hyperframes transcribe narration.wav` gives word-level transcript. Choose hype/corporate/tutorial/storytelling/social style from transcript tone (`references/features.md`). Never use `.en` Whisper models unless audio is confirmed English; `.en` translates non-English. Every caption group gets `tl.set(el, { opacity: 0, visibility: "hidden" }, group.end)` after exit.
- **Audio reactive:** pre-extract bass/mid/treble; sample each frame via `for` + `tl.call(draw, [], f / fps)`, not one long tween. Map bass→`scale`, treble→`textShadow`/`boxShadow`, amplitude→`opacity`/`y`/`backgroundColor`; avoid equalizer clichés.
- **Marker highlights:** deterministic CSS+GSAP highlight/circle/burst/scribble/sketchout; `references/features.md#marker-highlighting`.
- **Scene transitions:** CSS primitives or shader names including `flash-through-white`, `liquid-wipe`, `cross-warp-morph`, `chromatic-split`; choose from mood/energy table; no CSS+shader mixing.

### 7. Lint, validate, inspect, preview, render

```bash
npx hyperframes lint              # catches missing data-composition-id, overlapping tracks, unregistered timelines
npx hyperframes validate          # WCAG contrast audit at 5 timestamps
npx hyperframes inspect           # visual layout audit — overflow, off-frame elements, occluded text
npx hyperframes preview           # live browser preview
npx hyperframes render --quality draft --output draft.mp4    # fast iteration
npx hyperframes render --quality high --output final.mp4     # final delivery
```

`validate` samples background behind text and warns below 4.5:1 (3:1 for large text). `inspect` renders multiple timestamps and finds overflow, off-frame elements, occlusion, wrapping, and transition-hidden elements; especially run it for speech bubbles/cards/captions/tight typography.

### 8. Website-to-video

When input is a URL, follow `references/website-to-video.md`: capture → `DESIGN.md` → `SCRIPT.md` → storyboard → composition → render → deliver.

## Cleanup

`render` exits workers; `preview` does not. On WSL/containers/CI, idle Chrome swiftshader can consume a CPU core each.

```bash
pkill -f "hyperframes.*preview"     # the Studio server (frees port 3002)
pkill -f chrome-headless-shell      # its render workers; only safe if nothing else uses them
```

Before killing shared Chrome, check `pgrep -af chrome-headless-shell`. Recovery details: `references/troubleshooting.md#runaway-cpu-from-leftover-preview-workers`.

## Pitfalls

- forgotten `preview` leaves long-lived Next.js/Chrome workers
- `HeadlessExperimental.beginFrame` missing on Chromium 147+: use `hyperframes@>=0.4.2` fallback or `export PRODUCER_FORCE_SCREENSHOT=true`; see [hyperframes#294](https://github.com/heygen-com/hyperframes/issues/294)
- system Chrome instead of `chrome-headless-shell` hangs; run `npx puppeteer browsers install chrome-headless-shell`; `doctor` reports binary
- `repeat: -1` breaks capture
- `gsap.set()` on later clip elements runs too early; use `tl.set(...)` at/after `data-start`
- forced `<br>` plus natural wrapping double-breaks; use `max-width`, except deliberate short display titles
- GSAP cannot tween `visibility`/`display`; use `autoAlpha`
- never call `video.play()`/`audio.play()`; framework owns playback
- async timeline construction is invisible to synchronous capture
- root `index.html` inside `<template>` hides page; only `data-composition-src` sub-compositions use `<template>`
- use muted video + separate audio

## Verification

1. Run `npx hyperframes lint --strict && npx hyperframes validate && npx hyperframes inspect`.
2. For new/significant animation, run:

   ```bash
   node skills/hyperframes/scripts/animation-map.mjs <composition-dir> \
     --out <composition-dir>/.hyperframes/anim-map
   ```

   Review `animation-map.json`: per-tween summary, ASCII Gantt, stagger/dead zones (>1s), lifecycles, and flags `offscreen`, `collision`, `invisible`, `paced-fast` (<0.2s), `paced-slow` (>2s); fix or justify flags. Skip for small edits.
3. File non-empty: `ls -lh final.mp4`.
4. Duration matches `data-duration`: `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 final.mp4`.
5. Visual frame: `ffmpeg -i final.mp4 -ss 00:00:05 -vframes 1 preview.png`.
6. Expected audio: `ffprobe -v error -show_streams -select_streams a -of default=nw=1:nk=1 final.mp4 | head -1`.

Render failure → run `npx hyperframes doctor` and attach output when reporting.

## References

- `references/composition.md` — data attributes, timeline contract, typography/assets
- `references/cli.md` — init/capture/lint/validate/inspect/preview/render/transcribe/tts/doctor/browser/info/upgrade/benchmark
- `references/gsap.md` — tweens, eases, stagger, timelines, matchMedia
- `references/features.md` — captions, TTS, audio-reactive, markers, transitions
- `references/website-to-video.md` — capture-to-video workflow
- `references/troubleshooting.md` — fixes, env vars, render errors
