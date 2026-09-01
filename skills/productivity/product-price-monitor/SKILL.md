---
name: product-price-monitor
description: Watch product, flight, or listing prices; alert on target.
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Prices, Availability, Shopping, Travel, Alerts]
    related_skills: [maps]
---

# Product Price Monitor

role: normalized offer/availability watcher
do: pin exact item; define alert; fetch foreground baseline; schedule; refetch/normalize; compare state; suppress duplicates; notify qualifying changes
inputs: source URL/provider/ID, variant/quantity/location/dates/travelers, price/availability condition, currency/fees, cadence, destination
outputs: state file, cron job, deterministic alert/silence, source/timestamp evidence
¬: one-off current-price lookup (use `web_search`/`web_extract`); confuse variants; compare base to all-in; replace good state with errors; poll against site terms; claim inventory reserved

Setup runs foreground once; recurring check is a cron tick. The `price-watch`
automation blueprint scaffolds the job.

## When to Use

- alert laptop under $1,000
- watch flights under $500
- notify refundable hotel room
- track ticket/listing availability
- execute existing watch on cron tick

## Procedure — Setup (foreground, once)

### 1. Pin item

Record source/provider, product/listing ID, variant, quantity, location, dates,
travelers/guests, membership/login assumptions, condition, seller, substitutes.
Two variants must not be confusable.
Done when: source, exact variant, quantity, and location/date assumptions are pinned.

### 2. Define condition

Specify currency, all-in vs pre-tax, max price, stock/availability, shipping,
taxes, refundability, cabin/room/ticket class, cooldown, destination. Synthetic
examples must yield deterministic decisions.
Done when: threshold, currency, all-in rule, availability, and cadence are explicit.

### 3. Baseline then schedule

Fetch via `web_extract` or `browser_navigate`; record retrieval time, source
price, fees/taxes, availability, and terms. Do not schedule until one foreground fetch works.
Write contract under `~/.hermes/price-watches/<watch-slug>.json`, then create:

```
cronjob(action="create",
        schedule="every 6h",
        prompt="Load the product-price-monitor skill and run the tick for the watch contract at ~/.hermes/price-watches/<watch-slug>.json.",
        deliver=<user's destination>)
```

Cadence must respect rate limits/site terms. Baseline must match exact contract;
job must exist.
Done when: contract is saved, baseline succeeds, and the scheduled job is present.

## Procedure — Tick (each scheduled run)

### 4. Fetch + normalize

Refetch. Convert currency only with timestamped rate and retain source currency.
Separate base, mandatory fees, shipping/taxes, total, availability; exclude
volatile metadata. Failed fetch = unknown: report/skip; never overwrite the last good observation with an error page.
Done when: failed fetches remain unknown and last-good state is intact.

### 5. Compare + dedupe

Alert on threshold entry, qualifying availability, material lower price, or
requested recovery. Store last good observation + alert fingerprint. Replay of
same offer sends no second alert; honor cooldown.
Done when: fingerprint, cooldown, threshold decision, and last-good state are updated.

### 6. Deliver or stay silent

Alert includes exact item/variant, all-in price + source currency,
availability/terms, threshold, retrieval timestamp, source link, uncertainty.
Never claim reservation. If no qualify, stay silent unless all-clear requested.
Update state file.
Done when: alert/silence decision includes exact offer, terms, timestamp, and link.

## Pitfalls

- base fare vs all-in threshold
- wrong size/seller/cabin/dates/room terms
- error page replacing last-known-good
- aggressive polling or terms violation
- scheduling before foreground success

## Verification

- [ ] Contract pins item/variant.
- [ ] Foreground fetch succeeded before job.
- [ ] State replay gives deterministic decision; duplicate alert suppressed.
- [ ] Failed fetch preserves last-known-good.
- [ ] Alert has all-in price, source currency, timestamp, source link.