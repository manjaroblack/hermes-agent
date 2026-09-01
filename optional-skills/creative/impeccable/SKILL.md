---
name: impeccable
description: Frontend design guidance, upstream-maintained (impeccable).
version: 4.1.2
author: Paul Bakaus (pbakaus)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, frontend, ui, ux, web-design, anti-slop]
    category: creative
    related_skills: [claude-design, popular-web-designs]
    upstream:
      repo: pbakaus/impeccable
      path: .hermes/skills/impeccable
---

# Impeccable (upstream-maintained)

role: upstream Impeccable catalog router
do: install current Hermes-native bundle; read docs; start `/impeccable init`; run detector
inputs: frontend brief/repo; design review or command request
outputs: installed skill bundle; anti-pattern guidance; detector findings
¬: treat this directory as vendored skill content; use a stale local copy; invent hosted plumbing

> **Catalog stub.** This entry is maintained upstream at
> [pbakaus/impeccable](https://github.com/pbakaus/impeccable): the project
> ships and verifies a Hermes-native skill bundle under `.hermes/skills/`.
> `hermes skills install impeccable` pulls the current bundle live from that
> repo (quarantined and scanned like any hub install) — this directory holds
> only the catalog metadata, so the vendored copy can never go stale.

## When to Use

- frontend design guidance, anti-pattern review, or an Impeccable command
- detector checks without an LLM or API key

Impeccable is a design language for AI coding agents: one skill exposing 23
sub-commands (`/impeccable init`, `craft`, `shape`, `critique`, `audit`,
`polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `animate`,
`colorize`, `typeset`, `layout`, `delight`, `overdrive`, `clarify`, `adapt`,
`optimize`, `extract`, `document`, `live`); anti-pattern guidance covers
overused fonts, purple gradients, nested cards, and bounce easing; the
61-rule deterministic detector CLI (`npx impeccable detect`) needs no LLM or API key.

After install, start with:

```
/impeccable init
```

Full documentation: https://impeccable.style
