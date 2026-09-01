---
name: powerpoint
description: Create, read, edit .pptx decks with python-pptx.
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pptx, powerpoint, presentations, slides, office, python-pptx]
    category: productivity
    related_skills: [docx, xlsx, pdf]
---

# PowerPoint

role: offline `.pptx` deck creator/reader/editor
do: create from JSON; inspect outline/notes/tables/charts/images; edit text/data/slide assets; fill brand template; render; PDF-export; visually verify
inputs: spec/deck/template, text/chart/image/slide operations, values, render tools
outputs: `.pptx`, JSON outline/assets, PNG/PDF render, verification report
¬: legacy `.ppt` directly; require PowerPoint installation; duplicate chart slide; copy slides between decks; assume JSON outline proves visuals; ship without render/outline verification; claim PDF conversion without `soffice`

`python-pptx` + five helper scripts operate offline: create JSON spec,
structured read-back, in-place edit, template brand deck, slide rendering.

## When to Use

- build report/pitch/presentation deck
- extract text/notes/tables/chart data/images from `.pptx`
- replace text/data/logo; duplicate/remove/reorder slides; backgrounds,
  footers, hyperlinks, notes
- use company template
- `.ppt` → convert first:
  `soffice --convert-to pptx old.ppt` when LibreOffice exists

## Prerequisites

- Python 3.10+ + `python-pptx` (`pip install python-pptx`)
- optional LibreOffice `soffice` + poppler `pdftoppm`/`pdftocairo` for render/PDF
- render helper detects tools; absent →
  `{"rendered": false, "missing": [...]}` exit 0; create/read/edit still work
- check via `terminal`: `python -c "import pptx; print(pptx.__version__)"` and
  `which soffice pdftoppm`

## Commands

Scripts in `scripts/`; each supports `--help`, JSON stdout, non-zero failure:

```bash
python scripts/pptx_create.py deck.json out.pptx
python scripts/pptx_read.py deck.pptx --outline      # full JSON outline
python scripts/pptx_read.py deck.pptx --notes        # speaker notes
python scripts/pptx_read.py deck.pptx --images ./img # export pictures
python scripts/pptx_edit.py deck.pptx --replace-text "Old Corp" "New Corp"
python scripts/pptx_edit.py deck.pptx --chart-data update.json
python scripts/pptx_edit.py deck.pptx --duplicate-slide 2
python scripts/pptx_edit.py deck.pptx --remove-slide 3 --move-slide 2 0
python scripts/pptx_from_template.py brand.pptx out.pptx --values vals.json
python scripts/pptx_render.py deck.pptx --outdir ./render  # slide PNGs
```

Specs via `write_file`; inspect generated JSON via `read_file`.

## Quick Reference

| Task | Command |
|---|---|
| New deck from spec | `pptx_create.py spec.json out.pptx` |
| 16:9 vs 4:3 | `"slide_size": "16:9"` or `"4:3"` in the spec |
| Outline as JSON | `pptx_read.py deck.pptx --outline` |
| Export images | `pptx_read.py deck.pptx --images DIR` |
| Replace text | `pptx_edit.py deck.pptx --replace-text OLD NEW` |
| Replace chart data | `pptx_edit.py deck.pptx --chart-data spec.json` |
| Patch one series | same flag, spec with `"ops"` (see below) |
| Swap picture | `pptx_edit.py deck.pptx --swap-image N NAME new.png` |
| Duplicate slide | `pptx_edit.py deck.pptx --duplicate-slide N` |
| Remove slide | `pptx_edit.py deck.pptx --remove-slide N` |
| Reorder slide | `pptx_edit.py deck.pptx --move-slide FROM TO` |
| Slide background | `pptx_edit.py deck.pptx --set-background N RRGGBB` |
| Hyperlink runs | `pptx_edit.py deck.pptx --hyperlink N TEXT URL` |
| Slide number on | `pptx_edit.py deck.pptx --enable-slide-number N` |
| Footer text | `pptx_edit.py deck.pptx --set-footer N TEXT` |
| Set notes | `pptx_edit.py deck.pptx --set-notes N TEXT` |
| Append notes | `pptx_edit.py deck.pptx --append-notes N TEXT` |
| Fill template | `pptx_from_template.py tpl.pptx out.pptx --values v.json` |
| Render slide PNGs | `pptx_render.py deck.pptx --outdir DIR` |

## Procedure

1. **Create**: JSON layouts `title`, `title_content`, `section`,
   `two_content`, `title_only`, `blank`; fields `title`, `subtitle`,
   `bullets` (string or dict `level` 0–4, `size` pt, `bold`, `italic`,
   `font`, hex `color`, hyperlink `link`), solid hex `background`, `footer`,
   `slide_number`, images path + inch positions, tables rows, shapes
   (rectangle/rounded_rectangle/oval/diamond/right_arrow/chevron + fill/text),
   charts (bar/bar_h/line/pie + categories/series), speaker `notes`.
2. **Read**: outline returns slide size/layout inventory and per-slide layout,
   shape texts, table cells, image filename/ext/bytes, chart
   categories/series/values, notes. `--images DIR` then `vision_analyze`.
3. **Edit**: operations combine one pass; `--output` preserves original.
   Text scans shapes/tables/notes. Image swap keeps position/size via
   relationship ID. Remove/reorder XML `<p:sldId>` entries because no public
   python-pptx API. Duplicate appends deep independent copy with shape/media/
   hyperlink relationships and remapped rIds; chart slides refused.
   Notes/background/hyperlink/number/footer options polish deck.
4. **Charts**: `--chart-data` full replace
   `{"slide": 0, "chart": 0, "categories": [...], "series": {...}}`;
   `ops`: `update_series`, `add_series`, `remove_series`,
   `rename_category` (`from`/`to` or `index`), `set_title`. Wrapper reads,
   modifies, `replace_data`; unexpressible data normalizes.
5. **Template**: `pptx_from_template.py` replaces `{{token}}` across
   slides/tables/notes; append slides using template layouts by name/index,
   retaining master fonts/colors. Zero-slide start: remove existing slides
   with `pptx_edit.py --remove-slide`.
6. **Render**: `pptx_render.py` → `soffice --headless` PDF →
   `pdftoppm`/`pdftocairo` PNG; JSON lists paths; inspect every PNG with
   `vision_analyze`. Missing tool → exit 0 rendered false; outline verifies
   content/structure only.

## PDF Export

```bash
soffice --headless --convert-to pdf --outdir ./out deck.pptx
```

Output `./out/deck.pdf`; missing fonts substitute. Render-verify first. No
offline pure-Python `.pptx`→PDF; absent `soffice` → state limitation.

## Pitfalls

- PowerPoint fragments text into runs; replacement merges adjacent identically
  formatted runs. Cross-format matches rewrite using first run formatting; verify.
- chart slide duplication refused: separate XLSX workbook relationship graph;
  rebuild chart. Image/media/external-hyperlink rels carry; layout/notes fresh.
- chart ops replace whole dataset; chart type cannot change
- reorder is XML-level `<p:sldIdLst>`; reread
- cross-deck copy unsupported; duplicate only within shared master
- footer/number requires layout placeholder; absent → clear failure, add textbox
- hyperlinks apply whole matching runs on slide
- default create size 4:3 template but script sets 16:9 unless specified;
  custom template keeps size
- template layout indexes vary; inspect `pptx_read.py template.pptx --outline`
  (`layouts_available`)
- blank layout has `slide.shapes.title is None`; helper handles it
- spec UTF-8: tokens `{{city}}` may contain non-ASCII

## Verification

1. create/edit → `pptx_read.py OUT.pptx --outline`; check count/text/tables/
   notes/chart values
2. `--images DIR`; embedded pictures have expected files/bytes
3. render every slide; inspect PNGs for overlap/truncation/colors; absent
   tools → rely on outline and report no visual proof
4. full contract: `python -m pytest tests/ -q` (python-pptx + pytest required)