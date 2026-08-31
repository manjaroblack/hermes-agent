---
name: pretext
description: Build creative browser demos with DOM-free text layout.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, typography, pretext, ascii-art, canvas, generative, text-layout, kinetic-typography]
    related_skills: [p5js, claude-design, excalidraw, architecture-diagram]
---

# Pretext Creative Demos

role: creative browser-demo builder
do: use `@chenglou/pretext` to measure/layout real text without DOM reflow, then render a deliberate interactive visual
inputs: prose/script/poetry, font, width, obstacle geometry, interaction, palette
outputs: one self-contained `.html` demo
¬: CSS-only static layout; rich-text editor; image→text (`ascii-art`/`ascii-video`); canvas art with no text role (`p5js`); lorem ipsum; blank/default first paint

[`@chenglou/pretext`](https://github.com/chenglou/pretext) is Cheng Lou's 15KB zero-dependency TypeScript library (React core, ReasonML, Midjourney) for **DOM-free multiline text measurement and layout**. Given `(text, font, width)`, it returns line breaks, per-line widths, per-grapheme positions, and total height through canvas measurement, without reflow. It is a creative primitive: text can flow around a moving sprite, become game geometry, drive ASCII logos, or shatter into particles with exact positions. See `pretext.cool` and `chenglou.me/pretext` for community demos.

## When to Use

- "pretext demo", "cool pretext thing", or "text-as-X"
- text around a moving shape; hero/editorial/animated long-form layout
- ASCII effects made from real words/prose, not monospace rasters
- text playfields, Tetris-from-letters, Breakout-of-prose
- kinetic typography with per-glyph shatter/scatter/flock/flow
- typographic generative art with non-Latin or mixed scripts
- multiline shrink-wrap UI; known line breaks before rendering

## Creative Standard

- `hello-orb-flow.html` is a starting point, never the finished brief.
- choose a considered palette: amber-on-black CRT/terminal, cold white on charcoal editorial, or desaturated risograph pastels
- proportional fonts are the point; try Iowan Old Style, Inter, JetBrains Mono, Helvetica Neue, or a variable font; never default sans
- use meaningful source text (manifesto, poetry, real source code, found text, library README), never `lorem ipsum`
- first paint must be shippable: no blank/loading frame; add intentional color, motion, composition, and one appreciated extra detail

## Stack

Single self-contained HTML; no build step.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | `@chenglou/pretext` via `esm.sh` CDN | Text measurement + line layout |
| Render | HTML5 Canvas 2D | Glyph rendering, per-frame composition |
| Segmentation | `Intl.Segmenter` (built-in) | Grapheme splitting for emoji / CJK / combining marks |
| Interaction | Raw DOM events | Mouse / touch / wheel — no framework |

```html
<script type="module">
import {
  prepare, layout,                   // use-case 1: simple height
  prepareWithSegments, layoutWithLines,  // use-case 2a: fixed-width lines
  layoutNextLineRange, materializeLineRange, // use-case 2b: streaming / variable width
  measureLineStats, walkLineRanges,  // stats without string allocation
} from "https://esm.sh/@chenglou/pretext@0.0.6";
</script>
```

Pin the version; `@0.0.6` is the version at writing. Check [npm](https://www.npmjs.com/package/@chenglou/pretext) if behavior is off.

## API Patterns

### 1. Measure, render with CSS/DOM

```js
const prepared = prepare(text, "16px Inter");
const { height, lineCount } = layout(prepared, 320, 20);
```

Pretext computes box height without a DOM read. Use for virtualized wrapping rows, precise masonry heights, fit checks, and preventing layout shift. Keep `font` and `letterSpacing` exactly synchronized with CSS; `ctx.font` such as `"16px Inter"` or `"500 17px 'JetBrains Mono'"` must match rendered CSS.

### 2. Measure and render yourself

```js
const prepared = prepareWithSegments(text, FONT);
const { lines } = layoutWithLines(prepared, 320, 26);
for (let i = 0; i < lines.length; i++) {
  ctx.fillText(lines[i].text, 0, i * 26);
}
```

Render to canvas/SVG/WebGL/any coordinate system; apply per-glyph rotation/jitter/scale/opacity; treat line metadata as geometry.

For variable corridor widths (shape wrap, donut band, non-rectangular column):

```js
let cursor = { segmentIndex: 0, graphemeIndex: 0 };
let y = 0;
while (true) {
  const lineWidth = widthAtY(y);  // your function: how wide is the corridor at this y?
  const range = layoutNextLineRange(prepared, cursor, lineWidth);
  if (!range) break;
  const line = materializeLineRange(prepared, range);
  ctx.fillText(line.text, leftEdgeAtY(y), y);
  cursor = range.end;
  y += lineHeight;
}
```

This is the core pattern for text flowing around dragged sprites.

### Helpers

- `measureLineStats(prepared, maxWidth)` → `{ lineCount, maxLineWidth }` for multiline shrink-wrap width
- `walkLineRanges(prepared, maxWidth, callback)` for stats/physics without string allocation
- `@chenglou/pretext/rich-inline` for paragraphs mixing fonts/chips/mentions

## Demo Patterns

The community corpus in `references/patterns.md` supplies the pattern families below; riff on one rather than inventing a new category unless asked.

| Pattern | Key API | Example |
|---|---|---|
| Reflow around obstacle | `layoutNextLineRange` + per-row width function | Editorial paragraph parts around a dragged cursor sprite |
| Text-as-geometry game | `layoutWithLines` + per-line collision rects | Breakout with measured word bricks |
| Shatter / particles | `walkLineRanges` → per-grapheme `(x,y)` → physics | Sentence explodes into letters on click |
| ASCII obstacle typography | `layoutNextLineRange` + measured per-row obstacle spans | Bitmap ASCII logo, shape morphs, draggable wire objects open text around actual geometry |
| Editorial multi-column | `layoutNextLineRange` per column + shared cursor | Animated magazine spread with pull quotes |
| Kinetic type | `layoutWithLines` + per-line transforms | Star Wars crawl, wave, bounce, glitch |
| Multiline shrink-wrap | `measureLineStats` | Quote card auto-sizes to tightest container |

Templates: `templates/donut-orbit.html` (measured ASCII logo obstacles, draggable wire sphere/cube, morphing shape fields, selectable DOM text, dev controls) and `templates/hello-orb-flow.html` (moving orb reflow).

## Procedure

1. Select a pattern based on the brief.
2. `write_file` a new `.html` in `/tmp/` or the user's workspace, starting from the matching template.
3. Replace corpus with 10–100 sentences of intentional real prose.
4. Tune font, palette, composition, and interaction; do not skip the aesthetic work.
5. Verify locally:

```sh
cd <dir-with-html> && python -m http.server 8765
# then open http://localhost:8765/<file>.html
```

6. Check console; bad font strings can make `prepareWithSegments` throw; `Intl.Segmenter` exists in modern browsers.
7. Return the file path, not only source.

## Performance

- `prepare()`/`prepareWithSegments()` once per text+font; cache handle
- resize reruns `layout()`/`layoutWithLines()`, never re-prepare or thrash `getBoundingClientRect`
- `layoutNextLineRange` is cheap enough per frame for normal paragraphs
- ASCII masks: keep a `Uint8Array`/typed cell buffer; derive/merge measured per-row obstacle spans before `layoutNextLineRange`
- couple rendered cell buffer and obstacle spans with same tween when shape morphs
- fade transient ASCII sprites by layer opacity/CSS/GSAP, not glyph intensity or obstacle scale
- set `ctx.font` once per frame, not per `fillText`

## Pitfalls

1. CSS/canvas font drift: `ctx.font = "16px Inter"` vs CSS `font-family: Inter, sans-serif; font-size: 16px`; preload Inter or use a web-safe family because fallback changes measurements.
2. Re-preparing in animation; only `layout*` is cheap.
3. `"é".split("")` splits visible grapheme; use `new Intl.Segmenter(undefined, { granularity: "grapheme" })` for emoji/combining/CJK.
4. `rich-inline` `break: 'never'` chips need `extraWidth` for pill padding.
5. `unpkg` serves raw TypeScript/404; use `esm.sh`.
6. Verify actual rendered font; monospace fallback defeats proportional design.
7. If corridor is too narrow, skip row (`y += lineHeight; continue;`) instead of tiny `maxWidth` that yields one-grapheme lines.
8. Default first paint is tutorial-grade; add vignette, scanline, idle motion, and one deliberate interaction.

## Verification

- one HTML opens by double-click or `python -m http.server`
- pinned `esm.sh` import; real corpus matches concept
- canvas font and CSS match; prepare called once
- dark/considered palette, interactive response or idle motion, extra-mile detail
- local server test has no console errors; 60fps on mid-tier laptop or documented degradation

## Community References

All linked from [pretext.cool](https://www.pretext.cool/):

- Pretext Breaker — `github.com/rinesh/pretext-breaker`
- Tetris × Pretext — `github.com/shinichimochizuki/tetris-pretext`
- Dragon animation — `github.com/qtakmalay/PreTextExperiments`
- Somnai editorial engine — `github.com/somnai-dreams/pretext-demos`
- Bad Apple!! ASCII — `github.com/frmlinn/bad-apple-pretext`
- Drag-sprite reflow — `github.com/dokobot/pretext-demo`
- Alarmy editorial clock — `github.com/SmisLee/alarmy-pretext-demo`

Official playground: [chenglou.me/pretext](https://chenglou.me/pretext/) — accordion, bubbles, dynamic-layout, editorial-engine, justification-comparison, masonry, markdown-chat, rich-note.
