---
name: excalidraw
description: "Hand-drawn Excalidraw JSON diagrams (arch, flow, seq)."
version: 1.0.1
author: Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Excalidraw, Diagrams, Flowcharts, Architecture, Visualization, JSON]
    related_skills: []

---

# Excalidraw Diagram

role: Excalidraw JSON author
do: write standard element JSON for architecture, flow, sequence, concept, and similar diagrams
inputs: diagram graph, labels, positions, colors, bindings
outputs: `.excalidraw` envelope; optional shareable excalidraw.com URL
¬: invalid `label` property; duplicate IDs; stale/nonstandard shapes; emoji text; unverified uploads

No account, API key, or rendering library is needed. Save with `write_file`; drag onto [excalidraw.com](https://excalidraw.com) for viewing/editing.

## When to Use

Use for architecture diagrams, flowcharts, sequence diagrams, concept maps, and other hand-drawn diagrams. For polished dark technical SVG/HTML use `architecture-diagram`.

## Procedure

1. Build an elements array with unique IDs.
2. Save standard envelope below to `.excalidraw` with `write_file`.
3. Optionally upload using `scripts/upload.py` via `terminal`.
4. Open at excalidraw.com and inspect bindings, text, z-order, contrast.

### Envelope

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

Any path is valid, e.g. `~/diagrams/my_diagram.excalidraw`.

### Upload

```bash
python skills/creative/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

Upload prints a shareable URL; no account. Requires `cryptography` (`pip install cryptography`).

## Element Contract

All elements require `type`, unique string `id`, `x`, `y`, `width`, `height`.

Defaults (omit unless overriding): `strokeColor: "#1e1e1e"`; `backgroundColor: "transparent"`; `fillStyle: "solid"`; `strokeWidth: 2`; `roughness: 1`; `opacity: 100`. Canvas = white.

### Shapes

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```

Rounded: `roundness: { "type": 3 }`; filled: `backgroundColor: "#a5d8ff", fillStyle: "solid"`.

```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

### Labeled Shape: binding required

**Do not use** `"label": { "text": "..." }`; it is invalid Excalidraw and silently creates blank shapes. Shape `boundElements` lists text; text `containerId` points back:

```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```

Works rectangle/ellipse/diamond. `containerId` auto-centers; text geometry is approximate and recalculated on load; `originalText` = `text`; always `fontFamily: 1` (Virgil).

### Labeled Arrow

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

### Text

Standalone titles/annotations:

```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```

`x` is left edge. Center at `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`. Do not rely on `textAlign`/`width` for placement.

### Arrow + bindings

```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```

`points` = `[dx, dy]` from element x/y. `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"`; `strokeStyle`: `"solid"` | `"dashed"` | `"dotted"`.

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

Fixed points: top `[0.5,0]`; bottom `[0.5,1]`; left `[0,0.5]`; right `[1,0.5]`.

## Z-Order

Array order = z-order (first back, last front). Emit progressively: background zones → shape → bound text → arrows → next shape. Bad: all rectangles, then texts, then arrows. Good:

`bg_zone → shape1 → text_for_shape1 → arrow1 → arrow_label_text → shape2 → text_for_shape2 → ...`

Bound text must immediately follow its container.

## Sizing

- body/labels/descriptions `fontSize` ≥16
- titles/headings ≥20
- secondary annotations ≥14, sparingly; never below 14
- labeled shapes ≥120×60
- gaps 20–30px minimum; prefer fewer/larger elements

## Palette + Tips

See `references/colors.md`; quick palette:

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

Use colors consistently. Text contrast on white is critical; minimum text color `#757575`. No emoji text; see `references/dark-mode.md` for dark mode and `references/examples.md` for larger examples.

## Pitfalls

- never create a labeled shape without the matching `containerId` binding and `originalText`
- do not rely on visual proximity alone for arrows; bind both ends to the intended elements
- do not upload malformed JSON or expose the upload URL before local validation succeeds

## Verification

- valid JSON envelope; all required fields and unique IDs
- shape labels use bindings, `originalText` matches `text`, `fontFamily: 1`
- arrows use valid points/head/bindings; array z-order is intentional
- font sizes/gaps/contrast meet contract; no emoji
- saved file opens at excalidraw.com; upload URL only after script succeeds
