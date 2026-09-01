---
name: spike
description: "Throwaway experiments to validate an idea before build."
version: 1.0.0
author: Hermes Agent (adapted from gsd-build/get-shit-done)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spike, prototype, experiment, feasibility, throwaway, exploration, research, planning, mvp, proof-of-concept]
    related_skills: [sketch, subagent-driven-development]
---

# Spike

role: feasibility-spike operator
do: decompose questions; align scope; research approaches; build disposable probes; test edge cases; record verdict/recommendation
inputs: idea, feasibility question(s), approaches, user constraints, existing GSD setup
outputs: `spikes/NNN-descriptive-name/README.md`, runnable probe, evidence, VALIDATED/PARTIAL/INVALIDATED verdict
¬: productionize/clean up spike; skip observable tests; call happy-path success complete; add complex package/config infrastructure; research-only answer when a probe is needed

Use to feel out an idea before a real build: feasibility, approach comparison,
or unknowns research cannot answer. Spikes are disposable; discard after they
pay their uncertainty debt.

Load for “let me try this”, “spike this”, “before I commit”, “quick prototype”,
“is this possible?”, or “compare A vs B”.

## When to Use

Don't use when:

- docs/code already answer the question → research
- work is production path → `plan`
- idea is validated → implement

If `gsd-spike` is installed via `npx get-shit-done-cc --hermes`, prefer it for
persistent `.planning/spikes/`, MANIFEST, Given/When/Then verdicts, and GSD commits;
this skill is lightweight standalone mode.

## Prerequisites

- a concrete feasibility question or idea
- active workspace and disposable `spikes/` destination
- `terminal`, `write_file`, `read_file`, `web_search`, and optional `delegate_task`
- user alignment when multiple spikes/approaches are proposed

## Procedure

### 1. Decompose

Break idea into 2-5 independent observable feasibility questions; order by risk.
Present Given/When/Then table:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

Types: `standard` = one approach/question; `comparison` = same question,
shared number + `a`/`b`/`c`.

Good = specific feasibility + observable output. Bad = broad, unobservable, or
“read docs.” Skip decomposition only when user names exactly one spike.

### 2. Align multi-spike scope

Ask: “Build all in this order, or adjust?” Let user drop/reorder/reframe before
writing code.

### 3. Research each spike

Before building:

1. Brief what/why/risk in 2-3 sentences.
2. Surface competing approaches when choice is real:

   | Approach | Tool/Library | Pros | Cons | Status |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. Pick and justify one; build variants when ≥2 credible.
4. Skip research for pure logic/no external dependency.

Use Hermes tools:

- `web_search("python websocket streaming libraries 2025")`
- `web_extract(urls=["https://websockets.readthedocs.io/..."])`
- `terminal("pip show websockets | grep Version")`
- clone/read `README.md`/`examples/` with `read_file` when docs are absent
- optional Context7 MCP: `mcp_*_resolve-library-id` → `mcp_*_query-docs`

### 4. Build disposable probes

One standalone directory/spike:

```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   ├── README.md
│   └── parse.js
└── 002b-pdf-parse-camelot/
    ├── README.md
    └── parse.py
```

Prefer observable interaction:

1. runnable CLI input → output
2. minimal HTML demo
3. one-endpoint web server
4. unit test with recognizable assertions

Test edge cases and follow surprises; one happy-path run cannot validate an
idea. Avoid complex package management/build tools/bundlers/Docker/env/config
unless spike requires them; hardcode for throwaway work.

Typical sequence:

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python main.py")
# Observe output, iterate.
```

Parallel comparison spikes (real engineering, not 10-line probes):

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

Collect each subagent verdict and write head-to-head comparison.

### 5. Verdict

Each README ends:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

- VALIDATED = core question yes, evidence-backed
- PARTIAL = works under documented X/Y/Z constraints
- INVALIDATED = does not work for documented reason; this is a successful spike

### Comparison verdict

Build approaches back to back, then record:

```markdown
## Head-to-head: pdfjs vs camelot

| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 structured | 7/10 table-only |
| Setup complexity | npm install, 1 line | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
| Handles rotated text | no | yes |

**Winner:** pdfjs for our use case. Camelot if we need table-first extraction later.
```

### Frontier mode

For existing spikes, propose 2-4 Given/When/Then next candidates targeting:

- integration risks between independently validated spikes
- unproven data handoffs
- assumed/unproven capabilities
- alternatives for PARTIAL/INVALIDATED results

Let user choose.

## Output

- create `spikes/` (or `.planning/spikes/` with GSD)
- one `NNN-descriptive-name/` per spike
- README captures question, approach, results, verdict
- keep code throwaway; two-day cleanup means spike scope failed

## Pitfalls

- docs/code-known answer does not need a build
- no observable output or edge-case probe is weak evidence
- do not call one happy path “works”
- package/build/Docker/config complexity obscures feasibility
- production path belongs to `plan`, not spike
- comparison results need same question and head-to-head dimensions
- a failed/INVALIDATED spike is useful; record why
- use persistent GSD mode when installed and requested

## Verification

- Given/When/Then question(s), risk order, and user alignment recorded
- approach research/choice and evidence documented
- probe runs with observable output plus edge cases
- comparison variants are independently run and compared
- README has complete verdict sections and recommendation
- no production files, cleanup, or hidden infrastructure added

## Attribution

Adapted from GSD `/gsd-spike` — MIT © 2025 Lex Christopherson
([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). Full GSD:
`npx get-shit-done-cc --hermes --global`.
