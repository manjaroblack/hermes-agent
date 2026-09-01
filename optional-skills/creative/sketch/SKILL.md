---
name: sketch
description: "Throwaway HTML mockups: 2-3 design variants to compare."
version: 1.0.1
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sketch, mockup, design, ui, prototype, html, variants, exploration, wireframe, comparison]
    related_skills: [spike, claude-design, popular-web-designs, excalidraw]
---

# Sketch

role: disposable UI/UX explorer
do: build 2–3 interactive standalone HTML variants so the user can compare directions before committing
inputs: screen/flow brief, feel, references, core action, existing theme
outputs: `sketches/NNN-stance-name/index.html` + `README.md` per variant; head-to-head recommendation
¬: production component; polished one-off landing/deck (`claude-design`); diagram (`excalidraw`/`architecture-diagram`); locked design; frozen screenshot; one variant

## When to Use

Load for "sketch this screen", "show me what X could look like", "compare layout A vs B", "give me 2-3 takes", "let me see variants", or "mockup this before I build".

## GSD Note

If sibling `gsd-sketch` is installed via `npx get-shit-done-cc --hermes --global`, use its `/gsd-sketch` workflow for persistent `.planning/sketches/`, MANIFEST, frontier analysis, consistency audits, and GSD integration. This is the lightweight one-off path. Upstream [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) is archived/unmaintained; `get-shit-done-cc` still installs but is an archived community project.

## Attribution

Adapted from GSD `/gsd-sketch`; MIT © 2025 Lex Christopherson
([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). Upstream
is archived/unmaintained; `get-shit-done-cc` still installs via
`npx get-shit-done-cc --hermes --global` and provides persistent sketch state,
theme/variant references, and consistency audits. This standalone `sketch` path
is maintained and needs no extra setup.

## Procedure

```text
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. Intake

Skip if brief already answers all three. Ask one at a time and reflect briefly:

1. **Feel:** "What should this feel like? Adjectives, emotions, a vibe." (`"calm, editorial, like Linear"` beats `"minimal"`.)
2. **References:** "What apps, sites, or products capture the feel you're imagining?" Actual references beat abstractions.
3. **Core action:** "What's the single most important thing a user does on this screen?" Every variant serves this action.

### 2. Variants

Produce **2–3**, never 1, rarely 4+. Build complete standalone files; do not merely describe them. Choose one contrasting stance axis:

- density: compact / airy / ultra-dense
- emphasis: content-first / action-first / tool-first
- aesthetic: editorial / utilitarian / playful
- layout: single-column / sidebar / split-pane
- grounding: card-based / bare-content / document-style

Variants must differ structurally, not only in accent color. Name the stance:

```text
sketches/
├── 001-calm-editorial/
│   ├── index.html
│   └── README.md
├── 001-utilitarian-dense/
│   ├── index.html
│   └── README.md
└── 001-playful-split/
    ├── index.html
    └── README.md
```

### 3. Real HTML

Each file:

- inline `<style>`, no build step/no external CSS
- system fonts or one Google Font via `<link>`
- Tailwind CDN allowed: `<script src="https://cdn.tailwindcss.com"></script>`
- realistic actual sentences/names, no `Lorem ipsum`
- links clickable, real hovers, at least one state transition (open/close, filter, toggle)

Open and fix before showing. Verify every variant with browser tools:

```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` sees the rendered page/screenshot and catches failed fonts, collapsed flex containers, and broken images that source inspection misses. Re-navigate after fixes.

Default reset:

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #1a1a1a;
    background: #fafafa;
    line-height: 1.5;
  }
</style>
```

### 4. Variant README

```markdown
## Variant: {stance name}

### Design stance
One sentence on the principle driving this variant.

### Key choices
- Layout: ...
- Typography: ...
- Color: ...
- Interaction: ...

### Trade-offs
- Strong at: ...
- Weak at: ...

### Best for
- The kind of user or use case this variant actually serves
```

### 5. Head-to-Head

After building, compare and give an opinion:

```markdown
## Three takes on the home screen

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Primary action visibility | Low | High | Medium |
| Scan-ability | High | Medium | Low |
| Feel | Calm, trusted | Sharp, tool-like | Inviting, energetic |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences. Playful split is weakest — tries to do both and commits to neither.
```

User may pick, hybridize, or request another round.

## Theming

For an existing visual identity, put shared tokens in `sketches/themes/tokens.css` and `@import` into each variant:

```css
/* sketches/themes/tokens.css */
:root {
  --color-bg: #fafafa;
  --color-fg: #1a1a1a;
  --color-accent: #0066ff;
  --color-muted: #666;
  --radius: 8px;
  --font-display: "Inter", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

Do not over-tokenize a throwaway: three colors and one font usually suffice.

## Interactivity Bar

A sketch passes when the user can:

1. click a primary action and see a state/modal/toast/navigation feint
2. see one meaningful transition (filter, mode toggle, panel open/close)
3. hover recognizable buttons/rows/tabs

More = over-engineering; less = screenshot.

## Frontier Mode

For "what should I sketch next?" propose 2–4 named candidates from:

- consistency gaps between independent winning variants
- referenced but unsketched screens
- missing empty/loading/error/1000-items states
- responsive gap (mobile/ultrawide)
- static layouts without transition/drag/scroll interaction

Let the user pick.

## Output

Create `sketches/` (or `.planning/sketches/` under GSD conventions) in repo root. Each variant gets `NNN-stance-name/index.html` + `README.md`. Tell user: `open sketches/001-calm-editorial/index.html` macOS; `xdg-open` Linux; `start` Windows. Keep disposable; promote a winner into project code rather than curating a sketch asset.

Typical sequence:

```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

Repeat for each variant, then return the comparison table and recommendation.

## Pitfalls

- do not polish one direction before the requested 2–3 variants exist and share the same brief
- keep sketches disposable; do not silently promote mockup code into production files
- browser-render every variant before recommending a winner; screenshots alone do not prove interaction

## Verification

- 2–3 files exist, each complete, standalone, interactive, realistic, and disposable
- browser-render every variant; no visible overlaps/unstyled elements/broken images and no unverified claims
- stance, choices, trade-offs, best-for recorded in each README
- comparison is opinionated; winner/hybrid/next round is explicit
