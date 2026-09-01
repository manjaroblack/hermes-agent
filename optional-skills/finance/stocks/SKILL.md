---
name: stocks
description: Stock quotes, history, search, compare, crypto via Yahoo.
version: 0.1.0
author: Mibay (Mibayy), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Stocks, Finance, Market, Crypto, Investing]
    category: finance
    related_skills: [dcf-model, comps-analysis, lbo-model]
---

# Stocks

role: read-only Yahoo Finance market-data operator
do: quote; search tickers; fetch OHLCV history; compare symbols; query crypto; report source/rate-limit caveats
inputs: ticker(s) or company query; history range; optional `ALPHA_VANTAGE_KEY`
outputs: JSON quote/history/search/compare/crypto data
¬: place orders; access accounts; treat unofficial Yahoo API as stable; expose credentials; imply financial advice

Read-only market data via Yahoo Finance. Five commands: `quote`, `search`,
`history`, `compare`, `crypto`. Python stdlib only — no API key, no pip
installs. Yahoo's endpoint is unofficial and may rate-limit or change.

## When to Use

- current stock price (`AAPL`, `TSLA`, `MSFT`, ...)
- ticker lookup by company name
- OHLCV history or performance over a date range
- side-by-side comparison of several tickers
- crypto price (`BTC`, `ETH`, `SOL`, ...)

## Prerequisites

- Python 3.8+ stdlib only
- optional `ALPHA_VANTAGE_KEY` enriches `market_cap`, `pe_ratio`, and 52-week levels when Yahoo crumb-protected fields are null
- free key: https://www.alphavantage.co/support/#api-key

## Procedure

Invoke through the `terminal` tool. Installed helper:

```
SCRIPT=~/.hermes/skills/finance/stocks/scripts/stocks_client.py
python $SCRIPT quote AAPL
```

All output is JSON on stdout. Use `jq` only when slicing output.

### Quick Reference

```
python $SCRIPT quote AAPL
python $SCRIPT quote AAPL MSFT GOOGL TSLA
python $SCRIPT search "Tesla"
python $SCRIPT history NVDA --range 6mo
python $SCRIPT compare AAPL MSFT GOOGL
python $SCRIPT crypto BTC ETH SOL
```

### Commands

- `quote SYMBOL [SYMBOL2 ...]` → current price, change, change%, volume, 52-week high/low
- `search QUERY` → top 5 ticker results: symbol, name, exchange, type
- `history SYMBOL [--range RANGE]` → daily OHLCV plus min, max, average, total-return percentage; ranges `1mo`, `3mo`, `6mo`, `1y`, `5y`; default `1mo`
- `compare SYMBOL1 SYMBOL2 [...]` → price, change%, 52-week performance side by side
- `crypto SYMBOL [SYMBOL2 ...]` → crypto prices; `BTC` becomes `BTC-USD` automatically

## Pitfalls

- Yahoo Finance API unofficial; endpoints can change or rate-limit without notice.
- `market_cap` and `pe_ratio` may be null when Yahoo crumb session is absent; use `ALPHA_VANTAGE_KEY` to backfill.
- Add a small delay between bulk requests to reduce rate limiting.
- Read-only only: no order placement or account integration.

## Verification

```
python ~/.hermes/skills/finance/stocks/scripts/stocks_client.py quote AAPL
```

Confirm exit success, JSON object `symbol: "AAPL"`, and numeric `price`.