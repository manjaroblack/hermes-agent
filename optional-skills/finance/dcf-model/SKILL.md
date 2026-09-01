---
name: dcf-model
description: Build discounted cash flow valuation workbooks in Excel.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, valuation, dcf, excel, openpyxl, modeling, investment-banking]
    related_skills: [excel-author, pptx-author, comps-analysis, lbo-model, 3-statement-model]
---

# DCF Model Builder

role: institutional discounted-cash-flow valuation workbook builder/auditor
do: source/validate inputs; model history/revenue/OpEx/FCF/WACC/discounting/terminal value; bridge EV to equity/share price; build Bear/Base/Bull scenarios and full sensitivity grids; document sources; recalculate/error-audit workbook
inputs: company/ticker; historical financials; market price/shares/debt/cash/beta; growth/margin/tax/CapEx/NWC assumptions; WACC inputs; projection period; user/template/style
outputs: two-sheet `.xlsx` (DCF + WACC); linked formula-driven valuation; three full sensitivity tables; scenario selector; source comments; success recalculation JSON; `[UNSOURCED]` flags where necessary
¬: write derived values as numbers; build end-to-end without checkpoints; use Excel Data Tables/linear approximations/placeholders; put sensitivities on separate sheet; terminal growth ≥ WACC; omit comments/borders/formula errors; fabricate market/filing data; expose credentials

Headless `openpyxl` creates the workbook. Follow `excel-author` conventions for
formulas, colors, named ranges, number formats, and sensitivity tables.

## When to Use

- create a DCF valuation and implied share price
- compare Bear/Base/Bull outcomes
- stress WACC, terminal growth, growth/margins, beta/risk-free assumptions
- audit formula integrity, valuation bridge, and spreadsheet errors

## Environment and Hard Rules

### Formula policy

- every projection, margin, discount factor, PV, and sensitivity cell is a live Excel formula
- correct: `ws["D20"] = "=D19*(1+$B$8)"`; wrong: `ws["D20"] = calculated_revenue`
- hardcoded numbers only: raw historical inputs, assumption drivers (growth, WACC, terminal g), current market data (price, debt/cash)
- if Python computes a value and writes it as a number, stop; model must flex when assumptions change

### User checkpoints

Do not build end-to-end. Show/confirm:

1. raw input block (revenue, margins, shares, net debt) before projections
2. projected top line/growth before margin build
3. full FCF schedule before WACC
4. WACC inputs/calculation before discounting
5. EV → equity → share-price bridge before sensitivities

Catch errors at each stage; late margin errors require rebuilding downstream.

### Sensitivity rules

- use odd rows/columns, normally 5×5 (sometimes 7×7), so center exists
- center headers equal actual model assumptions; center output equals actual implied share price
- highlight center with medium blue `#BDD7EE` + bold font
- populate all cells (3×25 = 75 normally) with full DCF formulas, via openpyxl loops
- no placeholder, approximation, manual Data Table, or manual intervention

### Source comments

Add comments as each hardcoded value is created; format:
`Source: [System/Document], [Date], [Reference], [URL if applicable]`. Every blue
input must have comment before next section; never defer/TODO.

### Row planning and recalculation

Define all section row positions first; write headers/labels, dividers, blank rows,
then formulas. Recalculate before delivery:

```bash
python recalc.py model.xlsx 30
```

Fix every `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#NULL!`, `#NUM!`, `#N/A` until
status is `success`.

## Procedure

### 1. Retrieve and validate data

Priority: configured structured financial MCPs (Daloopa etc.) → user-provided
data → web/SEC/current market data when needed. Validate net debt/net cash,
diluted shares (buybacks/issuances), historical margins, growth versus industry,
and reasonable tax rate (typically 21-28%). Never fabricate; surface
`[UNSOURCED]` cells.

### 2. Analyze 3-5 years of history

Document revenue growth/CAGR and drivers; gross/EBIT/FCF margin progression;
D&A/CapEx as revenue; NWC as change in revenue; ROIC/ROE. Summary:

```text
Historical Metrics (LTM):
Revenue: $X million
Revenue growth: X% CAGR
Gross margin: X%
EBIT margin: X%
D&A % of revenue: X%
CapEx % of revenue: X%
FCF margin: X%
```

### 3. Project revenue

Start from latest actual/LTM; apply yearly growth; show dollars and growth %.
Near-term growth may be higher, years 3-4 moderate toward industry average, year
5+ approaches terminal growth. Formulas:

- Revenue(N) = Revenue(N-1) × (1 + Growth Rate)
- Growth %(N) = Revenue(N) / Revenue(N-1) - 1

```text
Bear Case: Conservative growth (e.g., 8-12%)
Base Case: Most likely scenario (e.g., 12-16%)
Bull Case: Optimistic growth (e.g., 16-20%)
```

### 4. Model operating expenses

Base S&M, R&D, G&A on revenue, not gross profit; keep line items separate;
calculate EBIT = Gross Profit - Total OpEx; allow operating leverage as scale
increases:

- S&M typically 15-40% revenue
- R&D typically 10-30% for technology
- G&A typically 8-15%

```text
Current State → Target State (Year 5)
Gross Margin: X% → Y% (justify based on scale, efficiency)
EBIT Margin: X% → Y% (result of revenue growth + opex leverage)
```

### 5. Calculate unlevered FCF

```text
EBIT
(-) Taxes (EBIT × Tax Rate)
= NOPAT (Net Operating Profit After Tax)
(+) D&A (non-cash expense, % of revenue)
(-) CapEx (% of revenue, typically 4-8%)
(-) Δ NWC (change in working capital)
= Unlevered Free Cash Flow
```

NWC is % of revenue change; typical range -2% to +2% of revenue change; negative
is source of cash/release, positive is use/build. Distinguish maintenance CapEx
(~2-3% revenue) from growth CapEx (additional 2-5%) and align total to strategy.

### 6. Calculate WACC

CAPM:

```text
Cost of Equity = Risk-Free Rate + Beta × Equity Risk Premium

Where:
- Risk-Free Rate = Current 10-Year Treasury Yield
- Beta = 5-year monthly stock beta vs market index
- Equity Risk Premium = 5.0-6.0% (market standard)
```

Debt:

```text
After-Tax Cost of Debt = Pre-Tax Cost of Debt × (1 - Tax Rate)

Determine Pre-Tax Cost of Debt from:
- Credit rating (if available)
- Current yield on company bonds
- Interest expense / Total Debt from financials
```

Capital structure:

```text
Market Value Equity = Current Stock Price × Shares Outstanding
Net Debt = Total Debt - Cash & Equivalents
Enterprise Value = Market Cap + Net Debt

Equity Weight = Market Cap / Enterprise Value
Debt Weight = Net Debt / Enterprise Value

WACC = (Cost of Equity × Equity Weight) + (After-Tax Cost of Debt × Debt Weight)
```

If cash > debt, net debt is negative and debt weight may be negative; no debt →
WACC = cost of equity. Typical WACC: stable large cap 7-9%, growth 9-12%, high
growth/risk 12-15%.

### 7. Discount explicit cash flows

Default mid-year periods: `0.5, 1.5, 2.5, 3.5, 4.5, ...`; factor =
`1 / (1 + WACC)^Period`.

```text
For each projection year:
PV of FCF = Unlevered FCF × Discount Factor

Example (Year 1):
FCF = $1,000
WACC = 10%
Period = 0.5
Discount Factor = 1 / (1.10)^0.5 = 0.9535
PV = $1,000 × 0.9535 = $954
```

Projection period: 5 years standard; 7-10 for high-growth runway; 3 for mature
stable businesses.

### 8. Calculate terminal value

Preferred perpetuity method:

```text
Terminal FCF = Final Year FCF × (1 + Terminal Growth Rate)
Terminal Value = Terminal FCF / (WACC - Terminal Growth Rate)

Critical Constraint: Terminal Growth < WACC (otherwise infinite value)
```

Terminal g: conservative 2.0-2.5% (GDP), moderate 2.5-3.5%, aggressive 3.5-5.0%
only for market leaders; do not exceed risk-free rate or long-term GDP growth.

Alternative exit multiple:

```text
Terminal Value = Final Year EBITDA × Exit Multiple

Where Exit Multiple comes from:
- Industry comparable trading multiples
- Precedent transaction multiples
- Typical range: 8-15x EBITDA
```

PV terminal value = Terminal Value / `(1 + WACC)^Final Period`; with five-year
mid-year model final period is 4.5. Terminal value should be 50-70% EV; >75%
signals over-reliance; <40% warrants checking conservative assumptions.

### 9. Bridge enterprise to equity

```text
(+) Sum of PV of Projected FCFs = $X million
(+) PV of Terminal Value = $Y million
= Enterprise Value = $Z million

(-) Net Debt [or + Net Cash if negative] = $A million
= Equity Value = $B million

÷ Diluted Shares Outstanding = C million shares
= Implied Price per Share = $XX.XX

Current Stock Price = $YY.YY
Implied Return = (Implied Price / Current Price) - 1 = XX%
```

Net debt = total debt - cash; positive net debt subtracts from EV, negative adds.
Use diluted shares including options/RSUs/convertibles. Consider minority
interests, pension liabilities, and operating leases where applicable.

Output table:

```csv
Valuation Component,Amount ($M)
PV Explicit FCFs,X.X
PV Terminal Value,Y.Y
Enterprise Value,Z.Z
(-) Net Debt,A.A
Equity Value,B.B
,,
Shares Outstanding (M),C.C
Implied Price per Share,$XX.XX
Current Share Price,$YY.YY
Implied Upside/(Downside),+XX%
```

### 10. Build three sensitivity tables

Place at bottom of DCF sheet, not separate sheet:

1. WACC vs Terminal Growth
2. Revenue Growth vs EBIT Margin
3. Beta vs Risk-Free Rate

They are regular 2D formula grids, not Excel Data Tables. Each cell fully
recalculates implied share price for its row/column assumptions. All 75 cells
must work immediately on open; no linear approximation/manual population.

## Correct Patterns

### Scenario blocks and consolidation

Create separate Bear/Base/Bull blocks with assumptions horizontal over projection
years. Each block has a merged section title, required year header row, and data:

```csv
BEAR CASE ASSUMPTIONS (section header, merge cells across)
Assumption,FY1,FY2,FY3,FY4,FY5
Revenue Growth (%),12%,10%,9%,8%,7%
EBIT Margin (%),45%,44%,43%,42%,41%

BASE CASE ASSUMPTIONS (section header, merge cells across)
Assumption,FY1,FY2,FY3,FY4,FY5
Revenue Growth (%),16%,14%,12%,10%,9%
EBIT Margin (%),48%,49%,50%,51%,52%

BULL CASE ASSUMPTIONS (section header, merge cells across)
Assumption,FY1,FY2,FY3,FY4,FY5
Revenue Growth (%),20%,18%,15%,13%,11%
EBIT Margin (%),50%,51%,52%,53%,54%
```

Case selector: 1=Bear, 2=Base, 3=Bull. Create a consolidation/Selected column
with `INDEX` or `OFFSET`, and have projections reference it. Recommended:
`=INDEX(B10:D10, 1, $B$6)`. The centralized approach is auditable and preferred
to scattered nested IFs. If documenting the direct selection alternative, its
shape is:
`=IF($B$6=1,[Bear cell],IF($B$6=2,[Base cell],[Bull cell]))`.

Revenue pattern:

```text
Consolidation FY1 growth: =INDEX([Bear FY1 growth]:[Bull FY1 growth], 1, $B$6)
Revenue Year 1: =D29*(1+$E$10)
```

`D29` is prior revenue, `$E$10` selected FY1 growth, `$B$6` selector. Do not
embed selection logic in every projection.

FCF pattern:

```csv
Item,Formula,Reference
D&A,=E29*$E$21,$E$21 = consolidation column for D&A %
CapEx,=E29*$E$22,$E$22 = consolidation column for CapEx %
Δ NWC,=(E29-D29)*$E$23,$E$23 = consolidation column for NWC %
Unlevered FCF,=E57+E58-E60-E62,E57=NOPAT E58=D&A E60=CapEx E62=Δ NWC
```

Confirm scenario row locations and consolidation columns before formulas.

### Correct comments

```csv
Item,Source Comment
Stock price,Source: Market data script 2025-10-12 Close price
Shares outstanding,Source: 10-K FY2024 Page 45 Note 12
Historical revenue,Source: 10-K FY2024 Page 32 Consolidated Statements
Beta,Source: Market data script 2025-10-12 5-year monthly beta
Consensus estimates,Source: Management guidance Q3 2024 earnings call
```

### Correct sensitivity implementation

Use odd symmetric axes centered on actual assumptions. Example base WACC 9.0%,
terminal g 3.0%, step 0.5%:

```csv
WACC vs Terminal Growth,  2.0%,  2.5%,  3.0%,  3.5%,  4.0%
              8.0%,       [fml], [fml], [fml], [fml], [fml]
              8.5%,       [fml], [fml], [fml], [fml], [fml]
              9.0%,       [fml], [fml], [★  ], [fml], [fml]
              9.5%,       [fml], [fml], [fml], [fml], [fml]
             10.0%,       [fml], [fml], [fml], [fml], [fml]
                                   ↑
                          middle col = base terminal g
```

Axis values: `[base - 2*step, base - step, base, base + step, base + 2*step]`.
Cell B88 uses WACC `$A88` and growth `B$87`; center must equal valuation summary
share price. Every grid cell needs a full recalculation formula.

```python
# Pseudocode for populating sensitivity table
for row_idx, wacc_value in enumerate(wacc_range):
    for col_idx, term_growth_value in enumerate(term_growth_range):
        # Build formula that uses wacc_value and term_growth_value
        formula = f"=<DCF recalc using {wacc_value} and {term_growth_value}>"
        ws.cell(row=start_row+row_idx, column=start_col+col_idx).value = formula
```

### Correct row planning

```csv
Row,Content
1,[Company Name] DCF Model
2,Ticker | Date | Year End
4,Case Selector
7,KEY ASSUMPTIONS
26,Assumption headers
27-31,Growth assumptions
...,...
```

Write headers/labels → dividers/blank rows → formulas → immediate formula tests.
Think foundation/walls, not formulas before headers.

## Pitfalls

### Sensitivity shortcuts

Never use linear approximations, division shortcuts, empty cells, or notes telling
the user to use Data → What-If Analysis → Data Table. Relationships are nonlinear;
manual notes make model incomplete. Write every formula in a Python loop.

### Missing comments/shifted rows

Do not create blue hardcodes without comments/TODO. Lock rows before formulas;
otherwise inserted headers shift references (e.g. D&A/CapEx point at wrong rows).

### Scenario/layout errors

Use separate Bear/Base/Bull horizontal blocks with year headers, not one vertical
Bear/Base/Bull row per assumption. Centralize selection and verify references.

### Presentation errors

Professional models require section borders, distinguish blue hardcoded inputs,
black formulas, green sheet links, and do not make all cells black. Keep formulas
and color semantics auditable.

### Calculation errors

- OpEx based on gross profit instead of revenue
- wrong WACC inputs: book vs market values, beta misuse, tax application, stale 10Y Treasury, net cash ignored
- terminal g ≥ WACC; projections unsupported by history/industry/unit economics; unsubstantiated margin expansion
- terminal value >80% EV, inconsistent steady-state margins, wrong discount period
- D&A/CapEx/NWC/tax/NOPAT/working-capital sign errors

Top five: off-row references; missing comments; simplified sensitivities; wrong
scenario blocks; missing borders.

## Workbook Deliverable

### Required architecture

Exactly two sheets:

1. `DCF`: main valuation model; sensitivities at bottom
2. `WACC`: cost of capital calculation

Naming: `[Ticker]_DCF_Model_[Date].xlsx`. Features: case selector 1/2/3,
consolidation INDEX/OFFSET formulas, color-coded cells, comments on all inputs,
professional borders.

### DCF sheet structure

Header:

```csv
Row,Content
1,[Company Name] DCF Model
2,Ticker: [XXX] | Date: [Date] | Year End: [FYE]
3,Blank
4,Case Selector Cell (1=Bear 2=Base 3=Bull)
5,Case Name Display (formula: =IF([Selector]=1"Bear"IF([Selector]=2"Base""Bull")))
```

Market data (not case-dependent):

```csv
Item,Value
Current Stock Price,$XX.XX
Shares Outstanding (M),XX.X
Market Cap ($M),[Formula]
Net Debt ($M),XXX [or Net Cash if negative]
```

Scenario assumptions: separate Bear/Base/Bull DCF-specific blocks (Revenue
Growth %, EBIT Margin %, Tax Rate %, D&A % Revenue, CapEx % Revenue, NWC Change
% ΔRev, Terminal Growth Rate, WACC), horizontal across years, section title +
required year header + data rows, then Selected consolidation column.

Historical/projected matrix:

```csv
Income Statement ($M),2020A,2021A,2022A,2023A,2024E,2025E,2026E
Revenue,XXX,XXX,XXX,XXX,[=E29*(1+$E$10)],[=F29*(1+$E$11)],[=G29*(1+$E$12)]
  % growth,XX%,XX%,XX%,XX%,[=E29/D29-1],[=F29/E29-1],[=G29/F29-1]
,,,,,,
Gross Profit,XXX,XXX,XXX,XXX,[=E29*E33],[=F29*F33],[=G29*G33]
  % margin,XX%,XX%,XX%,XX%,[=E33/E29],[=F33/F29],[=G33/G29]
,,,,,,
Operating Expenses:,,,,,,,
  S&M,XXX,XXX,XXX,XXX,[=E29*0.15],[=F29*0.14],[=G29*0.13]
  R&D,XXX,XXX,XXX,XXX,[=E29*0.12],[=F29*0.11],[=G29*0.10]
  G&A,XXX,XXX,XXX,XXX,[=E29*0.08],[=F29*0.07],[=G29*0.07]
  Total OpEx,XXX,XXX,XXX,XXX,[=E36+E37+E38],[=F36+F37+F38],[=G36+G37+G38]
,,,,,,
EBIT,XXX,XXX,XXX,XXX,[=E33-E39],[=F33-F39],[=G33-G39]
  % margin,XX%,XX%,XX%,XX%,[=E41/E29],[=F41/F29],[=G41/G29]
,,,,,,
Taxes,(XX),(XX),(XX),(XX),[=E41*$E$24],[=F41*$E$24],[=G41*$E$24]
  Tax rate,XX%,XX%,XX%,XX%,[=E43/E41],[=F43/F41],[=G43/G41]
,,,,,,
NOPAT,XXX,XXX,XXX,XXX,[=E41-E43],[=F41-F43],[=G41-G43]
```

Reference Selected cells, not scattered selection logic. FCF:

```csv
Cash Flow ($M),2020A,2021A,2022A,2023A,2024E,2025E,2026E
NOPAT,XXX,XXX,XXX,XXX,[=E45],[=F45],[=G45]
(+) D&A,XXX,XXX,XXX,XXX,[=E29*$E$21],[=F29*$E$21],[=G29*$E$21]
    % of Rev,XX%,XX%,XX%,XX%,[=E58/E29],[=F58/F29],[=G58/G29]
(-) CapEx,(XX),(XX),(XX),(XX),[=E29*$E$22],[=F29*$E$22],[=G29*$E$22]
    % of Rev,XX%,XX%,XX%,XX%,[=E60/E29],[=F60/F29],[=G60/G29]
(-) Δ NWC,(XX),(XX),(XX),(XX),[=(E29-D29)*$E$23],[=(F29-E29)*$E$23],[=(G29-F29)*$E$23]
    % of Δ Rev,XX%,XX%,XX%,XX%,[=E62/(E29-D29)],[=F62/(F29-E29)],[=G62/(G29-F29)]
,,,,,,
Unlevered FCF,XXX,XXX,XXX,XXX,[=E57+E58-E60-E62],[=F57+F58-F60-F62],[=G57+G58-G60-G62]
```

Confirm `$E$21` D&A, `$E$22` CapEx, `$E$23` NWC, `E29` Revenue, `E45` NOPAT
row locations before writing; test one column then copy.

DCF valuation:

```csv
DCF Valuation,2024E,2025E,2026E,2027E,2028E,Terminal
Unlevered FCF ($M),XXX,XXX,XXX,XXX,XXX,
Period,0.5,1.5,2.5,3.5,4.5,
Discount Factor,0.XX,0.XX,0.XX,0.XX,0.XX,
PV of FCF ($M),XXX,XXX,XXX,XXX,XXX,
,,,,,,
Terminal FCF ($M),,,,,,,XXX
Terminal Value ($M),,,,,,,XXX
PV Terminal Value ($M),,,,,,,XXX
,,,,,,
Valuation Summary ($M),,,,,,
Sum of PV FCFs,XXX,,,,,
PV Terminal Value,XXX,,,,,
Enterprise Value,XXX,,,,,
(-) Net Debt,(XX),,,,,
Equity Value,XXX,,,,,
,,,,,,
Shares Outstanding (M),XX.X,,,,,
IMPLIED PRICE PER SHARE,$XX.XX,,,,,
Current Stock Price,$XX.XX,,,,,
Implied Upside/(Downside),XX%,,,,,
```

WACC sheet:

```csv
COST OF EQUITY CALCULATION,,
Risk-Free Rate (10Y Treasury),X.XX%,[Yellow input]
Beta (5Y monthly),X.XX,[Yellow input]
Equity Risk Premium,X.XX%,[Yellow input]
Cost of Equity,X.XX%,[Calculated blue]
,,
COST OF DEBT CALCULATION,,
Credit Rating,AA-,[Yellow input]
Pre-Tax Cost of Debt,X.XX%,[Yellow input]
Tax Rate,XX.X%,[Link to DCF sheet]
After-Tax Cost of Debt,X.XX%,[Calculated blue]
,,
CAPITAL STRUCTURE,,
Current Stock Price,$XX.XX,[Link to DCF]
Shares Outstanding (M),XX.X,[Link to DCF]
Market Capitalization ($M),"X,XXX",[Calculated]
,,
Total Debt ($M),XXX,[Yellow input]
Cash & Equivalents ($M),XXX,[Yellow input]
Net Debt ($M),XXX,[Calculated]
,,
Enterprise Value ($M),"X,XXX",[Calculated]
,,
WACC CALCULATION,Weight,Cost,Contribution
Equity,XX.X%,X.X%,X.XX%
Debt,XX.X%,X.X%,X.XX%
,,
WEIGHTED AVERAGE COST OF CAPITAL,X.XX%,[Green output]
```

Key formulas: Market Cap = Price × Shares; Net Debt = Debt - Cash; EV = Market
Cap + Net Debt; Equity Weight = Market Cap / EV; Debt Weight = Net Debt / EV;
WACC = (CoE × Equity Weight) + (after-tax CoD × Debt Weight).

Sensitivities are vertically stacked at DCF rows 87+ (example): WACC/g rows
87-100, Revenue Growth/EBIT Margin 102-115, Beta/Risk-Free Rate 117-130; use
5×5 formula grids, leave 1-2 blank rows, conditionally format high/low values,
bold base case, and never use a separate sheet.

## Formatting and Audit Standards

### Fonts/fills/borders

Font colors: blue RGB `0,0,255` for all hardcodes, black `0,0,0` for formulas,
green `0,128,0` for sheet links. Default fills only:

- section headers: dark blue RGB `31,78,121` / `#1F4E79`, white bold
- sub/column headers: light blue RGB `217,225,242` / `#D9E1F2`, black bold
- inputs: light grey RGB `242,242,242` / `#F2F2F2` or white, blue font
- calculations: white/black
- outputs: medium blue RGB `189,215,238` / `#BDD7EE`, black bold

Three blues + one grey + white; user/template colors override. Thick 1.5pt
borders around KEY INPUTS, PROJECTION ASSUMPTIONS, 5-YEAR CASH FLOW PROJECTION,
TERMINAL VALUE, VALUATION SUMMARY, and each sensitivity table; medium 1pt
between Company Details/History and Growth/EBIT/FCF subsections; thin 0.5pt
around scenario and historical/projected tables; no individual interior borders.
Borders are required for client-ready output.

### Number formats/comments

- years as text (`2024` not `2,024`)
- percentages `0.0%`
- currency `$#,##0` millions and `$#,##0.00` per share; headers state units
- zeros displayed `-` (e.g. `$#,##0;($#,##0);-`)
- large numbers `#,##0`; negatives `(#,##0)`
- comment every hardcode immediately with source format above

### Recalculation output

```bash
python recalc.py [path_to_excel_file] [timeout_seconds]
python recalc.py AAPL_DCF_Model_2025-10-12.xlsx 30
```

Recalculator uses LibreOffice, scans all sheets/cells for errors, and returns:

```json
{
  "status": "success",
  "total_errors": 0,
  "total_formulas": 42,
  "error_summary": {}
}
```

Errors look like:

```json
{
  "status": "errors_found",
  "total_errors": 2,
  "total_formulas": 42,
  "error_summary": {
    "#REF!": {
      "count": 2,
      "locations": ["DCF!B25", "DCF!C25"]
    }
  }
}
```

Fix and rerun until success.

## Case Framework

| Case | Growth | Margins | WACC | Terminal g | CapEx |
|---|---|---|---|---|---|
| Bear | low historical range | compression/no expansion | higher risk premium | lower | higher |
| Base | consensus/management | moderate operating leverage | market-implied | GDP-aligned 2.5-3.0% | standard |
| Bull | high end | significant expansion | lower risk premium | 3.5-5.0% | reduced intensity |

Use consolidation column in all projections; centralization improves auditability.

## Variations and Quality

- high-growth tech: 7-10 years, 20-30% initial growth, margin expansion, WACC 12-15%, unit economics
- mature/stable: 3-5 years, GDP+1-3%, stable margins, WACC 7-9%, cash/capital allocation
- cyclical: model cycle, normalize mid-cycle margins, trough/peak, cyclicality-adjusted beta
- multi-segment: separate DCF per unit, segment growth/margins, sum-of-parts, synergies

Quality rubric: realistic history-based assumptions; correct CAPM/cost of capital;
comprehensive sensitivities; justified terminal value; scenario-ready structure;
transparent assumptions. Build incrementally, test sample values, document unusual
formulas, and add checks. Document assumptions, sources, methodology, uncertainty;
cross-check math, stress test, peer-review, and version work.

For errors/unreasonable results read `TROUBLESHOOTING.md`.

## Verification and Delivery

### Before delivery

1. Bear/Base/Bull blocks horizontal with year headers and functional selector
2. DCF sheet has all three sensitivities at bottom, each cell a formula
3. font colors: blue inputs, black formulas, green sheet links
4. comments on all hardcoded inputs; professional borders around major sections
5. OpEx based on revenue, not gross profit
6. terminal value 50-70% EV; terminal growth < WACC; tax 21-28%
7. formulas recalculate with zero errors; spot-check FCF rows and selector behavior
8. filename `[Ticker]_DCF_Model_[Date].xlsx`; two sheets only

### Final checklist

- run `python recalc.py model.xlsx 30` until `status: "success"`
- DCF + WACC sheets; sensitivity at DCF bottom
- all requested inputs sourced or `[UNSOURCED]`
- no hardcoded derived values, linear shortcuts, placeholders, or manual tables
- center sensitivity equals implied share price and is highlighted
- no #REF/#DIV/0/#VALUE/#NAME/#NULL/#NUM/#N/A errors

## Data Sources in Hermes

If structured financial-data MCP configured, prefer it for point-in-time comps,
precedent transactions, and filings; Hermes MCP support is documented in the
`native-mcp` skill. Otherwise use `web_search`/`web_extract` on SEC EDGAR
(`https://www.sec.gov/cgi-bin/browse-edgar`), company IR pages,
`browser_navigate` for interactive portals, or user data. Ask when missing.
Never fabricate; surface `[UNSOURCED]`.

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0).
Office-JS/Cowork live-Excel paths were removed; targets headless `openpyxl` via
`excel-author`. Original: https://github.com/anthropics/financial-services