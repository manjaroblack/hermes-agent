---
name: baoyu-comic
description: "Knowledge comics (知识漫画): educational, biography, tutorial."
version: 1.56.1
author: 宝玉 (JimLiu)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [comic, knowledge-comic, creative, image-generation]
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-comic
---

# Knowledge Comic Creator

role: knowledge-comic production operator
do: ingest/analyze source; preserve language; resolve references; confirm style/options; storyboard; define characters; save prompts; generate/download pages; review/finalize
inputs: topic/text/file/URL, optional reference images, art/tone/layout/aspect/language, partial-workflow choice
outputs: source, analysis, storyboard, character definitions/sheet, prompt files, downloaded page PNGs, completion report
¬: pass reference PNG to `image_generate`; generate before prompt save; hide timeout defaults; use relative download paths; skip required confirmation; alter source facts; expose secrets

Create original educational, biography, tutorial, or Logicomix-style knowledge comics from text, files, URLs, or topics. Adapted from [baoyu-comic](https://github.com/JimLiu/baoyu-skills) for Hermes tools.

## When to Use

- `知识漫画`, `教育漫画`, biography/tutorial comic, or Logicomix-style request
- source content plus optional art style, tone, layout, aspect, language, or reference image
- storyboard-only, prompts-only, images-only, or page regeneration workflow

## Prerequisites

- source content or topic; output directory decision
- `clarify`, `vision_analyze`, `image_generate`, `terminal`, `read_file`, `write_file`
- `image_generate` is prompt-only: accepts `prompt` + `aspect_ratio`, returns URL, no reference-image input

## Reference Images

Extract traits as text; never pass a reference image to `image_generate`.

- path/attachment → copy to `refs/NN-ref-{slug}.{ext}` for provenance
- pasted image without path → ask path via `clarify`, or use a verbal text fallback
- no reference → skip

| Usage | Effect |
|-------|--------|
| `style` | Extract style traits (line treatment, texture, mood) and append to every page's prompt body |
| `palette` | Extract hex colors and append to every page's prompt body |
| `scene` | Extract scene composition or subject notes and append to the relevant page(s) |

When refs exist, record each in page prompt frontmatter:

```yaml
references:
  - ref_id: 01
    filename: 01-ref-scene.png
    usage: style
    traits: "muted earth tones, soft-edged ink wash, low-contrast backgrounds"
```

Character consistency uses text in `characters/characters.md`, embedded inline in every page prompt. Optional `characters/characters.png` is a human review/regeneration artifact only; it is not model input.

## Options

### Visual

| Option | Values | Description |
|--------|--------|-------------|
| Art | ligne-claire (default), manga, realistic, ink-brush, chalk, minimalist | Art style / rendering technique |
| Tone | neutral (default), warm, dramatic, romantic, energetic, vintage, action | Mood / atmosphere |
| Layout | standard (default), cinematic, dense, splash, mixed, webtoon, four-panel | Panel arrangement |
| Aspect | 3:4 (default, portrait), 4:3 (landscape), 16:9 (widescreen) | Page aspect ratio |
| Language | auto (default), zh, en, ja, etc. | Output language |
| Refs | File paths | Reference images used for style / palette trait extraction (not passed to the image model). See [Reference Images](#reference-images) above. |

### Partial workflows

| Option | Description |
|--------|-------------|
| Storyboard only | Generate storyboard only, skip prompts and images |
| Prompts only | Generate storyboard + prompts, skip images |
| Images only | Generate images from existing prompts directory |
| Regenerate N | Regenerate specific page(s) only (e.g., `3` or `2,5,8`) |

Details: `references/partial-workflows.md`.

### Presets

  | Preset | Equivalent | Hook |
  |--------|-----------|------|
  | `ohmsha` | manga + neutral | Visual metaphors, no talking heads, gadget reveals |
  | `wuxia` | ink-brush + action | Qi effects, combat visuals, atmospheric |
  | `shoujo` | manga + romantic | Decorative elements, eye details, romantic beats |
  | `concept-story` | manga + warm | Visual symbol system, growth arc, dialogue+action balance |
  | `four-panel` | minimalist + neutral + four-panel layout | 起承转合 structure, B&W + spot color, stick-figure characters |

Full definitions: `references/art-styles/<style>.md`, `references/tones/<tone>.md`, `references/presets/<preset>.md`, `references/auto-selection.md`.

## File Contract

Output: `comic/{topic-slug}/`, slug=2-4 kebab-case words; conflict→timestamp, e.g. `turing-story-20260118-143052`.

| File | Description |
|------|-------------|
| `source-{slug}.md` | Saved source content (kebab-case slug matches the output directory) |
| `analysis.md` | Content analysis |
| `storyboard.md` | Storyboard with panel breakdown |
| `characters/characters.md` | Character definitions |
| `characters/characters.png` | Character reference sheet (downloaded from `image_generate`) |
| `prompts/NN-{cover\|page}-[slug].md` | Generation prompts |
| `NN-{cover\|page}-[slug].png` | Generated images (downloaded from `image_generate`) |
| `refs/NN-ref-{slug}.{ext}` | User-supplied reference images (optional, for provenance) |

## Language Contract

Detection priority: explicit user language → conversation language → source language. Use the selected user/input language for storyboard, scene descriptions, prompts, options, confirmations, progress, errors, and summaries. Technical terms stay English.

## Procedure

### Progress gate

```
Comic Progress:
- [ ] Step 1: Setup & Analyze
  - [ ] 1.1 Analyze content
  - [ ] 1.2 Check existing directory
- [ ] Step 2: Confirmation - Style & options ⚠️ REQUIRED
- [ ] Step 3: Generate storyboard + characters
- [ ] Step 4: Review outline (conditional)
- [ ] Step 5: Generate prompts
- [ ] Step 6: Review prompts (conditional)
- [ ] Step 7: Generate images
  - [ ] 7.1 Generate character sheet (if needed) → characters/characters.png
  - [ ] 7.2 Generate pages (with character descriptions embedded in prompt)
- [ ] Step 8: Completion report
```

Flow: `Input → Analyze → [Check Existing?] → [Confirm: Style + Reviews] → Storyboard → [Review?] → Prompts → [Review?] → Images → Complete`.

| Step | Action | Key Output |
|------|--------|------------|
| 1.1 | Analyze content | `analysis.md`, `source-{slug}.md` |
| 1.2 | Check existing directory | Handle conflicts |
| 2 | Confirm style, focus, audience, reviews | User preferences |
| 3 | Generate storyboard + characters | `storyboard.md`, `characters/` |
| 4 | Review outline (if requested) | User approval |
| 5 | Generate prompts | `prompts/*.md` |
| 6 | Review prompts (if requested) | User approval |
| 7.1 | Generate character sheet (if needed) | `characters/characters.png` |
| 7.2 | Generate pages | `*.png` files |
| 8 | Completion report | Summary |

### 1. Setup and analyze

Read source, save source copy, analyze content, detect existing output directory, and handle conflicts before generation.

### 2. Confirm options

Use `clarify` sequentially; ask the important question first and skip answers already supplied. Critical timeout behavior: if `clarify` returns `"The user did not provide a response within the time limit. Use your best judgement to make the choice and proceed."`, default only that question; continue remaining questions; visibly tell the user the default, e.g. `Style: defaulted to ohmsha preset (clarify timed out). Say the word to switch.` Do not collapse all five questions into invisible defaults. Ask no more than 2-3 in a row.

### 3. Storyboard and characters

Generate `storyboard.md` and text character definitions. Embed those descriptions into every page prompt.

### 4-6. Review and prompt records

Honor requested outline/prompt review gates. Before any `image_generate`, save every full final prompt under `prompts/NN-{cover|page}-[slug].md`; prompt files are reproducibility records.

### 7. Generate images

1. Use `image_generate` with only `prompt` and `aspect_ratio`.
2. Map storyboard ratio: `3:4`, `9:16`, `2:3`→`portrait`; `4:3`, `16:9`, `3:2`→`landscape`; `1:1`→`square`.
3. Read returned URL; download bytes with an **absolute** path, e.g. `curl -fsSL "<url>" -o /abs/path/to/comic/<slug>/NN-page-<slug>.png`.
4. Verify exact path exists and is non-empty before the next page.
5. Retry generation once on failure.

Never rely on shell CWD persistence: `curl -o relative/path.png` can silently land in the wrong directory after session/CWD drift.

#### 7.1 Character sheet

For recurring characters in multi-page comics, write `characters/characters.md`, save its prompt before generation, then generate/download `characters/characters.png` with `landscape`. Skip for one-page/simple presets such as four-panel minimalist. The PNG is for human review/regeneration; page prompts always use text descriptions because image input is unsupported.

#### 7.2 Pages and backups

Each page prompt must exist before generation. Embed `characters/characters.md` descriptions uniformly, with or without a PNG sheet. Before regenerating, rename existing `prompts/…md` and `…png` files with `-backup-YYYYMMDD-HHMMSS`.

Detailed analysis/storyboard/review/regeneration workflow: `references/workflow.md`.

## Page Modification

| Action | Steps |
|--------|-------|
| **Edit** | **Update prompt file FIRST** → regenerate image → download new PNG |
| **Add** | Create prompt at position → generate with character descriptions embedded → renumber subsequent → update storyboard |
| **Delete** | Remove files → renumber subsequent → update storyboard |

## References

- `references/analysis-framework.md` — content analysis
- `references/character-template.md` — character format
- `references/storyboard-template.md` — storyboard format
- `references/ohmsha-guide.md` — Ohmsha specifics
- `references/art-styles/`, `references/tones/`, `references/presets/`, `references/layouts/`
- `references/workflow.md`, `references/auto-selection.md`, `references/partial-workflows.md`

## Pitfalls

- generation takes 10-30s/page; retry once on failure
- download every returned URL to local PNG; downstream review expects files, not ephemeral URLs
- use absolute `curl -o` paths; CWD drift caused pages 06-09 to land at repo root in a prior incident
- use stylized alternatives for sensitive public figures
- Step 2 confirmation is required; Steps 4/6 only when requested
- character sheet is optional/review-only; page prompts use text, not PNG
- strip API keys, tokens, credentials before writing output

## Verification

- selected language is used in all user-facing/generated text
- `analysis.md`, `storyboard.md`, characters, and prompt records exist as applicable
- every generated page has an existing prompt and non-empty PNG at exact absolute path
- aspect ratio mapping is valid; references are recorded with usage/traits
- rendered character/page consistency is checked from text descriptions
- backup suffix used before regeneration; completion report includes generated pages and paths

## Preserved Source Tables

### Original table 1

| Storyboard ratio | `image_generate` format |
|------------------|-------------------------|
| `3:4`, `9:16`, `2:3` | `portrait` |
| `4:3`, `16:9`, `3:2` | `landscape` |
| `1:1` | `square` |

## Preserved Source Examples

### Original example 1

```
Input → Analyze → [Check Existing?] → [Confirm: Style + Reviews] → Storyboard → [Review?] → Prompts → [Review?] → Images → Complete
```
