---
name: comps-analysis
description: Build comparable-company valuation workbooks in Excel.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, valuation, comps, excel, openpyxl, modeling, investment-banking]
    related_skills: [excel-author, pptx-author, dcf-model, lbo-model]
---

# Comparable Company Analysis

role: institutional comparable-company operating/valuation analysis builder
do: choose peer group/period/units; source and cite data; ask format/audience/question/context; build formula-driven operating and valuation sections; calculate statistics; document methodology; sanity-check and audit workbook
inputs: xlsx/template/example; companies/tickers; raw financial/market data; industry/context; audience/key question; period/units; user formatting preferences
outputs: structured `.xlsx` comps analysis; operating metrics; valuation multiples; quartile/statistics blocks; notes/methodology; source comments/hyperlinks; warnings/red flags
¬: use web search as primary when structured MCP exists; hardcode derived metrics; duplicate raw inputs; copy example blindly; omit source comments; mix periods/units; include incomparable peers; fabricate/leave unsourced data undisclosed

Headless `openpyxl` produces the workbook. Follow `excel-author` conventions
for cell coloring, formulas, named ranges, and sensitivity tables; recalculate:

```bash
python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx
```

## When to Use

- compare peer operating performance, growth, margins, efficiency, or cash generation
- compare valuation multiples and quartile positioning
- create an investment-committee, board, M&A, sector-benchmark, or portfolio-monitoring workbook

## Data Source Priority

1. If S&P Kensho, FactSet, Daloopa, or another structured financial-data MCP is configured, use it exclusively for financial/trading information; do not web-search.
2. If no structured MCP is available, use Bloomberg Terminal, SEC EDGAR filings, company IR pages, or other institutional sources. In Hermes, access SEC through `web_search`/`web_extract` or use interactive data portals with `browser_navigate`.
3. User-provided data is valid when explicitly supplied; ask when required context is missing.
4. Never fabricate. If a multiple/filing number cannot be sourced, mark cell `[UNSOURCED]` and surface it to user.

## Intake and Context

Before building, ask:

1. preferred format or adapt template style?
2. audience: investment committee, board, quick reference, detailed memo?
3. key question: valuation, growth, competitive positioning, efficiency?
4. context: M&A, investment decision, sector benchmark, performance review?

User examples/preferences override defaults. `examples/comps_example.xlsx` teaches
structure, rigor, documentation, clear headers, transparent formulas, and audit
trails only; do not exactly reproduce its metrics/layout/style. Adapt to industry
(mega-cap tech vs emerging SaaS), sector metrics, company familiarity (less
background/more deltas for known peers), and decision type.

Core principle: build right structure first, let data tell story; target
institutional-quality analysis, not institutional-looking templates.

## Non-Negotiable Construction Rules

### Formulas and verification

- every derived margin, multiple, statistic is an Excel formula referencing input cells
- with `openpyxl`, `cell.value = "=E7/C7"` is correct; `cell.value = 0.687` is wrong
- hardcodes only raw inputs (revenue, EBITDA, share price, etc.); every hardcode gets source comment
- do not build end-to-end without checkpoints:
  1. show header layout before data
  2. show raw-input block and confirm sources/periods before formulas
  3. show operating-metric margins and sanity-check before valuation
  4. show multiples and confirm reasonable before statistics

### Default layout/style

User/template/team style overrides these defaults. Suggested font: Times New
Roman; 11pt data, 12pt headers; bold section headers/company names/stat labels.

Palette: dark blue + light blue + light grey + white only:

- section headers: dark blue `#1F4E79`/`#17365D`, white bold, full-row fill
- column headers: light blue `#D9E1F2`, black bold, centered
- data: white; black formulas, blue hardcoded inputs
- statistics: light grey `#F2F2F2`, black left-aligned labels

Formatting: percentages/margins one decimal (`12.3%`), multiples one decimal
(`13.5x`), dollar amounts no decimals with thousands separator (`69,632`), no
borders, centered metrics, uniform column widths/row heights. Add one blank row
between company data and statistics. Do not add `SECTOR STATISTICS` or
`VALUATION STATISTICS` header rows.

## Procedure

### 1. Define header/context block

```text
Row 1: [ANALYSIS TITLE] - COMPARABLE COMPANY ANALYSIS
Row 2: [List of Companies with Tickers] • [Company 1 (TICK1)] • [Company 2 (TICK2)] • [Company 3 (TICK3)]
Row 3: As of [Period] | All figures in [USD Millions/Billions] except per-share amounts and ratios
```

Header establishes companies, date, units, and interpretation immediately.

### 2. Build operating statistics

Start with:

1. Company
2. Revenue (LTM, quarterly, or annual per context)
3. Revenue Growth (YoY %)
4. Gross Profit
5. Gross Margin = GP/Revenue
6. EBITDA
7. EBITDA Margin = EBITDA/Revenue

Add only context-relevant metrics: quarterly/LTM for seasonality; FCF/FCF margin
for capital-intensive/SaaS; net income for mature companies; operating income;
CapEx; Rule of 40 for SaaS; FCF conversion for advanced earnings quality.

Formula examples (row 7):

```excel
// Core ratios - these are always calculated
Gross Margin (F7): =E7/C7
EBITDA Margin (H7): =G7/C7

// Optional ratios - include if relevant
FCF Margin: =[FCF]/[Revenue]
Net Margin: =[Net Income]/[Revenue]
Rule of 40: =[Growth %]+[FCF Margin %]
```

Golden rule: ratio = `[Something] / [Revenue]` or `[Something] / [Something
from this sheet]`; keep it simple.

After company rows, blank row, then statistics for comparable metrics:

```text
[Leave one blank row for visual separation]
- Maximum: =MAX(B7:B9)
- 75th Percentile: =QUARTILE(B7:B9,3)
- Median: =MEDIAN(B7:B9)
- 25th Percentile: =QUARTILE(B7:B9,1)
- Minimum: =MIN(B7:B9)
```

Statistics required for Revenue Growth %, Gross Margin %, EBITDA Margin %, EPS,
EV/Revenue, EV/EBITDA, P/E, Dividend Yield %, Beta. Do not apply them to size
metrics Revenue, EBITDA, Net Income, Market Cap, Enterprise Value. Quartiles show
distribution: 75th = premium, median = typical, 25th = discount.

### 3. Build valuation multiples

Core columns, same company order:

1. Company
2. Market Cap
3. Enterprise Value = Market Cap ± Net Debt/Cash
4. EV/Revenue
5. EV/EBITDA
6. P/E

Optional by context/data: FCF Yield, PEG, Price/Book, ROE/ROA, Revenue/EBITDA
CAGR, Asset Turnover, Debt/Equity. Include 3-5 meaningful core multiples, not
every possible metric.

```excel
// Core multiples - always include these
EV/Revenue: =[Enterprise Value]/[LTM Revenue]
EV/EBITDA: =[Enterprise Value]/[LTM EBITDA]
P/E Ratio: =[Market Cap]/[Net Income]

// Optional multiples - include if data available
FCF Yield: =[LTM FCF]/[Market Cap]
PEG Ratio: =[P/E]/[Growth Rate %]
```

Valuation must reference operating metrics; never input raw data twice. If
revenue is in C7, EV/Revenue references C7. Add same Max/75th/Median/25th/Min
statistics after one blank row; no separate valuation-statistics header.

### 4. Document notes and methodology

Required notes:

- data sources and quality: source, period (e.g. Q4 2024 audited), verification/cross-check; prefer MCP where available
- definitions: EBITDA, FCF = Operating CF - CapEx, Rule of 40/FCF conversion, LTM/CAGR periods
- valuation: EV = Market Cap + Net Debt, growth-rate basis, one-time/normalization adjustments
- analysis framework: investment thesis, key metrics, interpretation of quartiles

### 5. Choose metrics by question

| Question | Emphasize | Skip |
|---|---|---|
| undervalued? | EV/Revenue, EV/EBITDA, P/E, Market Cap | operational details/growth |
| most efficient? | Gross Margin, EBITDA Margin, FCF Margin, Asset Turnover | size/absolute dollars |
| growing fastest? | Revenue Growth %, EBITDA CAGR, user/customer growth | margins/leverage |
| best cash generator? | FCF, FCF Margin, FCF Conversion, CapEx intensity | EBITDA/P/E |

Industry guidance:

| Industry | Must have | Optional | Skip |
|---|---|---|---|
| Software/SaaS | Revenue Growth, Gross Margin, Rule of 40 | ARR, NDR, CAC Payback | Asset Turnover, Inventory |
| Manufacturing/Industrials | EBITDA Margin, Asset Turnover, CapEx/Revenue | ROA, Inventory Turns, Backlog | Rule of 40/SaaS |
| Financial Services | ROE, ROA, Efficiency Ratio, P/E | Net Interest Margin, Loan Loss Reserves | Gross Margin, EBITDA |
| Retail/E-commerce | Revenue Growth, Gross Margin, Inventory Turnover | Same-Store Sales, CAC | heavy R&D/CapEx |

5-10 rule: 5 operating metrics (Revenue, Growth, 2-3 margin/efficiency) + 5
valuation metrics (Market Cap, EV, 3 multiples) = enough story. More than 15 is
probably noise; edit ruthlessly.

### 6. Add comments and quality controls

Before: define comparable peer group (business model, scale, geography), period
(LTM smooths seasonality; quarterly shows trends), units, and source map.

During:

1. enter all raw data in blue first
2. add comments to every hardcoded input: exact source or assumption rationale, with hyperlinks when available
3. build formulas row-by-row; test each
4. use absolute references for headers (`$C$6`)
5. format percentages consistently; add conditional formatting for outliers

Comment examples:

- `Bloomberg Terminal - MSFT Equity DES, accessed 2024-10-02`
- `Q4 2024 10-K filing, page 42, line item 'Total Revenue'`
- `FactSet consensus estimate as of 2024-10-02`
- assumption: `Assumed 15% EBITDA margin based on peer median, company does not disclose`
- estimate: `Estimated Enterprise Value as Market Cap + $50M net debt (from Q3 balance sheet, Q4 not yet available)`
- forward P/E: `Forward P/E based on street consensus EPS of $3.45 (average of 12 analyst estimates)`

### 7. Sanity-check and audit

- Gross margin > EBITDA margin > Net margin
- typical (industry-dependent) EV/Revenue 0.5-20x, EV/EBITDA 8-25x, P/E 10-50x
- higher growth usually correlates with higher multiples
- larger companies may show scale-driven margin advantage
- do not mix Market Cap and EV; align numerator/denominator periods; do not hardcode formulas; cite every input; avoid too many/noncomparable/outdated companies; use median rather than incorrectly averaging percentages

### 8. Advanced/industry additions

Dynamic headers:

```text
Revenue Growth (YoY) % | EBITDA Margin | FCF Margin | Rule of 40
```

Quartiles answer whether target trades rich/cheap versus peers. Add only when
critical:

- Software/SaaS: ARR, NDR, CAC Payback, Rule of 40, FCF/gross margins >70%
- Healthcare: R&D/Revenue, pipeline value, regulatory status, reimbursement risk
- Industrials: backlog/order book, geographic mix, ROIC, asset turnover, cyclicality
- Consumer: same-store sales, CAC, brand value, inventory turns

### 9. Build workflow and formatting checklist

1. structure (~30m): headers, input/formula colors, units/date
2. data (~60-90m): MCP if available else Bloomberg/SEC, blue raw inputs, source notes
3. formulas (~30m): ratios → multiples → cross-checks
4. statistics (~15m): all metric ranges correct, quartile logic
5. QC (~30m): sanity, references, `#DIV/0!`/`#REF!`, benchmarks
6. documentation (~15m): notes, sources, methods, date stamp

Pro tips: save reusable templates; conditional-format >2 standard deviations;
hyperlink filings/data; version as `Comps_v1_2024-12-15`; obtain peer review.

Checklist (adapt to user/template):

- [ ] user font/style; section headers dark blue/white, column headers light blue/black, stats light grey
- [ ] no borders; uniform/even widths and consistent row heights (20-25pt typical)
- [ ] correct precision/thousands separators; all metrics centered
- [ ] one blank row before stats; no statistics header rows
- [ ] hardcode comments contain exact source or assumption explanation; relevant hyperlinks exist

### 10. Reference layout

```text
┌─────────────────────────────────────────────────────────────┐
│ TECHNOLOGY - COMPARABLE COMPANY ANALYSIS                    │
│ Microsoft • Alphabet • Amazon                               │
│ As of Q4 2024 | All figures in USD Millions                │
├─────────────────────────────────────────────────────────────┤
│ OPERATING METRICS                                           │
├──────────┬─────────┬─────────┬──────────┬──────────────────┤
│ Company  │ Revenue │ Growth  │ Gross    │ EBITDA  │ EBITDA │
│          │ (LTM)   │ (YoY)   │ Margin   │ (LTM)   │ Margin │
├──────────┼─────────┼─────────┼──────────┼─────────┼────────┤
│ MSFT     │ 261,400 │ 12.3%   │ 68.7%    │ 205,100 │ 78.4%  │
│ GOOGL    │ 349,800 │ 11.8%   │ 57.9%    │ 239,300 │ 68.4%  │
│ AMZN     │ 638,100 │ 10.5%   │ 47.3%    │ 152,600 │ 23.9%  │
│          │         │         │          │         │        │ [blank row]
│ Median   │ =MEDIAN │ =MEDIAN │ =MEDIAN  │ =MEDIAN │=MEDIAN │
│ 75th %   │ =QUART  │ =QUART  │ =QUART   │ =QUART  │=QUART  │
│ 25th %   │ =QUART  │ =QUART  │ =QUART   │ =QUART  │=QUART  │
├─────────────────────────────────────────────────────────────┤
│ VALUATION MULTIPLES                                         │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│ Company  │ Mkt Cap  │ EV       │ EV/Rev   │ EV/EBITDA │ P/E│
├──────────┼──────────┼──────────┼──────────┼───────────┼────┤
│ MSFT     │3,550,000 │3,530,000 │ 13.5x    │ 17.2x     │36.0│
│ GOOGL    │2,030,000 │1,960,000 │  5.6x    │  8.2x     │24.5│
│ AMZN     │2,226,000 │2,320,000 │  3.6x    │ 15.2x     │58.3│
│          │          │          │          │           │    │ [blank row]
│ Median   │ =MEDIAN  │ =MEDIAN  │ =MEDIAN  │ =MEDIAN   │=MED│
│ 75th %   │ =QUART   │ =QUART   │ =QUART   │ =QUART    │=QRT│
│ 25th %   │ =QUART   │ =QUART   │ =QUART   │ =QUART    │=QRT│
└──────────┴──────────┴──────────┴──────────┴───────────┴────┘
```

Add complexity only as needed: quarterly+LTM for seasonality, FCF for cash
story, sector metrics, or more statistic rows for >5 companies.

### 11. Red flags

Data: inconsistent periods, unexplained missing data, >10% source variance.
Valuation: negative EBITDA valued on EBITDA (use revenue), P/E >100x without
hypergrowth, industry-incoherent margins. Comparability: different fiscal year
ends, pure-play/conglomerate mix, materially different business models. When in
doubt exclude; 3 perfect comps beat 6 questionable ones.

## Formula Reference

```excel
// Statistical Functions
=AVERAGE(range)          // Simple mean
=MEDIAN(range)           // Middle value
=QUARTILE(range, 1)      // 25th percentile
=QUARTILE(range, 3)      // 75th percentile
=MAX(range)              // Maximum value
=MIN(range)              // Minimum value
=STDEV.P(range)          // Standard deviation

// Financial Calculations
=B7/C7                   // Simple ratio (Margin)
=SUM(B7:B9)/3            // Average of multiple companies
=IF(B7>0, C7/B7, "N/A")  // Conditional calculation
=IFERROR(C7/D7, 0)       // Handle divide by zero

// Cross-Sheet References
='Sheet1'!B7             // Reference another sheet
=VLOOKUP(A7, Table1, 2)  // Lookup from data table
=INDEX(MATCH())          // Advanced lookup

// Formatting
=TEXT(B7, "0.0%")        // Format as percentage
=TEXT(C7, "#,##0")       // Thousands separator
```

```excel
Gross Margin = Gross Profit / Revenue
EBITDA Margin = EBITDA / Revenue
FCF Margin = Free Cash Flow / Revenue
FCF Conversion = FCF / Operating Cash Flow
ROE = Net Income / Shareholders' Equity
ROA = Net Income / Total Assets
Asset Turnover = Revenue / Total Assets
Debt/Equity = Total Debt / Shareholders' Equity
```

## Delivery Checklist

- all companies truly comparable; periods consistent; units clearly labeled
- formulas reference cells, not hardcoded derived values
- every hardcoded input has exact source citation or assumption explanation; hyperlinks where relevant
- statistics include Max, 75th, Median, 25th, Min for comparable metrics
- notes document sources/methodology; date stamp says `As of [Date]`
- formatting follows input/formula conventions; sanity checks pass
- formula audit has no `#DIV/0!`, `#REF!`, or `#N/A`
- recalculate workbook with `excel-author` before delivery

## Continuous Improvement

After delivery ask: did statistics reveal unexpected insights? data gaps?
stakeholder-requested metrics? time spent versus target? what would improve next
iteration? Save templates, learn feedback, refine for actual decision use.

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0).
Office-JS/Cowork live-Excel paths were removed; this version targets headless
`openpyxl` via `excel-author`. Original:
https://github.com/anthropics/financial-services