---
name: baoyu-article-illustrator
description: "Article illustrations: type × style × palette consistency."
version: 1.57.0
author: 宝玉 (JimLiu)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [article-illustration, creative, image-generation]
    category: creative
    homepage: https://github.com/JimLiu/baoyu-skills#baoyu-article-illustrator
---

# Article Illustrator

role: article-to-illustration production operator
do: read/analyze source; select type/style/palette; confirm settings; write outline/prompts; generate/download images; insert links; report
inputs: article path/content, optional reference images, type, style, palette, density, language, output layout
outputs: `analysis.md`, `outline.md`, reproducible prompt files, PNGs, article image inserts
¬: alter article data; write prompt after generation; copy binary through text tools; expose secrets; claim backend/model selection; insert an unverified image path

Analyze an article, place illustrations where they add information, and generate images with consistent **Type × Style × Palette**. Adapted from [baoyu-article-illustrator](https://github.com/JimLiu/baoyu-skills) for Hermes tools.

## When to Use

- illustrate an article or add images to content
- generate illustrations from a file or pasted article
- user asks `为文章配图`, `illustrate article`, or `add images`

## Dimensions

| Dimension | Controls | Examples |
|-----------|----------|----------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Rendering approach | notion, warm, minimal, blueprint, watercolor, elegant |
| **Palette** | Color scheme (optional) | macaron, warm, neon — overrides style's default colors |

Combine dimensions, e.g. `type=infographic, style=vector-illustration, palette=macaron`; preset `edu-visual` supplies all three. See `references/style-presets.md`.

| Type | Best For |
|------|----------|
| `infographic` | Data, metrics, technical |
| `scene` | Narratives, emotional |
| `flowchart` | Processes, workflows |
| `comparison` | Side-by-side, options |
| `framework` | Models, architecture |
| `timeline` | History, evolution |

Styles, gallery, and Type × Style compatibility: `references/styles.md`.

## Prerequisites

- article path or content; optional reference images
- `vision_analyze`, `image_generate`, `clarify`, `terminal`, `read_file`, `write_file`
- output path/layout decision

## Output Contract

```
{output-dir}/
├── source-{slug}.{ext}    # Only for pasted content
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```

| Input | Output Directory | Markdown Insert Path |
|-------|------------------|----------------------|
| Article file path | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| Pasted content | `illustrations/{topic-slug}/` (cwd) | `illustrations/{topic-slug}/NN-{type}-{slug}.png` |

Honor an explicit layout. Slug=2-4 kebab-case words; conflict→`-YYYYMMDD-HHMMSS`.

## Core Rules

- visualize concepts, not literal metaphors such as `电锯切西瓜`
- labels use article numbers, terms, and quotes; never generic placeholders
- save every prompt under `prompts/` before generation
- scan source for API keys, tokens, credentials before writing output

## Procedure

```
- [ ] Step 1: Detect reference images (if provided)
- [ ] Step 2: Analyze content
- [ ] Step 3: Confirm settings (clarify tool, one question at a time)
- [ ] Step 4: Generate outline
- [ ] Step 5: Generate prompts
- [ ] Step 6: Generate images (image_generate)
- [ ] Step 7: Finalize
```

### 1. Detect reference images

For each path/attachment/URL:

1. Call `vision_analyze`; record style, palette, composition, subject in the output `references` directory as `NN-ref-{slug}.md` with `write_file`.
2. Do not copy binary via `write_file`/`read_file`; optional local copy uses `terminal` into the output `references` directory.
3. Embed the textual vision description in prompts because `image_generate` accepts no image input.

Full procedure: `references/workflow.md#step-1-detect-reference-images`.

### 2. Analyze

| Analysis | Output |
|----------|--------|
| Content type | Technical / Tutorial / Methodology / Narrative |
| Purpose | information / visualization / imagination |
| Core arguments | 2-5 main points |
| Positions | Where illustrations add value |

Read file with `read_file` or use pasted text; write `{output-dir}/analysis.md`. Full procedure: `references/workflow.md#step-2-analyze`.

### 3. Confirm settings

Use `clarify`, one question at a time; skip answered questions; ask no more than 2-3 in a row.

| Order | Question | Options |
|-------|----------|---------|
| Q1 | **Preset or Type** | [Recommended preset], [alt preset], or manual: infographic, scene, flowchart, comparison, framework, timeline, mixed |
| Q2 | **Density** | minimal (1-2), balanced (3-5), per-section (Recommended), rich (6+) |
| Q3 | **Style** *(skip if preset chosen in Q1)* | [Recommended], minimal-flat, sci-fi, hand-drawn, editorial, scene, poster |
| Q4 | **Palette** *(optional)* | Default (style colors), macaron, warm, neon |
| Q5 | **Language** *(only if article language is ambiguous)* | article language / user language |

### 4. Outline

Write `{output-dir}/outline.md` with frontmatter `(type, density, style, palette, image_count)` and one entry per illustration:

```yaml
## Illustration 1
**Position**: [section/paragraph]
**Purpose**: [why]
**Visual Content**: [what to show]
**Filename**: 01-infographic-concept-name.png
```

Template: `references/workflow.md#step-4-generate-outline`.

### 5. Prompts

**Hard gate:** save each full final prompt before any image generation.

1. Follow `references/prompt-construction.md`.
2. Save `prompts/NN-{type}-{slug}.md` with YAML frontmatter.
3. Use type-specific `ZONES / LABELS / COLORS / STYLE / ASPECT` sections.
4. Put actual article numbers, terms, metrics, and quotes in `LABELS`.
5. Apply `direct`/`style`/`palette` reference semantics; for `direct`, embed textual traits because image input is unsupported.

### 6. Generate and download

For each prompt:

1. Call `image_generate(prompt=..., aspect_ratio=...)`; result is an image URL, not a file.
2. Map `16:9`→`landscape`, `9:16`→`portrait`, `1:1`→`square`; custom ratios→nearest enum.
3. Download via `terminal` to `{output-dir}/NN-{type}-{slug}.png`, e.g. `curl -sSL -o "{output-dir}/NN-{type}-{slug}.png" "{url}"`.
4. Retry once on failure.

Backend is user-configured (default FAL FLUX 2 Klein 9B), not agent-selectable through `image_generate`; do not route by writing model names into prompts.

### 7. Finalize

Insert `![description]({relative-path}/NN-{type}-{slug}.png)` after the matching paragraph; alt text is concise and in article language.

```
Article Illustration Complete!
Article: [path] | Type: [type] | Density: [level] | Style: [style] | Palette: [palette or default]
Images: X/N generated
```

## Modification

| Action | Steps |
|--------|-------|
| Edit | Update prompt → Regenerate → Update reference |
| Add | Position → Prompt → Generate → Update outline → Insert |
| Delete | Delete files → Remove reference → Update outline |

## References

| File | Content |
|------|---------|
| [references/workflow.md](references/workflow.md) | Detailed procedures |
| [references/usage.md](references/usage.md) | Invocation examples |
| [references/styles.md](references/styles.md) | Style gallery + Palette gallery |
| [references/style-presets.md](references/style-presets.md) | Preset shortcuts (type + style + palette) |
| [references/prompt-construction.md](references/prompt-construction.md) | Prompt templates |

## Pitfalls

- Preserve source statistics exactly: `73% increase` stays `73% increase`.
- Strip API keys, tokens, credentials before writing any output.
- Do not illustrate metaphors literally.
- No `image_generate` call before its prompt file exists.
- `image_generate` supports only `landscape`, `portrait`, `square`; returns URL, so download before insertion.
- Agent cannot select the generation backend; default is FAL FLUX 2 Klein 9B.

## Verification

- source analysis and outline exist at the chosen output directory
- every image has a saved prompt and article-specific labels
- PNG exists at the exact downloaded path and is non-empty
- aspect mapping and alt text match the article
- inserted links resolve relative to the article
- report states generated count `X/N`
