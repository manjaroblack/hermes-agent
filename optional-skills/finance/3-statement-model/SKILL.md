---
name: 3-statement-model
description: Build integrated IS/BS/CF financial workbooks in Excel.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, three-statement, income-statement, balance-sheet, cash-flow, excel, openpyxl, modeling]
    related_skills: [excel-author, pptx-author, dcf-model, lbo-model]
---

# 3-Statement Financial Model

role: integrated Income Statement/Balance Sheet/Cash Flow workbook builder and auditor
do: inspect template; map tabs/inputs/dependencies; populate historicals; build formula-driven projections/schedules; add optional margins/credit/scenarios; validate statements and audit checks; recalculate with LibreOffice; document sources
inputs: xlsx template; historical actuals; assumptions/drivers; scenario selector; schedules; sourced public-company data; user format/period/unit choices
outputs: recalculated `.xlsx`; linked IS/BS/CF and schedules; optional analysis blocks; checks dashboard; documented sources/assumptions; unresolved `[UNSOURCED]` flags
¬: hardcode derived/projected values; overwrite formulas; build end-to-end without user checkpoints; add optional analyses unprompted; break named ranges/links; deliver formula errors; fabricate financial data; claim unsourced values sourced

Headless `openpyxl` produces the workbook. Follow `excel-author` conventions for
cell colors, formulas, named ranges, sensitivity tables, and recalculation:

```bash
python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx
```

## When to Use

- complete an existing integrated three-statement template
- build linked IS/BS/CF projections with supporting schedules
- add optional margin analysis, credit metrics, or Bear/Base/Bull scenarios when requested
- audit cross-statement integrity, formulas, units, and source documentation

## Non-Negotiable Constraints

### Formula policy

- every projection cell, roll-forward, linkage, and subtotal is an Excel formula
- with `openpyxl`, write `ws["D15"] = "=D14*(1+Assumptions!$B$5)"`, never a computed number
- hardcoded numbers only: historical actuals and assumption drivers in Assumptions tab
- if Python computes a value for a cell, stop and replace with formula; scenarios must flex

### User checkpoints

Do not populate end-to-end silently. Confirm each stage:

1. template map: identified tabs/sections before touching cells
2. historical block: values/periods match source
3. IS projections: subtotal checks and projected IS before BS
4. BS: Assets = Liabilities + Equity for every period before CF
5. CF: ending cash equals BS cash before finalizing
6. final: resolve/document errors, scenarios, units, and placeholders

### Default palette and cell meaning

Use template/user style when supplied. Otherwise use only dark/light/medium
blues, light grey, and white; no extra accent colors:

| Element | Fill | Font |
|---|---|---|
| IS/BS/CF section headers | dark blue `#1F4E79` | white bold |
| FY2024A/FY2025E column headers | light blue `#D9E1F2` | black bold |
| historicals/assumption drivers | light grey `#F2F2F2` or white | blue `#0000FF` |
| formulas | white | black |
| cross-tab links | white | green `#008000` |
| checks/key totals | medium blue `#BDD7EE` | black bold |

Font says what a cell is (input/formula/link); fill says where it is
(header/data/check). Keep colors minimal.

## Procedure

### 1. Inspect and map the template

Review every tab before writing. Common tabs:

| Tab names | Content |
|---|---|
| IS, P&L, Income Statement | Income Statement |
| BS, Balance Sheet | Balance Sheet |
| CF, CFS, Cash Flow | Cash Flow Statement |
| WC, Working Capital | working-capital schedule |
| DA, D&A, Depreciation, PP&E | depreciation/amortization schedule |
| Debt, Debt Schedule | debt schedule |
| NOL, Tax, DTA | NOL schedule |
| Assumptions, Inputs, Drivers | drivers/inputs |
| Checks, Audit, Validation | error dashboard |

Checklist:

- record existing and template-specific tabs; not all schedules exist
- understand dependencies (e.g. Assumptions → IS → BS → CF)
- locate input/formula cells, named ranges, title, section headers, units row
- distinguish historical Actual vs projected Estimate columns and period labels
- verify line items, leftmost labels, historical-before-projection order, and separator borders
- inspect named ranges for growth, cost %, Net Income, EBITDA, debt, cash, scenario selector

Projection usually extends five years from last historical year; confirm rather
than assume. Preserve fiscal labels such as `FY2024A`, `FY2025E`.

### 2. Plan structure before formulas

Define all row positions, section dividers, blank rows, and column headers first;
then write formulas against locked positions. Do not insert/delete rows/columns
after formulas without checking every tab dependency.

### 3. Populate safely

| Rule | Requirement |
|---|---|
| input cells only | never overwrite existing formulas unless intentionally replacing/documenting one |
| references | paste values for source inputs; preserve formulas/formatting |
| units | match thousands/millions/actuals and document scale |
| signs | follow template convention for expenses, assets, liabilities, cash flows |
| circularity | if intended, enable iterative calculation |
| order | historicals → assumption drivers → outputs/checks |

Safe sequence: identify inputs; enter historical data and check calculations;
enter assumption drivers; inspect outputs; document any intentional formula
replacement. Temporary `#REF!`/`#DIV/0!` from unpopulated inputs may occur, but
all errors must be resolved before delivery.

### 4. Optional margin analysis

Only when user prompts or template requires it. On IS, display percentages below
profit lines:

| Margin | Formula | Measures |
|---|---|---|
| Gross Margin | Gross Profit / Revenue | pricing/production efficiency |
| EBITDA Margin | EBITDA / Revenue | core operating profitability |
| EBIT Margin | EBIT / Revenue | operating profitability after D&A |
| Net Income Margin | Net Income / Revenue | bottom-line profitability |

### 5. Optional credit analysis

Only when prompted/required. On BS:

| Metric | Formula | Measures |
|---|---|---|
| Total Debt / EBITDA | Total Debt / LTM EBITDA | leverage |
| Net Debt / EBITDA | (Total Debt - Cash) / LTM EBITDA | net leverage |
| Interest Coverage | EBITDA / Interest Expense | debt service |
| Debt / Total Cap | Total Debt / (Total Debt + Equity) | capital structure |
| Debt / Equity | Total Debt / Total Equity | financial leverage |
| Current Ratio | Current Assets / Current Liabilities | liquidity |
| Quick Ratio | (Current Assets - Inventory) / Current Liabilities | immediate liquidity |

Expected hierarchy: leverage Upside < Base < Downside; coverage and liquidity
Upside > Base > Downside. Add covenant threshold compliance checks if covenants
are known.

### 6. Optional scenario analysis

Only when requested. Use an Assumptions dropdown and `CHOOSE` or `INDEX/MATCH`:

| Scenario | Meaning |
|---|---|
| Base | management guidance/consensus |
| Upside | above-guidance growth, margin expansion |
| Downside | below-trend growth, margin compression |

Sensitize revenue growth, gross margin, SG&A %, DSO/DIO/DPO, CapEx %, interest
rate, and tax rate. Toggling must change all statements; BS must balance, cash
must tie, and hierarchy must hold for NI/EBITDA/FCF/margins.

### 7. Retrieve data

If public-company filing extraction is required, use
`references/sec-filings.md`. Prefer structured financial-data MCP when
configured (S&P Kensho, FactSet, Daloopa, or equivalent). Otherwise use SEC
EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`), company IR pages, interactive
data portals, or explicitly user-provided data. Never fabricate; mark an
unsourced multiple/filing number `[UNSOURCED]` and surface it.

### 8. Validate formulas and linkages

Use Excel trace precedents/dependents, Evaluate Formula, test values, and compare
formula logic across periods. Check:

- absolute/relative reference errors; external/deleted links; circularity; inconsistent projection formulas
- duplicated cross-tab values versus links; schedule totals versus statements; aligned periods
- IS: source revenue; expense totals; Gross Profit/EBIT/EBT/NI; tax handles losses; forecasts reference assumptions; directionally sensible changes
- BS: Assets = Liabilities + Equity; cash = CF ending cash; working capital/debt schedules tie; retained earnings = prior RE + NI - dividends +/- adjustments; signs appropriate
- CF: NI/CFO ties to IS; D&A/SBC/non-cash add-backs tie; increase in asset is negative cash; CapEx and financing tie; ending cash = BS cash; beginning cash = prior ending cash
- schedules: opening = prior closing; Beginning + Additions - Deductions = Ending; totals and assumptions tie

Cross-statement checks:

| Check | Formula | Expected |
|---|---|---|
| BS balance | Assets - Liabilities - Equity | 0 |
| cash tie-out | CF Ending Cash - BS Cash | 0 |
| NI link | IS Net Income - CF Starting Net Income | 0 |
| retained earnings | Prior RE + NI - Dividends - BS Ending RE | 0; adjust SBC/other items as needed |

### 9. Audit categories

Run these on the Checks/Audit tab when present or create equivalent checks:

1. currency: documented currency, consistent symbol/scale, correct units row
2. BS: Assets - Liabilities - Equity = 0 every period
3. CF: ending cash ties BS; monthly/annual closing cash ties; NI, D&A, SBC, ΔAR, ΔInventory, ΔAP, CapEx tie sources
4. RE: Prior RE + NI + SBC - Dividends = ending RE, with component breakdown
5. WC: AR/inventory/AP tie BS; DSO/DIO/DPO reasonable and flagged out of range
6. debt: current + long-term debt ties BS; interest ties IS
7. equity financing: BS Common Stock/APIC change = CFF equity issuance; Year 0 raise = Year 1 beginning equity; cash and equity increase tie
8. NOL: formation beginning NOL = 0; only EBT < 0 generates NOL; DTA ties BS; utilization ≤80% of EBT; balance non-negative; tax expense = 0 when taxable income ≤0
9. scenario: absolute NI/EBITDA/FCF and margins Upside > Base > Downside; leverage inverted
10. formula integrity: COGS/S&M/G&A/R&D/SBC are % Revenue formulas; projection formulas consistent; no `#REF!`, `#DIV/0!`, `#VALUE!`
11. credit thresholds: flag Green/Yellow/Red against known covenants and summarize red flags

Master status: `✓ ALL CHECKS PASS` only when every section passes; otherwise
`✗ ERRORS DETECTED - REVIEW BELOW`. Debug red sections → category → source tab
→ fix root cause → recheck Checks tab.

### 10. Handle circularity

Interest → Net Income → Cash → Debt Balance → Interest may be circular. In
Excel: File → Options → Formulas → Enable iterative calculation; maximum
iterations 100, maximum change 0.001. Add a circuit-breaker toggle in Assumptions.

### 11. Recalculate and final review

Run the `excel-author` recalculator before delivery. Resolve every error until
status is `success`. Review all `#REF!`, `#DIV/0!`, `#VALUE!`, and `#NAME?`;
confirm inputs/placeholders, units, scenario behavior, and clean save.

## Verification

- workbook opens as `.xlsx` with linked IS/BS/CF and preserved template formulas
- no derived/projection hardcodes; input comments and source links exist
- each user checkpoint was shown/confirmed
- all requested optional blocks and audit checks pass
- BS, cash, NI, RE, schedules, scenarios, and NOL/equity/debt checks reconcile
- recalculate with `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`; status is `success` and formula-error count is zero
- unsupported/unsourced inputs are explicitly flagged, never invented

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0).
Office-JS/Cowork live-Excel paths were removed; this version targets headless
`openpyxl` through `excel-author`. Original:
https://github.com/anthropics/financial-services