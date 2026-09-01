---
name: pptx-author
description: Build PowerPoint decks headless with python-pptx.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [powerpoint, pptx, python-pptx, presentation, finance]
    related_skills: [excel-author, powerpoint]
---

role: headless financial pitch-deck author
do: create `.pptx` with python-pptx; load firm template; bind every number to source workbook; embed model-rendered charts; keep one takeaway per slide; deliver file only
inputs: source `.xlsx`/named ranges; template; deck narrative; charts/figures; slide types
outputs: `./out/<name>.pptx`; traceable footnotes; presentation-ready slides
¬: drive live PowerPoint; transcribe numbers from memory/summary; use fragile native charts when fidelity requires PNG; email/upload/post; omit model cell/sheet sources; add unrelated animation-heavy slideware

Produce a `.pptx` file on disk with `python-pptx`, not a live PowerPoint session.
Adapted from Anthropic `pptx-author`/`pitch-deck`; MCP/Office-JS branches removed.
For broader slide, speaker-note, embed, and media support use built-in
`powerpoint`.

## When to Use

- model-backed pitch decks, IC memos, earnings notes, financial presentations
- deck numbers that must trace to a source workbook

Use live Office MCP for a live PowerPoint session; use `powerpoint` for
non-financial slideware, heavy animation/transitions, or speaker notes.

## Output Contract and Setup

- write `./out/<name>.pptx`; create `./out/`
- return relative path in final response
- no external sends; orchestration layers handle delivery

```bash
pip install "python-pptx>=0.6"
```

## Procedure

### 1. Establish a template and slide idea

If `./templates` contains `firm-template.pptx`, load it so branded colors, fonts,
and master layouts survive:

```python
from pptx import Presentation
from pathlib import Path

template = Path("./templates") / "firm-template.pptx"
prs = Presentation(str(template)) if template.exists() else Presentation()
```

One idea per slide: title states takeaway; body supports it. Weak:
`Q3 Revenue`; strong: `Revenue growth accelerated to 14% Y/Y in Q3`.

### 2. Bind numbers to model

Every slide figure from `./out/model.xlsx` gets sheet/cell footnote:

```text
Revenue: $1,250M  (Source: model.xlsx, Inputs!C3)
```

Never transcribe from memory or a summary. Open workbook, read named range, and
bind programmatically whenever possible. Recalculate workbook before reading;
`openpyxl` only sees computed values after a prior calculation. Run the
`excel-author` recalc helper or open/save through real Excel.

```python
from openpyxl import load_workbook

wb = load_workbook("./out/model.xlsx", data_only=True)
def nr(name):
    """Resolve a named range to its current computed value."""
    rng = wb.defined_names[name]
    sheet, coord = next(rng.destinations)
    return wb[sheet][coord].value

revenue_fy24 = nr("RevenueFY24")
implied_mid  = nr("ImpliedSharePriceBase")
```

```python
slide.shapes.title.text = f"Implied share price of ${implied_mid:.2f} (base case)"
```

### 3. Prefer PNG charts from model

When fidelity matters, render chart to PNG from source workbook and embed it;
native `pptx.chart` charts are fragile and often do not match firm conventions:

```python
from pptx.util import Inches
slide.shapes.add_picture("./out/charts/football_field.png",
                         Inches(1), Inches(2),
                         width=Inches(8))
```

### 4. Create slides and save

```python
from pptx import Presentation
from pptx.util import Inches
from pathlib import Path

template = Path("./templates") / "firm-template.pptx"
prs = Presentation(str(template)) if template.exists() else Presentation()

# Title slide
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "Project Aurora — Strategic Alternatives"
slide.placeholders[1].text = "Preliminary Discussion Materials"

# Valuation summary slide (title-only layout)
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Valuation implies $38–$52 per share across methodologies"

# Add a table bound to model outputs
rows, cols = 5, 4
tbl_shape = slide.shapes.add_table(rows, cols,
                                   Inches(0.5), Inches(1.5),
                                   Inches(9), Inches(3))
tbl = tbl_shape.table
headers = ["Methodology", "Low ($)", "Mid ($)", "High ($)"]
for c, h in enumerate(headers):
    tbl.cell(0, c).text = h

# In a real deck, read these from the model workbook with openpyxl
data = [
    ("Trading comps",     "35", "41", "48"),
    ("Precedent M&A",     "39", "45", "52"),
    ("DCF (base)",        "36", "43", "51"),
    ("LBO (10% IRR)",     "33", "38", "44"),
]
for r, row in enumerate(data, start=1):
    for c, val in enumerate(row):
        tbl.cell(r, c).text = val

# Embed a chart rendered from the model
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Football field — current price $42"
slide.shapes.add_picture("./out/charts/football_field.png",
                         Inches(1), Inches(1.8), width=Inches(8))

Path("./out").mkdir(exist_ok=True)
prs.save("./out/pitch-aurora.pptx")
```

## Suggested Pitch-Deck Sequence

Not prescriptive; use as starting skeleton:

1. cover/title
2. disclaimer
3. contents
4. situation overview
5. target company snapshot
6. market/sector context
7. valuation summary/football field (money slide)
8. trading comps detail
9. precedent transactions detail
10. DCF summary
11. illustrative LBO/sponsor case
12. process considerations
13. appendix

## Verification

- [ ] firm template loaded when present
- [ ] output is `./out/<name>.pptx` and path returned
- [ ] each slide has one clear takeaway
- [ ] every number traces to workbook sheet/cell or named range
- [ ] workbook recalculated before `data_only=True` reads
- [ ] charts are PNG-from-model where fidelity matters
- [ ] no external send performed
- [ ] deck type fits this light financial authoring skill

## Attribution

Conventions adapted from Anthropic's Claude for Financial Services plugin suite,
Apache-2.0. Original:
https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/pitch-agent/skills/pptx-author