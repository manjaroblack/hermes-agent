---
name: merger-model
description: Build M&A accretion/dilution workbooks in Excel.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, m-and-a, merger, accretion-dilution, excel, openpyxl, modeling, investment-banking]
    related_skills: [excel-author, pptx-author, dcf-model, 3-statement-model]
---

role: M&A accretion/dilution and purchase-price-analysis workbook builder
do: gather acquirer/target/deal inputs; calculate purchase price, Sources & Uses, pro forma EPS, synergies, PPA, breakeven, sensitivities; present GAAP/adjusted consequences; recalculate workbook
inputs: company/share/EPS/PE/debt/tax/cash; target earnings/EV/equity value; offer/premium; cash-stock mix; new debt/equity; synergies/phase-in; fees; close date; source data
outputs: `.xlsx` with assumptions, Sources & Uses, pro forma income statement, accretion/dilution summary, sensitivities, breakeven analysis; one-page merger-consequences pitch summary
¬: omit purchase-price or PPA effects; use only one EPS view where relevant; ignore foregone cash interest/new debt interest; assume full run-rate synergies in Year 1; fabricate financial data; deliver un-recalculated formulas

Headless `openpyxl` produces the workbook. Follow `excel-author` conventions for
formulas, colors, comments, named ranges, formatting, and recalculation.

## When to Use

- evaluate a potential acquisition
- prepare merger consequences for a pitch
- advise on offer terms, consideration mix, synergies, or EPS impact

## Procedure

### 1. Gather inputs

Acquirer:

- company name, current share price, shares outstanding
- LTM/NTM EPS (GAAP and adjusted)
- P/E multiple
- pre-tax cost of debt, tax rate
- cash on balance sheet, existing debt

Target:

- company name, current share price, shares outstanding (if public)
- LTM/NTM EPS or net income
- enterprise value or equity value

Deal terms:

- offer price/share or premium to current
- consideration mix (% cash / % stock)
- new debt raised for cash portion
- expected revenue/cost synergies and phase-in timeline
- transaction fees and financing costs
- expected close date

### 2. Purchase Price Analysis

```text
Offer price per share
Premium to current
Equity value
Plus: net debt assumed
Enterprise value
EV / EBITDA implied
P/E implied
```

### 3. Sources & Uses

```text
Sources                         Uses
New debt                        Equity purchase price
Cash on hand                    Refinance target debt
New equity issued               Transaction fees
                                Financing fees
Total                           Total
```

Balance Sources = Uses and identify any plug.

### 4. Pro Forma EPS (Years 1-3)

Build year-by-year:

```text
                                  Standalone   Pro Forma   Accretion/(Dilution)
Acquirer net income
Target net income
Synergies (after tax)
Foregone interest on cash (after tax)
New debt interest (after tax)
Intangible amortization (after tax)
Pro forma net income
Pro forma shares
Pro forma EPS
Accretion / (Dilution) %
```

### 5. Sensitivities

Accretion/dilution vs synergies and offer premium:

```text
                         $0M syn  $25M syn  $50M syn  $75M syn  $100M syn
15% premium
20% premium
25% premium
30% premium
```

Accretion/dilution vs cash/stock mix:

```text
             100% cash  75/25  50/50  25/75  100% stock
Year 1
Year 2
```

Use explicit formula grids, not hardcoded outputs or Excel Data Tables where
openpyxl cannot preserve their behavior. Keep scenario headers and model links
auditable.

### 6. Breakeven Synergies

Calculate minimum synergies needed for EPS-neutral Year 1.

### 7. Output

Workbook includes:

- Assumptions tab
- Sources & Uses
- pro forma income statement
- accretion/dilution summary
- sensitivity tables
- breakeven analysis

Also provide a one-page merger-consequences summary for a pitch book.

## Mandatory Deal Considerations

- show GAAP and adjusted (cash) EPS where relevant
- stock deal: use acquirer current price for exchange ratio; show dilution from new shares
- include purchase price allocation; goodwill and intangible amortization affect GAAP EPS
- model synergy phase-in; Year 1 often only 25-50% of run-rate synergies
- include foregone interest income on cash used and new interest expense on debt raised
- apply acquirer marginal tax rate to synergies and interest adjustments

## Pitfalls

- purchase price without net debt, transaction fees, or PPA understates deal cost
- stock consideration without exchange-ratio/new-share dilution overstates EPS
- one EPS view can hide GAAP intangible amortization or adjusted cash economics
- full run-rate Year 1 synergies, omitted taxes, or omitted financing effects overstate accretion
- hardcoded sensitivity outputs conceal broken premium/synergy/mix linkages

## Verification

- [ ] acquirer, target, and transaction inputs sourced or marked `[UNSOURCED]`
- [ ] purchase price, EV, premium, and multiples reconcile
- [ ] Sources = Uses
- [ ] GAAP/adjusted EPS treatment explicit
- [ ] cash/stock share count and exchange ratio correct
- [ ] synergy phase-in, taxes, foregone interest, debt interest, PPA amortization included
- [ ] Year 1 breakeven synergy formula works
- [ ] sensitivity cells vary with premium/synergy/mix assumptions
- [ ] formulas recalculate with zero errors before delivery

## Data Sources — MCP First, Web Fallback

If configured, structured financial-data MCPs (Daloopa etc.) are preferred for
point-in-time comps, precedents, and filings; Hermes MCP support is documented
in the `native-mcp` skill. Otherwise use `web_search` / `web_extract` with SEC
EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`), company IR pages,
`browser_navigate`, or user data. Ask when absent; never fabricate and flag
unavailable values `[UNSOURCED]`.

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0).
Office-JS/Cowork paths removed; targets headless openpyxl through `excel-author`.
Original: https://github.com/anthropics/financial-services