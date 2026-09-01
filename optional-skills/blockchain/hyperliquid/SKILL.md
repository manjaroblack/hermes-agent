---
name: hyperliquid
description: Hyperliquid market data, account history, trade review.
version: 0.1.0
author: Hugo Sequier (Hugo-SEQUIER), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Hyperliquid, Blockchain, Crypto, Trading, Perpetuals, Spot, DeFi]
    related_skills: []
---

# Hyperliquid Skill

role: read-only Hyperliquid market/account analyst
do: select info command; query public endpoint; normalize/export data; review fills with context; state heuristic limits
inputs: perp/spot query, coin, optional address, time window, DEX, output path; optional `HYPERLIQUID_*` defaults
outputs: market/order-book/account data, trade review, normalized JSON dataset
¬: sign, place, cancel, or modify orders; imply complete history; treat heuristic review as intent/slippage reconstruction; leak user address

Query Hyperliquid's public `/info` endpoint. No API key, signing, or order placement. Twelve commands: `dexs`, `markets`, `spots`, `candles`, `funding`, `l2`, `state`, `spot-balances`, `fills`, `orders`, `review`, `export`; stdlib only (`urllib`, `json`, `argparse`).

## When to Use

- perp/spot markets, candles, funding, L2 book, HIP-3 or builder-deployed DEXs
- wallet positions, spot balances, fills, or orders
- post-trade review combining fills and market context
- normalized candle+funding JSON for backtesting preparation

## Prerequisites

- Python standard library; no package/API key
- optional `${HERMES_HOME:-~/.hermes}/.env` values:
  - `HYPERLIQUID_API_URL` → `https://api.hyperliquid.xyz`; testnet=`https://api.hyperliquid-testnet.xyz`
  - `HYPERLIQUID_USER_ADDRESS` → default for `state`, `spot-balances`, `fills`, `orders`, `review`
- project `.env` is a development fallback
- helper: `~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py`

## Procedure

Run through `terminal`:

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py <command> [args]
```

Add `--json` to any command.

### Discovery

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py dexs

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 15 --sort volume

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spots --limit 15
```

`--dex` applies to perp endpoints; spot aliases can be `PURR/USDC` or `@107`; HIP-3 coins look like `mydex:BTC`.

### Market history and book

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  candles BTC --interval 1h --hours 72 --limit 48

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  funding BTC --hours 168 --limit 30
```

Time-range endpoints paginate; repeat with later `startTime` or use `export` for larger windows. `l2` is a point-in-time depth snapshot.

### Account and trade review

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py state 0xabc...
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py spot-balances
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py fills 0xabc... --hours 72 --limit 25
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py orders --limit 25
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py review 0xabc... --hours 72 --fills 50
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py review --coin BTC --hours 168
```

`state` returns perp positions; `spot-balances` spot inventory. `review` reports realized PnL, fees, wins/losses, coin breakdown, market trend, average funding, and heuristics (fee drag, concentration, counter-trend losses). For deeper analysis: `review` → identify problem coin/window → `fills`/`orders` → `candles`/`funding` → judge decisions separately from outcomes.

### Dataset export

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  state 0xabc...

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spot-balances
```

Output: schema version, source metadata, exact time window, normalized candle/funding rows, summary stats. Use `--end-time-ms` for reproducibility.

## Quick Reference

```bash
hyperliquid_client.py dexs
hyperliquid_client.py markets [--dex DEX] [--limit N] [--sort volume|oi|funding_abs|change_abs|name]
hyperliquid_client.py spots [--limit N]
hyperliquid_client.py candles <coin> [--interval 1h] [--hours 24] [--limit N]
hyperliquid_client.py funding <coin> [--hours 72] [--limit N]
hyperliquid_client.py l2 <coin> [--levels N]
hyperliquid_client.py state [address] [--dex DEX]
hyperliquid_client.py spot-balances [address] [--limit N]
hyperliquid_client.py fills [address] [--hours N] [--limit N] [--aggregate-by-time]
hyperliquid_client.py orders [address] [--limit N]
hyperliquid_client.py review [address] [--coin COIN] [--hours N] [--fills N]
hyperliquid_client.py export <coin> [--interval 1h] [--hours N] [--output PATH]
```

Addresses are optional for account commands when `HYPERLIQUID_USER_ADDRESS` is set.

## Pitfalls

- Public info endpoints are rate-limited and may cap historical windows; paginate.
- `fills --hours` uses `userFillsByTime`, a recent rolling window, not a full archive.
- `historicalOrders` is recent only.
- `review` is heuristic; fills cannot reveal intent, placement quality, or true slippage.
- `export` is a normalized dataset, not a backtest engine; add a slippage/fill model.
- `@107` and similar spot aliases are valid identifiers.

## Verification

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  l2 BTC --levels 10
```

Expected: top Hyperliquid perp markets by 24h notional volume.

## Preserved Source Examples

### Original example 1

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  fills 0xabc... --hours 72 --limit 25

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  orders --limit 25
```

### Original example 2

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review 0xabc... --hours 72 --fills 50

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review --coin BTC --hours 168
```

### Original example 3

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 1h --hours 168 --output ./btc-1h-7d.json

python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 15m --hours 72 --end-time-ms 1760000000000
```

### Original example 4

```bash
python ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 5
```
