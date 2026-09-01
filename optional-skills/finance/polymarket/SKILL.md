---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
license: MIT
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [polymarket, prediction-markets, market-data, trading]
    related_skills: []
---

role: read-only Polymarket prediction-market data analyst
do: search/discover events; parse nested markets; present prices as probabilities and volume; deep-dive orderbooks/history; monitor movements when requested
inputs: market/event query; optional `clobTokenIds`/`conditionId`; desired depth/time range
outputs: market question; Yes/No percentages; volume; orderbook/history/trade data as requested
¬: place trades; require authentication for public REST reads; call prices certainty; omit market question/probability; fabricate unavailable price history

# Polymarket — Prediction Market Data

Query Polymarket public REST APIs. Endpoints are read-only and require zero
authentication. Full endpoint reference/curl examples:
`references/api-endpoints.md`.

## When to Use

- prediction markets, betting odds, event probabilities, or Polymarket
- market prices, orderbook data, price history, or movement monitoring

## Concepts

- Events contain one or more Markets (1:many)
- Markets are binary Yes/No outcomes; prices range 0.00-1.00 and represent probabilities
- `outcomePrices`: JSON-encoded array such as `["0.80", "0.20"]`
- `clobTokenIds`: JSON-encoded `[Yes, No]` token IDs for price/orderbook queries
- `conditionId`: hex string for price-history queries
- volume is USDC (US dollars)

## APIs

1. Gamma: `gamma-api.polymarket.com` — discovery, search, browsing
2. CLOB: `clob.polymarket.com` — real-time prices, orderbooks, history
3. Data: `data-api.polymarket.com` — trades, open interest

## Procedure

1. search Gamma `public-search` with user query
2. parse response; extract events and nested markets
3. present market question, current prices as percentages, volume
4. if requested, use `clobTokenIds` for orderbook and `conditionId` for history

Present `outcomePrices ["0.652", "0.348"]` as `Yes: 65.2%, No: 34.8%`; always
include market question/probability and available volume, e.g.
`"Will X happen?" — 65.2% Yes ($1.2M volume)`.

### Double-encoded fields

Gamma returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON. In Python:

```python
json.loads(market["outcomePrices"])
```

## Rate Limits

- Gamma: 4,000 requests / 10 seconds (general)
- CLOB: 9,000 requests / 10 seconds (general)
- Data: 1,000 requests / 10 seconds (general)

## Limitations and Verification

- read-only; trading requires wallet crypto authentication/EIP-712 signatures
- new markets may have empty price history
- geographic restrictions apply to trading; read-only data is globally accessible
- report API/source context and query time when monitoring or comparing movement