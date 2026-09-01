---
name: excel-author
description: Build auditable financial workbooks headless via openpyxl.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [excel, openpyxl, finance, spreadsheet, modeling]
    related_skills: [xlsx, pptx-author, dcf-model, comps-analysis, lbo-model, 3-statement-model]
---

# excel-author

role: headless `openpyxl` financial-workbook author and auditor
do: create one model per `.xlsx`; use formula/color/comment/named-range conventions; add Checks tab; build sensitivities; recalculate with LibreOffice; deliver artifact path
inputs: model assumptions/raw actuals; template; workbook structure; formulas; source/date/comments; user output name
outputs: `./out/<name>.xlsx`; computed values; Checks TRUE/FALSE; auditable source trail; validation result
¬: live Office session; append unless asked; hardcode derived values; omit named ranges/checks/comments; use even-dimension sensitivity; deliver without recalculation; email/upload/post artifact

Produces a banker-grade `.xlsx` on disk with formulas that flex, traceable
inputs, and checks reviewable by someone other than the author. Adapted from
Anthropic `xlsx-author`/`audit-xls`; MCP/Office-JS/Cowork branches removed for
headless Python.

## When to Use

- financial models, DCFs, comps, LBOs, three-statement workbooks
- auditable spreadsheet artifacts generated in a non-interactive environment

Use live Office MCP instead for a live Excel session. Use CSV/pandas for pure
tabular exports and a BI tool for heavily interactive dashboards/charts.

## Output Contract

- write to `./out/<name>.xlsx`; create `./out/`
- return relative path in final response for downstream pickup
- one logical model per file; do not append to existing workbook unless explicitly asked

## Prerequisites

```bash
pip install "openpyxl>=3.0"
```

## Procedure

### 1. Apply cell conventions

- blue `Font(color="0000FF")`: hardcoded input a human enters (drivers, WACC, terminal g, market data)
- black/default: formula/derived calculation
- green `Font(color="006100")`: link to another sheet/external file

Formula rule: every calculation cell is a formula string, never Python-computed
number. Only hardcoded: raw historical inputs, flexed assumption drivers, and
current market data with source/date comment.

```python
# WRONG — silent bug waiting to happen
ws["D20"] = revenue_prior_year * (1 + growth)

# CORRECT — flexes when the user changes the assumption
ws["D20"] = "=D19*(1+$B$8)"
```

### 2. Use named ranges

Name figures referenced from another sheet, deck, or memo:

```python
from openpyxl.workbook.defined_name import DefinedName
wb.defined_names["WACC"] = DefinedName("WACC", attr_text="Inputs!$C$8")
# then elsewhere:
calc["D30"] = "=D29/WACC"
```

### 3. Add Checks tab

Include TRUE/FALSE checks for BS Assets = Liabilities + Equity, cash-flow tie to
BS period change, sum-of-parts to consolidated totals, and no rogue hardcodes in
calc ranges:

```python
checks = wb.create_sheet("Checks")
checks["A2"] = "BS balances"
checks["B2"] = "=IS!D20-IS!D21-IS!D22"
checks["C2"] = "=ABS(B2)<0.01"  # TRUE/FALSE
```

### 4. Comment every hardcoded input immediately

```python
from openpyxl.comments import Comment
ws["C2"] = 1_250_000_000
ws["C2"].font = Font(color="0000FF")
ws["C2"].comment = Comment("Source: 10-K FY2024, p.47, revenue line", "analyst")
```

Format: `Source: [System/Document], [Date], [Reference], [URL if applicable]`.
Never defer and never use `TODO: add source`.

### 5. Build standard skeleton

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from pathlib import Path

BLUE = Font(color="0000FF")
BLACK = Font(color="000000")
GREEN = Font(color="006100")
BOLD = Font(bold=True)
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)

wb = Workbook()

# --- Inputs tab ---
inp = wb.active
inp.title = "Inputs"
inp["A1"] = "MARKET DATA & KEY INPUTS"
inp["A1"].font = HEADER_FONT
inp["A1"].fill = HEADER_FILL
inp.merge_cells("A1:C1")

inp["B3"] = "Revenue FY2024"
inp["C3"] = 1_250_000_000
inp["C3"].font = BLUE
inp["C3"].comment = Comment("Source: 10-K FY2024 p.47", "model")

inp["B4"] = "Growth Rate"
inp["C4"] = 0.12
inp["C4"].font = BLUE

# --- Calc tab ---
calc = wb.create_sheet("DCF")
calc["B2"] = "Projected Revenue"
calc["C2"] = "=Inputs!C3*(1+Inputs!C4)"   # formula, black

# --- Checks tab ---
chk = wb.create_sheet("Checks")
chk["A2"] = "BS balances"
chk["B2"] = "=BS!D20-BS!D21-BS!D22"
chk["C2"] = "=ABS(B2)<0.01"  # TRUE/FALSE

Path("./out").mkdir(exist_ok=True)
wb.save("./out/model.xlsx")
```

### 6. Style merged section headers

Set top-left value/style and style the full merged range:

```python
ws["A7"] = "CASH FLOW PROJECTION"
ws["A7"].font = HEADER_FONT
ws.merge_cells("A7:H7")
for col in range(1, 9):  # A..H
    ws.cell(row=7, column=col).fill = HEADER_FILL
```

### 7. Build sensitivity tables with formulas

Use odd 5×5/7×7 grids, symmetric axes, base at center, medium-blue `BDD7EE`
bold center, every cell full-recalculation formula, never approximation.

```python
# 5x5 WACC (rows) x terminal growth (cols) sensitivity
wacc_axis = [0.08, 0.085, 0.09, 0.095, 0.10]        # center row = base 9.0%
term_axis = [0.02, 0.025, 0.03, 0.035, 0.04]        # center col = base 3.0%

start_row = 40
ws.cell(row=start_row, column=1).value = "Implied Share Price ($)"
ws.cell(row=start_row, column=1).font = BOLD

for j, g in enumerate(term_axis):
    ws.cell(row=start_row+1, column=2+j).value = g
    ws.cell(row=start_row+1, column=2+j).font = BLUE

for i, w in enumerate(wacc_axis):
    r = start_row + 2 + i
    ws.cell(row=r, column=1).value = w
    ws.cell(row=r, column=1).font = BLUE
    for j, g in enumerate(term_axis):
        c = 2 + j
        # Full DCF recalc formula (simplified for illustration).
        # In a real model this references the full projection block.
        ws.cell(row=r, column=c).value = (
            f"=SUMPRODUCT(FCF_range,1/(1+{w})^year_offset) + "
            f"FCF_terminal*(1+{g})/({w}-{g})/(1+{w})^terminal_year"
        )

# Highlight center cell (base case)
center = ws.cell(row=start_row+2+len(wacc_axis)//2,
                 column=2+len(term_axis)//2)
center.fill = PatternFill("solid", fgColor="BDD7EE")
center.font = BOLD
```

Axes must equal `[base-2Δ, base-Δ, base, base+Δ, base+2Δ]`; center output
must equal base implied share price. Do not use Excel Data Table feature.

### 8. Recalculate

`openpyxl` writes formulas but does not calculate them. Downstream checks need
cached values; use LibreOffice or this skill's `scripts/recalc.py`:

```bash
# LibreOffice headless recalc
libreoffice --headless --calc --convert-to xlsx ./out/model.xlsx --outdir ./out/
```

## User Checkpoints

For large models, stop/show/confirm after Inputs, Revenue, FCF, WACC, and
valuation/equity bridge; only then build sensitivities. Catch wrong assumptions
before downstream work.

## Verification Checklist

- [ ] output is `./out/<name>.xlsx`, one logical model
- [ ] formulas, not Python hardcodes, for every calculation
- [ ] blue inputs, black formulas, green cross-sheet links
- [ ] named ranges for cross-sheet/deck/memo references
- [ ] comments on every hardcoded input at creation
- [ ] Checks tab covers BS, cash, sum-of-parts, rogue hardcodes
- [ ] sensitivity axes odd/symmetric, center is base, every cell formula, center highlighted
- [ ] formulas recalculated; no formula errors; artifact path returned

## Attribution

Conventions adapted from Anthropic's Claude for Financial Services plugin suite,
Apache-2.0. Original:
https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis/skills/xlsx-author