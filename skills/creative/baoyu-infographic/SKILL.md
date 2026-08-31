---
name: baoyu-infographic
description: "Infographics: 21 layouts x 21 styles (信息图, 可视化)."
version: 1.56.1
author: 宝玉 (JimLiu)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [infographic, visual-summary, creative, image-generation]
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-infographic
---

# Infographic Generator

role: faithful information designer
do: transform supplied text/file/URL/topic into an image-generation-ready infographic while preserving source data
inputs: source, audience/objectives, layout, style, aspect, language
outputs: `infographic/{topic-slug}/` with source, analysis, structured content, prompt, image
¬: invented statistics/claims; credential leakage; style mixing; custom ratio passed directly to unsupported image tool

Adapted from [baoyu-infographic](https://github.com/JimLiu/baoyu-skills) for Hermes. Layout = information structure; style = visual aesthetics; combine freely.

## When to Use

Trigger for infographic, visual summary, information graphic, `信息图`, `可视化`, `高密度信息大图`. Input may be text, file path, URL, or topic; user may choose layout/style/aspect/language.

## Options

| Option | Values |
|--------|--------|
| Layout | 21 options; default `bento-grid` |
| Style | 21 options; default `craft-handmade` |
| Aspect | `landscape` 16:9, `portrait` 9:16, `square` 1:1, or custom W:H such as 3:4, 4:3, 2.35:1 |
| Language | `en`, `zh`, `ja`, etc. |

## Layout Gallery

| Layout | Best For |
|--------|----------|
| `linear-progression` | Timelines, processes, tutorials |
| `binary-comparison` | A vs B, before-after, pros-cons |
| `comparison-matrix` | Multi-factor comparisons |
| `hierarchical-layers` | Pyramids, priority levels |
| `tree-branching` | Categories, taxonomies |
| `hub-spoke` | Central concept with related items |
| `structural-breakdown` | Exploded views, cross-sections |
| `bento-grid` | Multiple topics, overview (default) |
| `iceberg` | Surface vs hidden aspects |
| `bridge` | Problem-solution |
| `funnel` | Conversion, filtering |
| `isometric-map` | Spatial relationships |
| `dashboard` | Metrics, KPIs |
| `periodic-table` | Categorized collections |
| `comic-strip` | Narratives, sequences |
| `story-mountain` | Plot structure, tension arcs |
| `jigsaw` | Interconnected parts |
| `venn-diagram` | Overlapping concepts |
| `winding-roadmap` | Journey, milestones |
| `circular-flow` | Cycles, recurring processes |
| `dense-modules` | High-density modules, data-rich guides |

Full definition: `references/layouts/<layout>.md`.

## Style Gallery

| Style | Description |
|-------|-------------|
| `craft-handmade` | Hand-drawn, paper craft (default) |
| `claymation` | 3D clay figures, stop-motion |
| `kawaii` | Japanese cute, pastels |
| `storybook-watercolor` | Soft painted, whimsical |
| `chalkboard` | Chalk on black board |
| `cyberpunk-neon` | Neon glow, futuristic |
| `bold-graphic` | Comic style, halftone |
| `aged-academia` | Vintage science, sepia |
| `corporate-memphis` | Flat vector, vibrant |
| `technical-schematic` | Blueprint, engineering |
| `origami` | Folded paper, geometric |
| `pixel-art` | Retro 8-bit |
| `ui-wireframe` | Grayscale interface mockup |
| `subway-map` | Transit diagram |
| `ikea-manual` | Minimal line art |
| `knolling` | Organized flat-lay |
| `lego-brick` | Toy brick construction |
| `pop-laboratory` | Blueprint grid, coordinate markers, lab precision |
| `morandi-journal` | Hand-drawn doodle, warm Morandi tones |
| `retro-pop-grid` | 1970s retro pop art, Swiss grid, thick outlines |
| `hand-drawn-edu` | Macaron pastels, hand-drawn wobble, stick figures |

Full definition: `references/styles/<style>.md`.

## Recommended Combinations

| Content Type | Layout + Style |
|--------------|----------------|
| Timeline/History | `linear-progression` + `craft-handmade` |
| Step-by-step | `linear-progression` + `ikea-manual` |
| A vs B | `binary-comparison` + `corporate-memphis` |
| Hierarchy | `hierarchical-layers` + `craft-handmade` |
| Overlap | `venn-diagram` + `craft-handmade` |
| Conversion | `funnel` + `corporate-memphis` |
| Cycles | `circular-flow` + `craft-handmade` |
| Technical | `structural-breakdown` + `technical-schematic` |
| Metrics | `dashboard` + `corporate-memphis` |
| Educational | `bento-grid` + `chalkboard` |
| Journey | `winding-roadmap` + `storybook-watercolor` |
| Categories | `periodic-table` + `bold-graphic` |
| Product Guide | `dense-modules` + `morandi-journal` |
| Technical Guide | `dense-modules` + `pop-laboratory` |
| Trendy Guide | `dense-modules` + `retro-pop-grid` |
| Educational Diagram | `hub-spoke` + `hand-drawn-edu` |
| Process Tutorial | `linear-progression` + `hand-drawn-edu` |

Default: `bento-grid` + `craft-handmade`.

## Keyword Shortcuts

Check first; matched keyword overrides content inference. Offer listed styles first and append Prompt Notes to Step 5.

| User Keyword | Layout | Recommended Styles | Default Aspect | Prompt Notes |
|--------------|--------|--------------------|----------------|--------------|
| 高密度信息大图 / high-density-info | `dense-modules` | `morandi-journal`, `pop-laboratory`, `retro-pop-grid` | portrait | — |
| 信息图 / infographic | `bento-grid` | `craft-handmade` | landscape | Minimalist: clean canvas, ample whitespace, no complex background textures. Simple cartoon elements and icons only. |

## Output Structure

```text
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```

Slug = 2–4 kebab-case words; collision → `-YYYYMMDD-HHMMSS`.

## Core Principles

- copy statistics/quotes verbatim; no summary/rephrase; strip credentials, API keys, tokens, secrets from every output
- define learning objectives before structure
- use headlines, labels, and visual elements for visual communication

## Procedure

### 1. Analyze

Load `references/analysis-framework.md`.

1. Save supplied source as `source.md` with `write_file`; existing source → `source-backup-YYYYMMDD-HHMMSS.md`.
2. Analyze topic, data type, complexity, tone, audience.
3. Detect source language + user language.
4. Extract user design instructions.
5. Save `analysis.md`; existing file → `analysis-backup-YYYYMMDD-HHMMSS.md`.

### 2. Structure

Write `structured-content.md` (Markdown only): title/objectives; sections with key concept, verbatim content, visual element, labels; exact statistics/quotes; user design instructions. Add no information; strip secrets. Use `references/structured-content-template.md`.

### 3. Recommend

3.1 Keyword shortcut first. 3.2 Otherwise recommend 3–5 layout×style pairs using data structure, tone, audience, and user instructions.

### 4. Confirm

Use `clarify`, one question at a time, most important first:

- Q1 combination: present ≥3 pairs + rationale; user picks
- Q2 aspect: landscape/portrait/square/custom W:H
- Q3 language only when source language differs from user language

### 5. Prompt

Back up existing `prompts/infographic.md` as `prompts/infographic-backup-YYYYMMDD-HHMMSS.md`. Load selected `references/layouts/<layout>.md`, `references/styles/<style>.md`, `references/base-prompt.md`; combine layout, style, base, structured content, confirmed language. Resolve `{{ASPECT_RATIO}}`: landscape→`16:9`, portrait→`9:16`, square→`1:1`, custom unchanged (`3:4`, `4:3`, `2.35:1`). Save with `write_file`.

### 6. Generate image

Use `image_generate` with assembled prompt. Map 16:9→`landscape`, 9:16→`portrait`, 1:1→`square`; custom ratio → closest named aspect. Retry once on failure; save URL/path in output directory.

### 7. Report

Return topic, layout, style, aspect, language, output path, files created.

## References

- `references/analysis-framework.md`
- `references/structured-content-template.md`
- `references/base-prompt.md`
- `references/layouts/<layout>.md` (21)
- `references/styles/<style>.md` (21)

## Pitfalls

- data integrity: `73% increase` stays `73% increase`, never `significant increase`
- always scan/strip secrets
- one clear concept per section; overload harms readability
- apply one selected style consistently; do not mix
- `image_generate` supports only named `landscape`, `portrait`, `square`; map custom ratios to nearest

## Verification

- source, analysis, structured content, prompt, and image paths exist
- every statistic/quote matches source; no secret remains
- selected shortcut/layout/style/aspect/language are recorded
- prompt includes all required references and confirmed language
- image generation result or one retry failure is reported honestly
