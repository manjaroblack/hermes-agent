---
name: stripe-link-cli
description: Agent payments via Stripe Link — cards, SPT, approvals.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Payments, Stripe, Link, Checkout, MPP]
    related_skills: [mpp-agent, stripe-projects]
---

# Stripe Link CLI

role: Stripe Link payment/Shared Payment Token operator
do: install; authenticate; classify merchant challenge; list payment/shipping; confirm total; request approval; retrieve credential to protected file; use; delete; verify
inputs: checkout or MPP URL; merchant/name/context; amount in cents; line item/total; payment method/shipping choice; user approval
outputs: approved one-time card or SPT; completed checkout/MPP response; redacted status; cleanup evidence
¬: approve spend; surprise user with total; print PAN; read card file into context; use `card` for unsupported 402; proceed before auth; retry non-US failure

Wraps [@stripe/link-cli](https://github.com/stripe/link-cli) for one-time virtual
cards or Shared Payment Tokens (SPT). Every spend requires approval in the Link
mobile/web app; Hermes cannot self-approve. US-only and gated `[linux, macos]`;
upstream CLI does not support Windows.

## When to Use

- buy/pay/checkout request
- get a card or payment method
- Link login/wallet connection
- merchant API returns HTTP 402 with `www-authenticate: ... method="stripe"`

For a paid API with HTTP 402 and no checkout form, use this skill's SPT path or
`mpp-agent`; do not take the card path.

## Prerequisites

- Node.js 20+ on `PATH`: `node --version`
- US-based Link account

First run can guide setup; no prior Link state required:

- Link account: https://app.link.com
- payment method: https://app.link.com/wallet
- Link mobile/web app for first spend approval

No env vars; CLI stores auth locally in its own config directory.

## Procedure

### 1. Install and inspect CLI

```text
npm install -g @stripe/link-cli
```

Ad hoc alternative: `npx @stripe/link-cli`. Installed commands use `link-cli`.
Non-TTY output defaults to compact `toon`; use `--format json` when parsing.
Discover commands with `link-cli --llms-full`; inspect a command schema with
`link-cli <command> --schema`.

### 2. Authenticate

```
link-cli auth status
```

If unauthenticated:

```
link-cli auth login --client-name "Hermes" --interval 5 --timeout 300
```

Show verification URL/phrase and wait. Inline `--interval`/`--timeout` avoids
agent-managed `_next`. Do not proceed until `auth status` confirms login.

### 3. Classify merchant credential

| Merchant surface | `--credential-type` |
|---|---|
| Standard web checkout form / Stripe Elements | `card` (default) |
| Returns HTTP 402 with `method="stripe"` in `www-authenticate` | `shared_payment_token` |
| Returns HTTP 402 without `method="stripe"` | unsupported — stop |

For 402, pass raw header to validate and decode network ID/request body:

```
link-cli mpp decode --challenge '<full WWW-Authenticate header>'
```

### 4. List methods and shipping

```
link-cli payment-methods list
link-cli shipping-address list
```

Use first entry unless user selects another. Payment-method `id` becomes
`--payment-method-id`.

### 5. Confirm and create spend request

Confirm final total with user before issuing; amounts are cents:

```
link-cli spend-request create \
  --payment-method-id <pm_id> \
  --merchant-name "<name>" \
  --merchant-url "<url>" \
  --context "<one sentence: what is being purchased and why>" \
  --amount <cents> \
  --line-item "name:<item>,unit_amount:<cents>,quantity:1" \
  --total "type:total,display_text:Total,amount:<cents>" \
  --request-approval
```

MPP merchant: add `--credential-type shared_payment_token`.
`--request-approval` pings Link app and polls until approve/deny; deny/timeout
exits non-zero.

### 6. Retrieve credential securely

Never print card details. Use protected output file:

```
link-cli spend-request retrieve <lsrq_id> \
  --include card \
  --output-file /tmp/link-card.json \
  --format json
```

CLI writes `0600`; stdout contains only redacted brand/last4/expiry and
`card_output_file`.

### 7. Use credential

- all commands run through the `terminal` tool; web checkout: hand path to user or
  browser tool; never use `read_file` to load the card file into agent context
- MPP:

  ```
  link-cli mpp pay <merchant-url> \
    --spend-request-id <lsrq_id> \
    --method POST \
    --data '<json body>'
  ```

### 8. Delete immediately

```
rm -f /tmp/link-card.json
```

## Optional MCP mode

`@stripe/link-cli --mcp` exposes equivalent stdio MCP tools:

```
hermes mcp add stripe-link --command "npx" --args "@stripe/link-cli --mcp"
```

`hermes mcp list` should show `stripe-link`; Link app approval remains mandatory.

## Pitfalls

- US-only; outside US `auth login` fails; inform user and stop retrying.
- Card PAN must never enter agent context; always use `--output-file`. If already retrieved without it, logout alone is not enough; one-time card/rotation hygiene still matters.
- `--request-approval` blocks until user acts and can timeout.
- Some commands return `_next.command`; prefer inline polling flags.
- Non-TTY defaults to `toon`; use `--format json` for fields.
- Do not default to `card`; classify merchant first to avoid silent failure/data overreach.

## Verification

```
link-cli --version && link-cli auth status
```

Exit code 0 means installed and logged in. For a spend, additionally verify
approval, expected checkout/MPP result, redacted-only output, and card-file
deletion.