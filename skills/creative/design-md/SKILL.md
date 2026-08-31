---
name: design-md
description: Author/validate/export Google's DESIGN.md token spec files.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, ui, accessibility, wcag, tailwind, dtcg, google]
    related_skills: [popular-web-designs, claude-design, excalidraw, architecture-diagram]
---

# DESIGN.md

role: design-token spec author/validator
do: author, lint, diff, and export Google's `DESIGN.md` format
authority: https://github.com/google-labs-code/design.md (Apache-2.0)
outputs: normative YAML tokens + Markdown rationale; optional Tailwind/DTCG exports
¬: use for visual inspiration/one-off artifact (use `popular-web-designs`/`claude-design`); return broken refs or WCAG failures

`DESIGN.md` combines YAML front matter (machine-readable normative tokens) and Markdown rationale (why/how). `npx @google/design.md` lints structure/WCAG, detects regressions, and exports Tailwind or W3C DTCG JSON.

## When to Use

- create a DESIGN.md, token set, or formal design-system spec
- keep UI/brand consistent across projects/tools
- lint, diff, extend, or export an existing DESIGN.md
- port a style guide to an agent-readable format
- validate palette contrast/WCAG accessibility

## File Anatomy

```md
---
version: alpha
name: Heritage
description: Architectural minimalism meets journalistic gravitas.
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body-md:
    fontFamily: Public Sans
    fontSize: 1rem
rounded:
  sm: 4px
  md: 8px
  lg: 16px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
---

## Overview

Architectural Minimalism meets Journalistic Gravitas...

## Colors

- **Primary (#1A1C1E):** Deep ink for headlines and core text.
- **Tertiary (#B8422E):** "Boston Clay" — the sole driver for interaction.

## Typography

Public Sans for everything except small all-caps labels...

## Components

`button-primary` is the only high-emphasis action on a page...
```

## Token Contract

| Type | Format | Example |
|------|--------|---------|
| Color | any CSS color (hex, `rgb()`, `oklch()`, named) | `"#1A1C1E"`, `"oklch(62% 0.18 250)"` |
| Dimension | number + unit (`px`, `em`, `rem`) | `48px`, `-0.02em` |
| Token reference | `{path.to.token}` | `{colors.primary}` |
| Typography | object with `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, `fontVariation` | see above |

Component whitelist: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`. Hover/active/pressed variants are sibling entries (`button-primary-hover`), never nested.

## Canonical Section Order

Sections optional; present sections must follow order. Linter warns `section-order`; duplicate headings are rejected by spec consumers.

1. Overview (alias: Brand & Style)
2. Colors
3. Typography
4. Layout (alias: Layout & Spacing)
5. Elevation & Depth (alias: Elevation)
6. Shapes
7. Components
8. Do's and Don'ts

Unknown sections are preserved; unknown token names are accepted when type-valid; unknown component properties warn.

## Procedure: New Spec

1. Ask/infer brand tone, accent, typography; translate supplied site/image/vibe to token shape.
2. `write_file` project-root `DESIGN.md`; always include `name:` + `colors:`.
3. Use references (`{colors.primary}`) in `components:`; keep palette single-source.
4. Lint; repair broken references and WCAG failures.
5. Existing project: also export `tailwind.theme.json` or `tokens.json`.

## CLI: Lint / Diff / Export

CLI package: `@google/design.md`; use `npx`, no global install.

```bash
# Validate structure + token references + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions, fail on regression (exit 1 = regression)
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind v3 theme JSON (`tailwind` is a back-compat alias)
npx -y @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json

# Export to a Tailwind v4 CSS @theme block (--color-*, --text-*, --radius-*, ...)
npx -y @google/design.md export --format css-tailwind DESIGN.md > theme.css

# Export to W3C DTCG (Design Tokens Format Module) JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json

# Print the spec itself — useful when injecting into an agent prompt
npx -y @google/design.md spec --rules-only --format json
```

All commands accept `-` stdin. `lint` exit 1 on errors; warnings alone exit 0. `export` can exit 0 despite lint findings; run `lint` separately. Output JSON by default; parse structurally. Windows `design.md` bin may collide with `.md` association; use:

```bash
npx -y -p @google/design.md designmd lint DESIGN.md
```

### Lint rules (CLI 0.3.0)

- `broken-ref` error: `{colors.missing}` absent
- `contrast-ratio` warning: component text/background below WCAG AA 4.5:1
- `missing-primary` warning: colors but no `primary`
- `missing-typography` warning: colors but no typography
- `orphaned-tokens` warning: color tokens unused by components
- `section-order` warning: noncanonical order
- `unknown-key` warning: typo-like top-level key (`colours:` → `colors:`); custom extension keys silent
- `token-summary`, `missing-sections` info: counts/absent optional sections

When accessibility matters, call WCAG findings out in the summary.

## Pitfalls

- variants: `button-primary.hover` wrong; sibling `button-primary-hover` right
- quote hex strings or YAML may choke/truncate `#1A1C1E`
- quote negative dimensions: `letterSpacing: "-0.02em"`, not unquoted flow
- reorder sections despite warning-only linter; consumers expect canonical order
- CLI 0.3.0 silently drops typo `fontwight:`; check `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, `fontVariation`
- `version: alpha` is current spec version as of Jul 2026/CLI 0.3.0; alpha can break
- dotted `{colors.primary}` resolves; `{primary}` does not

## Verification

- YAML front matter parses; `name`, `colors`, token types, references present
- `lint` clean of errors; WCAG warnings reported or fixed
- `diff` regression status understood; exports succeed and are written
- source of truth remains https://github.com/google-labs-code/design.md; CLI = `@google/design.md`; generated file license follows user's project, spec is Apache-2.0
