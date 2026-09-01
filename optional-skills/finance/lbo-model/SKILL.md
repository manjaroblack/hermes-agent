---
name: lbo-model
description: Build leveraged buyout workbooks with IRR/MOIC in Excel.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, valuation, lbo, private-equity, excel, openpyxl, modeling]
    related_skills: [excel-author, pptx-author, dcf-model, 3-statement-model]
---

role: leveraged-buyout workbook builder and auditor
do: inspect/use provided template; map timeline/signs/formulas; build Sources & Uses, Operating Model, Debt Schedule, Returns, sensitivities; verify section-by-section; recalculate/error-audit; deliver workbook and merger-ready outputs
inputs: attached/user LBO template; company/transaction assumptions; operating projections; financing tranches; debt waterfall; exit assumptions; source data
outputs: template-shaped `.xlsx`; Sources & Uses; operating model; debt schedule; IRR/MOIC/returns; breakeven/sensitivity analysis; validated formulas
¬: ignore attached template; build from scratch when template exists; hardcode calculations; invent layout/sign convention; use circular ending-balance interest; let debt go negative; use even sensitivity dimensions; proceed past failed checkpoint; fabricate data; deliver red workbook

Headless `openpyxl` writes the workbook. Follow `excel-author` conventions for
formulas, named ranges, colors, comments, formats, and recalculation.

## When to Use

- evaluate sponsor leverage, debt paydown, exit returns, IRR, or MOIC
- populate an LBO template with dynamic Sources & Uses, operations, debt, and returns

## Template Gate (First)

Always check for an attached template:

1. attached/provided template → copy/use exact structure
2. no template → ask: “Do you have a specific LBO template you'd like me to use? If not, I can use the standard template which includes Sources & Uses, Operating Model, Debt Schedule, and Returns Analysis.”
3. standard template → copy `examples/LBO_Model.xlsx`, then populate assumptions

Never choose “build from scratch” when `LBO_Model.xlsx` is attached, even if it
contains more features than requested.

## Environment and Hard Rules

```text
headless openpyxl → .xlsx on disk
recalculate: python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx
```

- every calculation is an Excel formula string (`ws["D20"] = "=B5*B6"`), never a Python-calculated hardcode
- use template layout, proper cell references, and its sign convention consistently (outflows may be negative or positive)
- work section-by-section: complete, show, validate, and get confirmation before moving on

### Font colors

- blue `0000FF`: hardcoded input
- black `000000`: calculation formula using operators/functions (`=B4*B5`, `=SUM()`, `=-MAX(0,B4)`)
- purple `800080`: direct same-tab link (`=B9`, `=B45`)
- green `008000`: direct cross-tab link (`=Assumptions!B5`, `='Operating Model'!C10`)

### Fill palette

Default fills are restrained: only blue/grey/white, unless template/user colors
override. Section headers dark blue `#1F4E79` + white bold; period headers light
blue `#D9E1F2` + black bold; inputs light grey `#F2F2F2` or white (blue font);
formulas white; key outputs medium blue `#BDD7EE` + black bold. Fill colors are
separate from font colors.

### Number formats

- currency `$#,##0;($#,##0);"-"` or template's `$#,##0.0`
- percent `0.0%`
- multiples `0.0"x"`
- MOIC/detailed ratios `0.00"x"`
- all numeric cells right-aligned

## Procedure

### 1. Clarify and analyze template

Before formulas:

- map every section and dependencies
- identify timeline columns, Closing/Pro Forma columns, and projection start
- identify input/formula cells from colors, borders, shading
- read labels exactly; do not infer required calculations
- inspect existing formulas; preserve working formulas unless asked
- note sign convention, subtotal structures, tabs, and component organization
- ask if structure, method, requirements, or key assumptions are unclear

### 2. Fill each formula using hierarchy

For each required cell:

1. template: existing formula? verify and move on; inspect comments, labels, neighbors
2. user: follow requested method/assumptions/special requirements
3. standard LBO practice: document assumptions; ask if genuinely uncertain

### 3. Build and checkpoint sections

#### Sources & Uses

Balance Sources = Uses; identify the plug and calculate it as the difference.
Show the balanced table, confirm plug/signs, then stop before operating model.

#### Operating Model / Projections

Build revenue/top line from drivers/growth; costs and expenses; subtotals/totals;
margins/ratios; links to assumptions. Show projected P&L, confirm growth/margins,
then stop before debt schedule.

#### Debt Schedule

Build tranche balances, interest, paydown, and priority waterfall. Use beginning
balance for interest to break circularity:

`Interest → Cash Flow → Paydown → Ending Balance`

Use `MAX`/`MIN` so balances cannot go negative. Show beginning/ending balances and
interest; confirm waterfall before returns.

#### Returns

Investment cash flow negative; proceeds positive; IRR uses consecutive periods;
XIRR requires dates; MOIC = Total Proceeds / Total Investment. Show cash-flow
series and IRR/MOIC, confirm signs/ranges before sensitivities.

#### Sensitivities

Use odd 5×5 or 7×7 dimensions; symmetric axes `[base-2Δ, base-Δ, base,
base+Δ, base+2Δ]`; center is base output; center fill `#BDD7EE` + bold; all
cells explicit formulas with mixed refs (e.g. `$A5`, `B$4`), not Excel Data Table.
Each cell must differ as drivers vary and move directionally (higher exit
multiple → higher IRR, etc.). Confirm the grid after building.

### 4. Recalculate and repair

```bash
python /path/to/excel-author/scripts/recalc.py model.xlsx
```

Require success with zero errors. Fix all errors before delivery.

## Common Problem Areas

- balancing: one identified plug equals difference
- taxes: only relevant income line × tax rate; decide whether losses create tax shields or are ignored; do not reference unrelated debt schedules
- interest circularity: beginning balance, not average/ending, for interest
- debt: priority waterfall; cash sweep honors priority; `MAX`/`MIN` prevent negative balances
- returns: correct signs; complete IRR/XIRR ranges and dates; MOIC formula
- sensitivity: odd grid, centered base, explicit formulas, mixed refs, varying values

## Verification Checklist

### Formula validation

Run recalc helper; output must be success with zero errors.

### Section balancing

- [ ] Sources/Uses and Assets/Liabilities (if applicable) balance exactly
- [ ] plug items correctly calculate the balancing figure
- [ ] matching amounts agree across sections

### Operating projections

- [ ] revenue/top line builds from drivers/growth
- [ ] costs/expenses and subtotals are appropriate
- [ ] margins/ratios reasonable; assumptions linked correctly

### Balance sheet (if applicable)

- [ ] Assets = Liabilities + Equity
- [ ] items link to schedules/roll-forwards
- [ ] beginning balances = prior ending balances
- [ ] check row exists and is zero

### Cash flow (if applicable)

- [ ] correct income start
- [ ] non-cash items and working capital signs correct
- [ ] Ending Cash = Beginning Cash + Net Cash Flow
- [ ] cash consistent across statements

### Supporting schedules

- [ ] Beginning + Changes = Ending
- [ ] schedules link to statements
- [ ] drivers and periods are consistent

### Debt/financing

- [ ] beginning balances tie to sources/prior period
- [ ] interest uses appropriate balance (typically beginning)
- [ ] paydowns respect availability/priority
- [ ] no negative ending balances
- [ ] tranches total correctly

### Returns/output

- [ ] exit/terminal values and adjustments correct
- [ ] signs: investment negative, proceeds positive
- [ ] IRR/MOIC cover all periods and are reasonable

### Sensitivity

- [ ] 5×5/7×7 odd dimension; symmetric around base
- [ ] center result equals actual IRR/MOIC and has `#BDD7EE` + bold
- [ ] row/column headers contain input values; every data cell is a formula
- [ ] values differ and move in expected directions

### Formatting/logical sanity

- [ ] blue inputs; black calculations; purple same-tab links; green cross-tab links
- [ ] numbers right-aligned and correctly formatted
- [ ] no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or other errors
- [ ] order of magnitude, signs, trends, and outputs are plausible

## Error Table

| Error | Fix |
|---|---|
| hardcoded calculation | formula referencing source cells |
| copied formula wrong | verify `$` anchoring and links |
| circular reference | beginning balances for interest; break circle |
| sections do not balance | identify/calculate plug as difference |
| impossible negative balance | `MAX(0, ...)`/`MIN` with available cash |
| IRR/return error | signs and complete range/dates |
| sensitivity same value | mixed refs `$A5`, `B$4` and varying inputs |
| roll-forward mismatch | beginning = prior ending links |
| inconsistent signs | follow template convention end-to-end |

## User Checkpoint Contract

If template and requirements conflict, ask preference. If errors appear, fix them
before moving on. Show key formulas/assumptions as helpful. Never present a
completed model without checking Sources & Uses, Operating Model, Debt Schedule,
Returns, and Sensitivities in order.

## Data Sources — MCP First, Web Fallback

If configured, structured financial-data MCPs (Daloopa etc.) are preferred for
point-in-time comps, precedents, and filings. Otherwise use `web_search` /
`web_extract` with SEC EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`), company
IR pages, `browser_navigate`, or user data. Ask when absent; never fabricate and
mark unavailable values `[UNSOURCED]`.

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0).
Office-JS/Cowork paths removed; targets headless openpyxl through `excel-author`.
Original: https://github.com/anthropics/financial-services