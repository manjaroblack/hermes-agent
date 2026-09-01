---
name: solana
description: Query Solana wallets, tokens, txs, and NFTs in USD.
version: 0.2.0
author: Deniz Alagoz (gizdusum), enhanced by Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Solana, Blockchain, Crypto, Web3, RPC, DeFi, NFT]
    related_skills: []
---

# Solana Blockchain

role: read-only Solana/RPC portfolio operator
do: select command; verify RPC; query wallet/token/tx/activity/NFT/whale/stats/price; enrich USD; report rate limits/heuristics; verify response
inputs: wallet address, tx signature, token mint/symbol, whale threshold, RPC URL, limit/price flags
outputs: SOL/SPL balances and USD values, tx/activity/token/NFT/network/whale data
¬: sign/send transactions; claim historical whale scan; treat heuristic NFT list as complete; hide rate limits; expose private RPC key; claim stale public RPC data is live

Query Solana on-chain data enriched with USD pricing via CoinGecko. Eight commands: wallet portfolio, token info, transaction, activity, NFTs, whale detection, network stats, and price. Helper uses only Python stdlib (`urllib`, `json`, `argparse`); no key required.

## When to Use

- wallet balance/holdings/portfolio USD
- transaction signature details or recent address activity
- SPL metadata/price/supply/top holders
- NFT list, large SOL transfers, network health/TPS/epoch, token price

## Prerequisites

- Python standard library only
- default RPC `https://api.mainnet-beta.solana.com`; optional `SOLANA_RPC_URL` private endpoint
- CoinGecko free API, ~10-30 requests/min; `--no-prices` skips it
- helper: `~/.hermes/skills/blockchain/solana/scripts/solana_client.py`

## Quick Reference

```
python solana_client.py wallet   <address> [--limit N] [--all] [--no-prices]
python solana_client.py tx       <signature>
python solana_client.py token    <mint_address>
python solana_client.py activity <address> [--limit N]
python solana_client.py nft      <address>
python solana_client.py whales   [--min-sol N]
python solana_client.py stats
python solana_client.py price    <mint_or_symbol>
```

## Procedure

### 0. Connectivity

```bash
python --version

# Optional: set a private RPC for better rate limits
export SOLANA_RPC_URL="https://api.mainnet-beta.solana.com"

# Confirm connectivity
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

Use a private RPC (Helius, QuickNode, Triton) for production/rate limits; do not print private credentials.

### 1. Wallet portfolio

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  wallet 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Outputs SOL + USD, SPL tokens with price/value sorted by value, dust count, NFT summary, total USD. `--limit N` default 20; `--all` removes dust filter/limit; `--no-prices` RPC-only.

### 2. Transaction

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  tx 5j7s8K...your_signature_here
```

Shows slot, timestamp, fee, status, SOL/USD balance changes, and program invocations.

### 3. Token info

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Shows metadata, price, market cap, supply, decimals, mint/freeze authorities, top 5 holder percentages.

### 4. Activity

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  activity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM --limit 25
```

Default last 10; max 25.

### 5. NFTs

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  nft 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Heuristic: SPL amount=1 and decimals=0; compressed NFTs and Token-2022 NFTs are absent.

### 6. Whales

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  whales --min-sol 500
```

Scans latest block only—a point-in-time snapshot, not history.

### 7. Stats

```bash
# Should print current Solana slot, TPS, and SOL price
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

Shows current slot, epoch, TPS, supply, validator version, SOL price, market cap.

### 8. Price

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price BONK
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price JUP
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price SOL
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Known symbols: `SOL USDC USDT BONK JUP WETH JTO mSOL stSOL PYTH HNT RNDR WEN W TNSR DRIFT bSOL JLP WIF MEW BOME PENGU`.

## Pitfalls

- CoinGecko ~10-30 req/min; wallet many tokens may miss prices; `--no-prices` is faster
- public RPC rate-limits; set private `SOLANA_RPC_URL` for production
- NFT list is heuristic and incomplete
- whale scan latest block only; results vary by query moment
- public RPC history is ~2 days; older signatures may be unavailable
- only ~25 well-known tokens are named; others use abbreviated mints; `token` gives full info
- RPC/CoinGecko 429s retry up to 2 times with exponential backoff

## Verification

```bash
python ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

Expected current slot/TPS/SOL price; wallet/token/tx outputs should contain the requested address/signature and clearly label USD source/heuristics.
