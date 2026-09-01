---
name: draw-your-font
description: "Turn a handwriting photo into an installable TTF font."
version: 0.1.0
author: Danilo Znamerovszkij (https://github.com/danilo-znamerovszkij/draw-your-font), ported by Hermes Agent
license: MIT
platforms: [linux, macos, windows]
required_commands: [node, npx]
metadata:
  hermes:
    tags: [font, handwriting, typography, ttf, woff, vision, creative]
    category: creative
    homepage: https://github.com/danilo-znamerovszkij/draw-your-font
    related_skills: [pixel-art]
---

# draw-your-font

role: photo-to-font visual reviewer + draw-your-font CLI operator
do: inspect/label handwriting; run template|segment|build|preview; judge outputs; refine; deliver paths/install advice
inputs: photo paths; charset; labels; font name; refinement/format requests
outputs: TTF/web formats; preview/legibility findings; missing letters; install path
¬: edit SVG paths/coordinates; infer a photo from memory; proceed without a real file path; gate delivery on legibility

Photo of handwritten letters → installable font. Agent does visual work
(find/label letters; judge quality); CLI does geometry (trace, metrics, assembly).
Never edit SVG paths or coordinates.

## Setup in Hermes (once per session)

CLI: pinned npm package `draw-your-font@0.1.0`; run via npx (Node ≥ 18; no global install):

```bash
npx -y draw-your-font@0.1.0 --help
```

Replace `$DYF` below with `npx -y draw-your-font@0.1.0` each call; shell variables do not persist. All processing is local; handwriting stays on the machine.

Photo input may be a message path or gateway image-cache file; pass the actual path. Image without a path → ask the user to drag the file into the terminal (inserts its path) or give the path directly; CLI needs a real file, not memory.

Visual steps (contact sheets, previews, glyph sheets) → load PNGs with `vision_analyze`.

## When to Use

- no photo → offer the template: print, write, photograph
- photo path(s) → use the main flow
- image without a file path → ask for a path; do not proceed from memory
- font built this session needs changes → use Refine

## Template flow (best quality)

```bash
$DYF template -o template.pdf --charset minimal   # or: spanish
```

Tell the user: print; write one character per box with a dark pen (0.5 mm+),
keep each letter on the solid line; photograph each page from above in good
light; share file paths. Grid is light grey and vanishes during processing;
only ink survives.

## Main flow: photo(s) → font

**1. Segment.** Use for template pages and freeform photos alike:

```bash
$DYF segment photo1.jpg photo2.jpg -d work
```

**2. Look, then label.** Load `work/contact-1.png` with `vision_analyze` (one
per photo); every detected blob is numbered. Check:

- one box per written character; separate strokes can produce two boxes → give
  the main box its character and the fragment `""`; touching letters can share
  one box → ask for a re-shoot or accept the gap
- junk boxes (shadows, ruled lines, smudges, page edges) → `""`

Write `work/labels.json`, blob id → character, e.g.
`{"0": "A", "1": "B", "7": "", "8": "a"}`:

- template: verify printed charset order against the sheet; minimal = A–Z,
  a–z, 0–9, then `.,;:!?'"-()@#&+/$`; Spanish appends `ÑñÁÉÍÓÚáéíóúü¿¡`
- freeform: identify each letter from the contact sheet; use relative size and
  position for shape-twins (S/s, O/o, C/c, X/x…), comparing known neighbors
- user-provided sequence (e.g. "ABC then abc") → trust it; map top row first,
  left to right, then verify visually
- duplicate letter → label the better drawing; label the other `""`

**3. Build.**

```bash
$DYF build -d work --labels work/labels.json --name "Dan's Hand"
```

Name the font after the user; if unclear, ask one short question maximum.

**4. Judge before delivering.** Load `work/preview.png` and `work/glyphs.png`
with `vision_analyze`; critique as an art director:

- broken/blotchy letters (bad trace) → often faint ink; try `--weight 1`, or
  request a re-shoot of that letter
- all too thin/thick → rebuild with `--weight 1` / `--weight -1`
- jagged edges → rebuild with `--smooth 1.5` (up to 2)
- wrong placement (e.g. `g` not descending) → usually mislabel; fix labels.json and rebuild
- filled-in bowls (b, o, g solid) → never expected; crop is smudged; request a re-shoot

Rebuilds are cheap/safe: fix what you can first; request re-shoots only when source ink is the problem.

**5. Deliver.** Output is `<workdir>/<NameWithoutSpaces>.ttf`; build output
prints the exact path. Give it plus installation:
macOS - double-click → "Install Font"; Windows - right-click → "Install".
Mention uncovered letters (build prints them). Offer, without pushing:

- Web formats + CSS: rebuild with `--formats ttf,woff,woff2,css`.
- A legibility read (below).
- next photo to fill missing characters: re-run segment with ALL old+new photos
  in a fresh workdir - `$DYF segment p1.jpg p2.jpg -d work2` - then relabel from
  new contact sheets (blob ids renumber; old labels.json does not carry over)
  and build from the new workdir

## Refine (conversational iteration)

| User says | Do |
|---|---|
| "smoother / rounder" | `build … --smooth 1.5` (max 2) |
| "thicker / bolder" | `build … --weight 1` (max 2) |
| "thinner / lighter" | `build … --weight=-1` (negative needs the `=` form) |
| "the g looks bad" | show them `work/crops/<id>.png` for that letter; offer re-shoot or smooth |
| "wrong letter" / swap | edit labels.json, rebuild |
| "give me woff2 / web" | `build … --formats ttf,woff,woff2,css` |
| custom preview text | `$DYF preview -d work --text "…"` (after a build) |

Refine commands rebuild from stored crops; no re-photographing unless ink is the problem.

## Legibility report (offer after delivering)

```bash
$DYF preview -d work --text "minimum mill rn m cl d I l 1 O 0 quick brown fox" -o work/legibility.png
```

Read it kindly and honestly: score body-text use 0–10; name 2–3 likely-confused
pairs (rn→m, cl→d, I/l/1, O/0); give 1–2 fixes (rewrite larger, add spacing).
Display use (headings, notes) is more forgiving than paragraphs. Advice only;
never gate delivery on it.

## Troubleshooting

Too many/few blobs, surviving grey guide lines, shadow blobs, or faint
ballpoint strokes → see `references/troubleshooting.md`.
