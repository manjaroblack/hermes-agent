---
name: mpp-agent
description: Pay HTTP 402 APIs via Machine Payments Protocol (MPP).
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Payments, MPP, HTTP-402, Tempo, Stripe]
    related_skills: [stripe-link-cli, stripe-projects]
---

# MPP Agent

role: Machine Payments Protocol client operator
do: identify 402 challenge; choose funded client; onboard/login; pay GET/POST; inspect receipt; preserve wallet secrecy; route server-side work elsewhere
inputs: merchant URL; 402 `www-authenticate`; wallet/client preference; request method/body; optional provider onboarding
outputs: paid merchant response; receipt evidence; client/account status; unsupported-method explanation
¬: pay without user intent; expose wallet keys; confuse server integration with client payment; force Stripe on non-Stripe challenge; retry dead auth forever

Wrap npm MPP clients so Hermes can pay per-request APIs that answer
`HTTP 402 Payment Required`. MPP: https://mpp.dev. Payments tooling is gated
`[linux, macos]` while the cluster matures on Windows.

## When to Use

- merchant API returns `HTTP 402` with `www-authenticate` and user wants payment
- user asks for pay-per-request, agent wallet, Tempo, Privy, AgentCash, or MPP service discovery
- Stripe Link spend produced a Shared Payment Token (SPT) for a 402 challenge; prefer `link-cli mpp pay` via `stripe-link-cli`

## Client Selection

| Tool | When | Setup |
|---|---|---|
| `link-cli` | Stripe Link exists or challenge advertises `method="stripe"` | `stripe-link-cli` |
| Tempo Wallet | MPP services, spend controls, discovery | `tempo wallet login` |
| Privy Agent CLI | Multi-chain wallet, browser funding | `privy-agent-wallets login` |
| AgentCash | 300+ pre-priced APIs via USDC.e balance | `npx agentcash onboard` |
| `mppx` | development/debugging, smallest dependency surface | `npm install -g mppx`, then `mppx account create` |

Default: Stripe Link or `method="stripe"` → `link-cli mpp pay`; otherwise
`mppx` for one-off calls/debugging, Tempo Wallet for persistent spend controls.

## Prerequisites

- Node.js 20+ on `PATH`
- funded Tempo/Privy/AgentCash wallet or `mppx` account
- provider onboarding when selected: https://tempo.xyz/SKILL.md,
  https://agents.privy.io/skill.md, https://agentcash.dev/skill.md

Fetch a chosen onboarding skill with `web_extract`; do not invent its commands.

## Procedure: mppx

Run all commands through `terminal`.

### 1. Install and create account

```
npm install -g mppx
mppx account create
```

Store credentials where the CLI directs; never paste them into the agent
transcript.

### 2. Inspect the 402 challenge

```bash
curl -i <url>
```

Expected MPP shape:

```
HTTP/1.1 402 Payment Required
www-authenticate: tempo amount=0.1 currency=...
```

Select a client from the challenge method and the user's funded wallet.

### 3. Pay

```
mppx <url>
```

Non-GET/body:

```
mppx <url> --method POST --data '<json>'
```

`mppx` handles challenge/credential exchange and prints the merchant response
on success.

### 4. Verify receipt

MPP attaches receipt header automatically:

```
mppx <url> -v
```

## Procedure: Tempo Wallet

Canonical skill: https://tempo.xyz/SKILL.md. Fetch it with `web_extract` and
follow current instructions. Headline commands:

```
tempo wallet login
tempo wallet pay <url>
```

Spend controls/service discovery: https://wallet.tempo.xyz.

## Pitfalls

- `HTTP 402` without `method="stripe"` cannot use Stripe Link; use matching `mppx`/wallet. With `method="stripe"`, prefer Link so approved card spend is used.
- Multiple `www-authenticate` methods (e.g. `tempo, stripe`) are valid; `mpp decode` picks Stripe and `mppx` picks Tempo. Choose the funded wallet.
- Zero-amount challenges may require proof only; no funded wallet needed.
- Wallet keys stay in each client config or Privy ephemeral keypair; never expose them through a command or file tool.
- Server-side MPP is a separate task: use https://mpp.dev/quickstart/server and `mppx/nextjs`, `mppx/hono`, `mppx/express`, or `mppx/elysia` middleware; this skill is client-only.

## Verification

```
mppx --version && mppx account list
```

Exit code 0 means `mppx` is installed and an account exists. For a payment,
also require the expected HTTP response and receipt, without exposing wallet
credentials.