---
name: evm
description: "Read-only EVM client: wallets, tokens, gas across 8 chains."
version: 1.0.0
author: Mibayy (@Mibayy), youssefea (@youssefea), ethernet8023 (@ethernet8023), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [EVM, Ethereum, BNB, BSC, Base, Arbitrum, Polygon, Optimism, Avalanche, zkSync, Blockchain, Crypto, Web3, DeFi, NFT, ENS, Whale, Security]
    category: blockchain
    related_skills: [solana]
    requires_toolsets: [terminal]
---

# EVM Blockchain Skill

role: read-only EVM data operator
do: select chain/command; run standard-library client; inspect wallet/token/tx/gas/contract data; report limits and risk flags
inputs: address, token/tx hash, ENS name, chain, query options; optional `EVM_RPC_URL`
outputs: USD-enriched JSON or human-readable wallet, market, transaction, gas, ENS, contract, allowance, whale data
¬: sign/send transactions; expose credentials; treat known-token scans as complete; treat L2 gas as full transaction cost; bypass input validation

Query EVM-compatible blockchain data across 8 chains with USD pricing. Fourteen commands cover wallet portfolio, token info, transactions, activity, gas, network stats, prices, multi-chain scans, whale detection, ENS, allowances, contract inspection, and decoding. No API key; Python standard library only (`urllib`, `json`, `argparse`, `threading`).

Supports Ethereum, BNB Chain (BSC), Base, Arbitrum One, Polygon, Optimism, Avalanche C-Chain, and zkSync Era. This skill supersedes standalone `base`; pass `--chain base` for Base coverage, including AERO, DEGEN, TOSHI, BRETT, WELL, cbETH, cbBTC, wstETH, and rETH.

## When to Use

- wallet balance/portfolio on an EVM chain or across all chains
- ERC-20 metadata, price, supply, or market cap
- transaction details, input decoding, or recent address activity
- current gas prices or cross-chain fee comparison
- large transfers, ENS forward/reverse lookup, dangerous allowances
- proxy/ERC-20/ERC-721/ERC-165 and bytecode inspection

## Prerequisites

- Python 3.8+ standard library; no pip install
- CoinGecko free API for pricing (~10-30 requests/min)
- ensideas.com public API for ENS
- 4byte.directory public API for transaction decoding
- optional RPC override: `export EVM_RPC_URL=https://your-rpc.com`
- helper: `~/.hermes/skills/blockchain/evm/scripts/evm_client.py`

## Quick Reference

```
SCRIPT=~/.hermes/skills/blockchain/evm/scripts/evm_client.py

# Network & prices
python $SCRIPT stats                            # Ethereum stats
python $SCRIPT stats --chain arbitrum           # Arbitrum stats
python $SCRIPT compare                          # Gas + prices ALL 8 chains

# Wallet
python $SCRIPT wallet 0xd8dA...96045            # Portfolio (ETH + ERC-20)
python $SCRIPT wallet 0xd8dA...96045 --chain bsc
python $SCRIPT multichain 0xd8dA...96045        # Same wallet on ALL chains

# Tokens & prices
python $SCRIPT price ETH
python $SCRIPT price 0xdAC1...1ec7              # By contract address
python $SCRIPT token 0xdAC1...1ec7              # ERC-20 metadata + market cap

# Transactions
python $SCRIPT tx 0x5c50...f060                 # Transaction details
python $SCRIPT decode 0x5c50...f060             # Decode input data (4byte.directory)
python $SCRIPT activity 0xd8dA...96045          # Recent transactions

# Gas
python $SCRIPT gas                              # Gas prices + cost estimates
python $SCRIPT gas --chain optimism

# Security
python $SCRIPT allowance 0xd8dA...96045         # Dangerous ERC-20 approvals
python $SCRIPT contract 0xdAC1...1ec7           # Contract inspection (proxy? standards?)

# ENS
python $SCRIPT ens vitalik.eth                  # Name -> address + profile
python $SCRIPT ens 0xd8dA...96045               # Address -> ENS name

# Whale detection
python $SCRIPT whale                            # Large transfers (last 20 blocks, >$10k)
python $SCRIPT whale --blocks 50 --min-usd 100000 --chain arbitrum
```

## Procedure

### 0. Setup

```bash
python --version   # 3.8+ required
python ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats
```

### 1. Portfolio and multi-chain scan

```bash
python $SCRIPT wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python $SCRIPT wallet 0xd8dA... --chain bsc --no-prices   # faster
```

`wallet` returns native balance + known ERC-20 tokens sorted by USD; `multichain` scans all 8 chains in parallel and adds a grand USD total.

```bash
python $SCRIPT multichain 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

```bash
python $SCRIPT compare
```

### 2. Tokens, transactions, and ENS

```bash
python $SCRIPT tx 0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060
python $SCRIPT decode 0x5c504ed...   # Shows human-readable function signature
```

Token output includes metadata/market cap; decode maps selectors such as `0xa9059cbb` to `transfer(address,uint256)`; ENS returns address/profile or reverse name.

```bash
python $SCRIPT ens vitalik.eth          # -> 0xd8dA... + avatar + social links
python $SCRIPT ens 0xd8dA...96045       # -> vitalik.eth
```

### 3. Security, contracts, whales, gas

```bash
python $SCRIPT contract 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48   # USDC (proxy)
python $SCRIPT contract 0xdAC17F958D2ee523a2206206994597C13D831ec7   # USDT (ERC-20)
```

`allowance` flags unlimited approvals to known DEX/bridge contracts as HIGH risk. `contract` detects EIP-1967/EIP-1167 proxies, ERC-20/721/165, bytecode size, and implementation address. `gas` shows gwei + USD estimates for transfer, ERC-20 transfer, approve, swap, NFT mint, and NFT transfer. `whale` defaults to last 20 blocks and >$10k.

```bash
python $SCRIPT allowance 0xYourWallet
```

```bash
python $SCRIPT whale                                    # ETH, last 20 blocks, >$10k
python $SCRIPT whale --blocks 50 --min-usd 50000 --chain bsc
```

```bash
python $SCRIPT gas
python $SCRIPT gas --chain polygon
```

## Supported Chains

| Key       | Name           | Native | Chain ID |
|-----------|----------------|--------|----------|
| ethereum  | Ethereum       | ETH    | 1        |
| bsc       | BNB Chain      | BNB    | 56       |
| base      | Base           | ETH    | 8453     |
| arbitrum  | Arbitrum One   | ETH    | 42161    |
| polygon   | Polygon        | POL    | 137      |
| optimism  | Optimism       | ETH    | 10       |
| avalanche | Avalanche C    | AVAX   | 43114    |
| zksync    | zkSync Era     | ETH    | 324      |

## Pitfalls

- CoinGecko free tier is ~10-30 req/min; use `--no-prices` for faster scans.
- Public RPCs throttle; use a private `EVM_RPC_URL` for production.
- `wallet`/`allowance` inspect only the known token list (~30/chain); use an explorer for full discovery.
- `activity` scans recent blocks only (max 200); full history needs Etherscan API.
- `multichain` starts 8 threads and can trigger rate limits.
- ENS uses one public endpoint (`ensideas.com` / `ens.vitalik.ca`) with no fallback.
- Decode uses 4byte.directory with no fallback; unknown selectors remain `unknown`.
- L2 `gas` is L2 execution only; rollups also charge an L1 data-posting fee. Base's fee oracle is `0x420000000000000000000000000000000000000F`.
- Address/tx inputs require `0x` + length + hex; EIP-55 checksum casing is not enforced.

## Verification

```bash
# Should print current block, gas price, ETH price
python ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats

# Should resolve vitalik.eth to 0xd8dA...
python ~/.hermes/skills/blockchain/evm/scripts/evm_client.py ens vitalik.eth
```

Expected: current block/gas/ETH price, then a resolution of `vitalik.eth` to `0xd8dA...`.
