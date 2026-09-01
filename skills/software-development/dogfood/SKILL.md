---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood: Systematic Web Application QA

role: exploratory web-application QA operator
do: plan coverage; navigate/interact; inspect DOM/console/visuals; capture evidence; deduplicate/classify; write bug report
inputs: target URL, testing scope or `full site`, optional output directory
outputs: `{output_dir}/screenshots/`, `{output_dir}/report.md`, structured issues with reproduction/evidence
¬: test without scope; trust one visual/console check; omit expected-vs-actual; duplicate issues; report unsupported severity; expose credentials

Use browser tools for systematic exploratory testing: navigate, inspect the
accessibility tree, exercise controls/forms/keyboard/scroll paths, check console,
and preserve screenshots. Default output: `./dogfood-output`.

## When to Use

- exploratory QA of a web application
- browser-based regression/feature testing
- find functional, visual, accessibility, console, UX, or content issues
- produce an evidence-backed bug report

## Prerequisites

- browser toolset: `browser_navigate`, `browser_snapshot`, `browser_click`,
  `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`,
  `browser_back`, `browser_press`
- target URL and user testing scope
- optional output directory for screenshots/report

## Procedure

### Phase 1: Plan

1. Create:

   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```

2. Resolve scope; `full site` means comprehensive.
3. Build rough sitemap: landing/home; header/footer/sidebar links; sign-up,
   login, search, checkout and other key flows; forms/interactions; empty/error/
   404 states.

### Phase 2: Explore

For each planned page/feature:

1. Navigate:

   ```
   browser_navigate(url="https://example.com/page")
   ```

2. Snapshot DOM:

   ```
   browser_snapshot()
   ```

3. Check console after every navigation and significant interaction:

   ```
   browser_console(clear=true)
   ```

   Silent JS errors are high-value findings.

4. Annotated visual inspection:

   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```

   `[N]` labels map to `@eN` refs.
5. Exercise controls: click `browser_click(ref="@eN")`; fill with
   `browser_type(ref="@eN", text="test input")`; keyboard with
   `browser_press(key="Tab")`/`Enter`; scroll; invalid and empty submissions.
6. After each interaction, check console, visual changes, and expected-vs-actual.

### Phase 3: Collect Evidence

For each issue:

1. Capture screenshot:

   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```

   Save returned `screenshot_path`.
2. Record URL, reproduction steps, expected behavior, actual behavior, console
   errors, screenshot path.
3. Classify from `references/issue-taxonomy.md`: severity Critical/High/Medium/
   Low; category Functional/Visual/Accessibility/Console/UX/Content.

### Phase 4: Categorize

1. Review all issues; merge the same bug across locations.
2. Assign final severity/category.
3. Sort Critical → High → Medium → Low.
4. Count by severity/category for summary.

### Phase 5: Report

Use `templates/dogfood-report-template.md`; save `{output_dir}/report.md`.
Include:

1. Executive summary: total, severity breakdown, scope.
2. Each issue: number/title, severity/category badges, URL, description, steps,
   expected/actual, screenshot `MEDIA:<screenshot_path>`, relevant console errors.
3. Summary table.
4. Testing notes: tested/not tested/blockers.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get DOM text snapshot (accessibility tree) |
| `browser_click` | Click an element by ref (`@eN`) or text |
| `browser_type` | Type into an input field |
| `browser_scroll` | Scroll up/down on the page |
| `browser_back` | Go back in browser history |
| `browser_press` | Press a keyboard key |
| `browser_vision` | Screenshot + AI analysis; use `annotate=true` for element labels |
| `browser_console` | Get JS console output and errors |

## Pitfalls

- console check is required after navigation/significant interaction
- use `annotate=true` when refs/positions are unclear
- test valid + invalid + empty + long/special-character inputs
- scroll below fold and test multi-step navigation end-to-end
- check responsive behavior in screenshots
- merge manifestations of one bug; do not double-count
- screenshot reports use `MEDIA:<screenshot_path>` for inline display

## Verification

- sitemap/scope covered and tested paths recorded
- console checked after each required point
- each issue has reproducible steps, expected/actual, URL, severity/category, evidence
- duplicate manifestations merged; severity/category counts reconcile
- report saved at `{output_dir}/report.md` with summary, issue details, table, notes
