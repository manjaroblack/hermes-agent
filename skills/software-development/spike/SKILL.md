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

Use this skill to feel out an idea before committing to a real build: validate
feasibility, compare approaches, or surface unknowns research cannot answer.
Spikes are disposable; throw them away after paying their uncertainty debt.

## When to Use

Load for "let me try this", "I want to see if X works", "spike this out",
"before I commit to Y", "quick prototype of Z", "is this even possible?", or
"compare A vs B".

## When NOT to Use

- docs/code already answer the question → research, don't build
- work is production path → use `plan`
- idea is already validated → implement directly

## Full GSD Mode

If `gsd-spike` appears as a sibling (installed via
`npx get-shit-done-cc --hermes`), prefer it when the user wants full GSD:
persistent `.planning/spikes/` state, MANIFEST tracking, Given/When/Then
verdicts, and commits integrated with the rest of GSD. This is lightweight
standalone mode for users without or not wanting that system.

## Core Method

Every spike follows:

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

## Prerequisites

- concrete feasibility question or idea
- active workspace + disposable `spikes/` destination
- `terminal`, `write_file`, `read_file`, `web_search`, optional `delegate_task`
- user alignment when multiple spikes/approaches are proposed

## Procedure

### 1. Decompose

Break the idea into **2–5 independent feasibility questions**; one question =
one spike. Order by risk and present Given/When/Then:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

Types: `standard` = one approach/question; `comparison` = same question,
different approaches, shared number + `a`/`b`/`c` suffix.

Good = specific feasibility + observable output. Bad = broad, unobservable, or
only "read the docs". Run the highest idea-killing risk first; easy parts are
wasted if the hard part fails. Skip decomposition only when the user explicitly
knows exactly one spike.

### 2. Align multi-spike scope

Present the table and ask: "Build all in this order, or adjust?" Let the user
drop, reorder, or re-frame before code.

### 3. Research each spike

Spikes are not research-free: research enough to choose, then build.

1. Brief what/why/key risk in 2–3 sentences.
2. If choice is real, surface candidates:

   | Approach | Tool/Library | Pros | Cons | Status |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. Pick one and justify it; if ≥2 credible, build quick variants.
4. Skip research for pure logic with no external dependency.

Use Hermes tools:

- `web_search("python websocket streaming libraries 2025")` → candidates
- `web_extract(urls=["https://websockets.readthedocs.io/..."])` → actual docs
- `terminal("pip show websockets | grep Version")` → installed project version
- absent docs → clone, then `read_file` `README.md` / `examples/`
- optional Context7 MCP: `mcp_*_resolve-library-id` → `mcp_*_query-docs`

### 4. Build disposable probes

One standalone directory per spike:

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

Bias toward interaction, not a log line saying "it works":

1. runnable CLI input → observable output
2. minimal HTML behavior demo
3. one-endpoint web server
4. unit test with recognizable assertions

Depth over speed: test edge cases, follow surprises, and never declare success
from one happy path. Avoid complex package management, build tools/bundlers,
Docker, env files, and config systems unless required; hardcode throwaway work.

Typical single-spike sequence:

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python main.py")
# Observe output, iterate.
```

Comparison spikes 002a/002b: when both need real engineering (not 10-line
probes), delegate in parallel:

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

Each subagent returns a verdict; write the head-to-head comparison.

### 5. Verdict

Each spike `README.md` closes with:

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

- **VALIDATED** = core question answered yes with evidence
- **PARTIAL** = works under documented X/Y/Z constraints
- **INVALIDATED** = doesn't work for documented reason; still a successful spike

## Comparison Spikes

For approaches answering one question, build them back to back, then record:

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

## Frontier Mode

If existing spikes exist and the user asks "what should I spike next?", inspect
directories for:

- **Integration risks** — independently validated spikes touch one resource
- **Data handoffs** — A output assumed compatible with B input, never proven
- **Gaps in the vision** — assumed but unproven capabilities
- **Alternative approaches** — other angles for PARTIAL/INVALIDATED results

Propose 2–4 Given/When/Then candidates; let the user choose.

## Output

- create `spikes/` (or `.planning/spikes/` with GSD) at repo root
- one `NNN-descriptive-name/` per spike
- each `README.md` captures question, approach, results, verdict
- keep code throwaway; 2 days of production cleanup means spike scope failed

## Pitfalls

- docs/code-known answer needs research, not a build
- no observable output or edge-case probe = weak evidence
- one happy path ≠ validated
- package/build/Docker/config complexity obscures feasibility
- production path belongs to `plan`, not spike
- comparison requires same question + head-to-head dimensions
- failed/INVALIDATED spike is useful; record why
- use persistent GSD mode when installed and requested

## Verification

- [ ] Given/When/Then question(s), risk order, and alignment recorded
- [ ] approach research/choice and evidence documented
- [ ] probe has observable output + edge cases
- [ ] comparison variants independently run and compared
- [ ] README has complete verdict + recommendation
- [ ] no production files, cleanup, or hidden infrastructure added

## Attribution

Adapted from the GSD (Get Shit Done) project's `/gsd-spike` workflow — MIT ©
2025 Lex Christopherson
([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full
GSD system offers persistent spike state, MANIFEST tracking, and integration
with a broader spec-driven development pipeline; install with
`npx get-shit-done-cc --hermes --global`.
