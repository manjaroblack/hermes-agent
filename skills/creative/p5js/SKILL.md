---
name: p5js
description: "p5.js sketches: gen art, shaders, interactive, 3D."
version: 1.0.0
author: SHL0MS, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, manim-video, excalidraw]
---

# p5.js Production

role: browser creative-coding director + p5.js implementer
do: create generative art, interactive visualizations, data displays, 2D/3D scenes, audio-reactive visuals, motion graphics, and exports
inputs: concept, parameters/seed, data/media, interaction model, output format
outputs: single self-contained HTML; optional PNG/GIF/MP4/SVG
¬: tutorial-grade/default output; unseeded generative content; flat backgrounds; unverified frame rate/export

## When to Use

- p5.js sketch or creative coding
- generative art, canvas animation, browser visual art
- interactive visualization/data viz, shader effect, WebGL scene
- pixel manipulation, kinetic typography, audio-reactive or motion graphics

## Creative Standard

Canvas = medium; algorithm = brush. Before code, state what the piece communicates, what stops scrolling, what differs from a tutorial. First load must be striking; rethink default/AI-looking output before shipping. Combine/layer/invent beyond references. A particle system should gain emergent behavior, trailing echoes, depth fog, breathing noise, or another intentional treatment as the concept warrants. Never flat white/black; use hierarchy, color, and micro-detail. Cohesion beats feature count: shared temperature, stroke weights, motion speeds.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Generative art** | Seed / parameters | Procedural visual composition (still or animated) | `references/visual-effects.md` |
| **Data visualization** | Dataset / API | Interactive charts, graphs, custom data displays | `references/interaction.md` |
| **Interactive experience** | None (user drives) | Mouse/keyboard/touch-driven sketch | `references/interaction.md` |
| **Animation / motion graphics** | Timeline / storyboard | Timed sequences, kinetic typography, transitions | `references/animation.md` |
| **3D scene** | Concept description | WebGL geometry, lighting, camera, materials | `references/webgl-and-3d.md` |
| **Image processing** | Image file(s) | Pixel manipulation, filters, mosaic, pointillism | `references/visual-effects.md` § Pixel Manipulation |
| **Audio-reactive** | Audio file / mic | Sound-driven generative visuals | `references/interaction.md` § Audio Input |

## Stack

One self-contained HTML per project; no build step.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | p5.js 1.11.3 (CDN) | Canvas rendering, math, transforms, event handling |
| 3D | p5.js WebGL mode | 3D geometry, camera, lighting, GLSL shaders |
| Audio | p5.sound.js (CDN) | FFT analysis, amplitude, mic input, oscillators |
| Export | Built-in `saveCanvas()` / `saveGif()` / `saveFrames()` | PNG, GIF, frame sequence output |
| Capture | CCapture.js (optional) | Deterministic framerate video capture (WebM, GIF) |
| Headless | Puppeteer + Node.js (optional) | Automated high-res rendering, MP4 via ffmpeg |
| SVG | p5.js-svg 1.6.0 (optional) | Vector output for print — requires p5.js 1.x |
| Natural media | p5.brush (optional) | Watercolor, charcoal, pen — requires p5.js 2.x + WEBGL |
| Texture | p5.grain (optional) | Film grain, texture overlays |
| Fonts | Google Fonts / `loadFont()` | Custom typography via OTF/TTF/WOFF2 |

p5.js 1.x (1.11.3) is default for stability/docs/compatibility. p5.js 2.x (2.2+) adds `async setup()` instead of `preload()`, OKLCH/OKLAB, `splineVertex()`, shader `.modify()`, variable fonts, `textToContours()`, pointer events; required by p5.brush. See `references/core-api.md` § p5.js 2.0.

## Pipeline

```text
CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY
```

1. CONCEPT: mood, color world, motion, differentiator.
2. DESIGN: mode, canvas, interaction, colors, export.
3. CODE: inline HTML: globals → `preload()` → `setup()` → `draw()` → helpers → classes → events.
4. PREVIEW: browser/target resolution/performance.
5. EXPORT: `saveCanvas()` PNG; `saveGif()` GIF; `saveFrames()` + ffmpeg MP4; Puppeteer headless.
6. VERIFY: concept match, visual quality at display size, would you frame it?

## Aesthetic Dimensions

| Dimension | Options | Reference |
|-----------|---------|-----------|
| Color system | HSB/HSL, RGB, named palettes, procedural harmony, gradient interpolation | `references/color-systems.md` |
| Noise vocabulary | Perlin, simplex, fractal/octaved, domain warping, curl noise | `references/visual-effects.md` § Noise |
| Particle systems | physics, flocking, trail-drawing, attractor, flow-field | `references/visual-effects.md` § Particles |
| Shape language | primitives, custom vertices, bezier, SVG paths | `references/shapes-and-geometry.md` |
| Motion style | eased, spring, noise, physics, lerped, stepped | `references/animation.md` |
| Typography | system/OTF, `textToPoints()`, kinetic | `references/typography.md` |
| Shader effects | GLSL fragment/vertex, filter, post-process, feedback | `references/webgl-and-3d.md` § Shaders |
| Composition | grid, radial, golden ratio, thirds, organic scatter, tiled | `references/core-api.md` § Composition |
| Interaction | mouse, click, drag, keyboard, scroll, mic | `references/interaction.md` |
| Blend modes | `BLEND`, `ADD`, `MULTIPLY`, `SCREEN`, `DIFFERENCE`, `EXCLUSION`, `OVERLAY` | `references/color-systems.md` § Blend Modes |
| Layering | `createGraphics()` buffers, alpha, masking | `references/core-api.md` § Offscreen Buffers |
| Texture | Perlin, stipple, hatch, halftone, pixel sort | `references/visual-effects.md` § Texture Generation |

## Design Constraints

Never default:
- palette = designed 3–7 colors, not raw `fill(255, 0, 0)`
- stroke vocabulary = thin 0.5, medium 1–2, bold 3–5
- background = textured/gradient/layered, never plain `background(0)`/`background(255)`
- motion = primary 1x, secondary 0.3x, ambient 0.1x
- invention = at least one custom behavior/noise/interaction

Invent at least one custom mood palette, noise combination, particle behavior, extra interaction, or hierarchy technique. Parameters must expose algorithm character: quantities, scales, rates, thresholds, ratios. Avoid generic `color1`, `color2`, `size`, unrelated toggles, cosmetic-only controls. Each parameter should change how the algorithm thinks, not only looks.

## Procedure

### 1. Creative vision

State mood; visual story; color world; shape language; motion vocabulary; differentiator. Map prompt intentionally: relaxing background ≠ glitch data visualization.

### 2. Technical design

Choose mode; canvas (1920x1080 landscape, 1080x1920 portrait, 1080x1080 square, or responsive `windowWidth/windowHeight`); renderer `P2D` or `WEBGL`; 60fps interactive, 30fps ambient, or `noLoop()` static; browser/PNG/GIF/MP4/SVG target; passive/mouse/keyboard/audio/scroll interaction. Interactive generative art → read `templates/viewer.html` first; simple/video → bare HTML.

### 3. Code

For viewer-template projects, preserve seed prev/next/random/jump, live parameter sliders, and PNG download; replace algorithm/controls. Otherwise use this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Name</title>
  <script>p5.disableFriendlyErrors = true;</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"></script>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/addons/p5.sound.min.js"></script> -->
  <!-- <script src="https://unpkg.com/p5.js-svg@1.6.0"></script> -->  <!-- SVG export -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/ccapture.js-npmfixed/build/CCapture.all.min.js"></script> -->  <!-- video capture -->
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
<script>
// === Configuration ===
const CONFIG = {
  seed: 42,
  // ... project-specific params
};

// === Color Palette ===
const PALETTE = {
  bg: '#0a0a0f',
  primary: '#e8d5b7',
  // ...
};

// === Global State ===
let particles = [];

// === Preload (fonts, images, data) ===
function preload() {
  // font = loadFont('...');
}

// === Setup ===
function setup() {
  createCanvas(1920, 1080);
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  colorMode(HSB, 360, 100, 100, 100);
  // Initialize state...
}

// === Draw Loop ===
function draw() {
  // Render frame...
}

// === Helper Functions ===
// ...

// === Classes ===
class Particle {
  // ...
}

// === Event Handlers ===
function mousePressed() { /* ... */ }
function keyPressed() { /* ... */ }
function windowResized() { resizeCanvas(windowWidth, windowHeight); }
</script>
</body>
</html>
```

Patterns: seeded `randomSeed()` + `noiseSeed()`; `colorMode(HSB, 360, 100, 100, 100)`; CONFIG parameters/PALETTE colors/globals state; classes with `update()` + `display()`; `createGraphics()` buffers for layers/trails/masks.

### 4. Preview

Open directly for basic sketch. Local `loadImage()`/`loadFont()` needs `scripts/serve.sh` or `python -m http.server`; inspect Chrome DevTools Performance for 60fps; test target resolution, not only window; tune against Step 1.

### 5. Export

| Format | Method | Command |
|--------|--------|---------|
| **PNG** | `saveCanvas('output', 'png')` in `keyPressed()` | Press 's' to save |
| **High-res PNG** | Puppeteer headless capture | `node scripts/export-frames.js sketch.html --width 3840 --height 2160 --frames 1` |
| **GIF** | `saveGif('output', 5)` — captures N seconds | Press 'g' to save |
| **Frame sequence** | `saveFrames('frame', 'png', 10, 30)` — 10s at 30fps | Then `ffmpeg -i frame-%04d.png -c:v libx264 output.mp4` |
| **MP4** | Puppeteer frame capture + ffmpeg | `bash scripts/render.sh sketch.html output.mp4 --duration 30 --fps 30` |
| **SVG** | `createCanvas(w, h, SVG)` with p5.js-svg | `save('output.svg')` |

### 6. Verify

Concept match; sharp target resolution/no aliasing; 60fps interactive or 30fps animation; palette harmony on light/dark monitors; edge/resize/10-minute behavior.

## Critical Implementation

### Performance / FES

```javascript
p5.disableFriendlyErrors = true;  // BEFORE setup()

function setup() {
  pixelDensity(1);  // prevent 2x-4x overdraw on retina
  createCanvas(1920, 1080);
}
```

FES can add up to 10x overhead. In hot loops use `Math.*`:

```javascript
// In draw() or update() hot paths:
let a = Math.sin(t);          // not sin(t)
let r = Math.sqrt(dx*dx+dy*dy); // not dist() — or better: skip sqrt, compare magSq
let v = Math.random();        // not random() — when seed not needed
let m = Math.min(a, b);       // not min(a, b)
```

Never `console.log()` or manipulate DOM inside `draw()`.

### Seeded randomness

```javascript
function setup() {
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  // All random() and noise() calls now deterministic
}
```

Never `Math.random()` for generative content; use p5 `random()`; random seed: `CONFIG.seed = floor(random(99999))`.

### fxhash / Art Blocks

```javascript
// fxhash convention
const SEED = $fx.hash;              // unique per mint
const rng = $fx.rand;               // deterministic PRNG
$fx.features({ palette: 'warm', complexity: 'high' });

// In setup():
randomSeed(SEED);   // for p5's noise()
noiseSeed(SEED);

// Replace random() with rng() for platform determinism
let x = rng() * width;  // instead of random(width)
```

See `references/export-pipeline.md` § Platform Export.

### HSB palette

```javascript
colorMode(HSB, 360, 100, 100, 100);
// Now: fill(hue, sat, bri, alpha)
// Rotate hue: fill((baseHue + offset) % 360, 80, 90)
// Desaturate: fill(hue, sat * 0.3, bri)
// Darken: fill(hue, sat, bri * 0.5)
```

Derive variations from palette; no raw RGB values. See `references/color-systems.md`.

### Multi-octave noise

```javascript
function fbm(x, y, octaves = 4) {
  let val = 0, amp = 1, freq = 1, sum = 0;
  for (let i = 0; i < octaves; i++) {
    val += noise(x * freq, y * freq) * amp;
    sum += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / sum;
}
```

Raw `noise(x, y)` gives smooth blobs; domain warp feeds output back into input coordinates.

### Layer buffers

```javascript
let bgLayer, fgLayer, trailLayer;
function setup() {
  createCanvas(1920, 1080);
  bgLayer = createGraphics(width, height);
  fgLayer = createGraphics(width, height);
  trailLayer = createGraphics(width, height);
}
function draw() {
  renderBackground(bgLayer);
  renderTrails(trailLayer);   // persistent, fading
  renderForeground(fgLayer);  // cleared each frame
  image(bgLayer, 0, 0);
  image(trailLayer, 0, 0);
  image(fgLayer, 0, 0);
}
```

### Vectorize draws

```javascript
// SLOW: individual shapes
for (let p of particles) {
  ellipse(p.x, p.y, p.size);
}

// FAST: single shape with beginShape()
beginShape(POINTS);
for (let p of particles) {
  vertex(p.x, p.y);
}
endShape();

// FASTEST: pixel buffer for massive counts
loadPixels();
for (let p of particles) {
  let idx = 4 * (floor(p.y) * width + floor(p.x));
  pixels[idx] = r; pixels[idx+1] = g; pixels[idx+2] = b; pixels[idx+3] = 255;
}
updatePixels();
```

### Instance mode

```javascript
const sketch = (p) => {
  p.setup = function() {
    p.createCanvas(800, 800);
  };
  p.draw = function() {
    p.background(0);
    p.ellipse(p.mouseX, p.mouseY, 50);
  };
};
new p5(sketch, 'canvas-container');
```

Required for multiple sketches/framework integration.

### WebGL

`createCanvas(w, h, WEBGL)` origin = center; positive Y up (unlike P2D); `translate(-width/2, -height/2)` for P2D-like coordinates; `push()`/`pop()` around every transform; `texture()` before `rect()`/`plane()`; test custom `createShader(vert, frag)` across browsers.

### Export keys

```javascript
function keyPressed() {
  if (key === 's' || key === 'S') saveCanvas('output', 'png');
  if (key === 'g' || key === 'G') saveGif('output', 5);
  if (key === 'r' || key === 'R') { randomSeed(millis()); noiseSeed(millis()); }
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
}
```

### Deterministic headless capture

Puppeteer capture requires `noLoop()` in setup; otherwise draw races screenshots. The bundled `scripts/export-frames.js` waits for `_p5Ready` and calls `redraw()` once per frame:

```javascript
function setup() {
  createCanvas(1920, 1080);
  pixelDensity(1);
  noLoop();                    // capture script controls frame advance
  window._p5Ready = true;      // signal readiness to capture script
}
```

Multi-scene video → one HTML per scene, independent render, `ffmpeg -f concat`; see `references/export-pipeline.md` § Per-Clip Architecture.

## Agent Sequence

1. Write single inline HTML.
2. Open: `open sketch.html` macOS or `xdg-open sketch.html` Linux.
3. Local assets: `python -m http.server 8080`, then `http://localhost:8080/sketch.html`.
4. PNG/GIF: include `keyPressed()`; tell user keys.
5. Headless: `node scripts/export-frames.js sketch.html --frames 300`; requires `noLoop()` + `_p5Ready`.
6. MP4: `bash scripts/render.sh sketch.html output.mp4 --duration 30`.
7. Iterate by editing HTML + refresh.
8. Load `skill_view(name="p5js", file_path="references/...")` on demand.

## Targets

| Metric | Target |
|--------|--------|
| Frame rate (interactive) | 60fps sustained |
| Frame rate (animated export) | 30fps minimum |
| Particle count (P2D shapes) | 5,000-10,000 at 60fps |
| Particle count (pixel buffer) | 50,000-100,000 at 60fps |
| Canvas resolution | Up to 3840x2160 (export), 1920x1080 (interactive) |
| File size (HTML) | < 100KB (excluding CDN libraries) |
| Load time | < 2s to first frame |

## References

| File | Contents |
|------|----------|
| `references/core-api.md` | canvas, coordinates, draw, `push()`/`pop()`, buffers, composition, `pixelDensity()`, responsive |
| `references/shapes-and-geometry.md` | primitives, shapes, Bezier/Catmull-Rom, vertices, `p5.Vector`, SDF, SVG |
| `references/visual-effects.md` | noise, flow fields, particles, pixels, textures, feedback, reaction-diffusion |
| `references/animation.md` | frame/easing, lerp/map, springs, state machines, timelines, millis, transitions |
| `references/typography.md` | text/loadFont/textToPoints, kinetic type, masks, metrics, responsive sizing |
| `references/color-systems.md` | color modes, lerp, palettes/harmony, blend modes, gradients, palette library |
| `references/webgl-and-3d.md` | WEBGL, primitives, camera, lighting, materials, geometry, GLSL, framebuffers |
| `references/interaction.md` | mouse/keyboard/touch/DOM, sliders/buttons, FFT/amplitude, scroll, responsive events |
| `references/export-pipeline.md` | save APIs, deterministic capture, ffmpeg, CCapture, SVG, clips, fxhash |
| `references/troubleshooting.md` | performance, budgets, browser/WebGL, fonts, density, leaks, CORS |
| `templates/viewer.html` | seed navigation, parameter sliders, PNG download, responsive canvas |

## Creative Divergence

Only when requested: experimental, surprising, unconventional. Choose and reason before code.

- Conceptual Blending: name two visual systems (particle physics + handwriting) → map particles/forces/fields to ink/pressure/letterforms → keep emergent mappings → code one unified system.
- SCAMPER: transform flow/particles/L-system/cellular automata: substitute circles→text, lines→gradients; combine flow+voronoi; adapt 2D→3D; modify scale/warp; purpose physics for typography/sorting for color; eliminate grid/color/symmetry; reverse simulation/parameter space.
- Distance Association: anchor concept (e.g. loneliness); generate close (empty room/single figure/silence), medium (wrong-way fish, phone with no notifications, subway-car gap), far (prime numbers, asymptotic curves, color of 3am); develop medium associations.

## Pitfalls

- do not claim deterministic output without controlling seeds, readiness, and frame advancement
- avoid per-particle allocations and unbounded draw work when the target frame budget cannot support them
- preserve the browser-origin/CORS and WebGL constraints of the selected export path

## Verification

- HTML opens and console is clean; seeded output is reproducible
- palette/background/layers/motion match concept; one invented element exists
- target frame rate/resolution/load time or documented degradation
- export file is playable/valid; key bindings and headless readiness work
