---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, subagent-driven-development]
---

# Systematic Debugging

role: root-cause debugging investigator
do: build red-capable feedback loop; read evidence; trace data flow; compare patterns; rank/test hypotheses; implement one root fix; verify regression
inputs: error/traceback, exact symptom, reproduction, repo/history/config, component boundaries
outputs: isolated root cause, minimal repro/regression test, single root fix, green verification
¬: guess/fix before Phase 1; stack fixes; bundle changes; skip failing test; treat symptom as cause; attempt Fix #4 without architecture discussion; hide uncertainty

## Overview

Random fixes waste time/create bugs; quick patches mask underlying issues.
ALWAYS find root cause before fixes; symptom fixes = failure. Violating the letter
of this process violates its spirit.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If Phase 1 is incomplete, do not propose a fix.

## Feedback Loop Rule

The feedback loop is the debugging work. Before reading code to form a theory,
create/identify a **tight** command that goes red on the exact user symptom and
green after the fix. It is fast, deterministic, agent-runnable, and specific —
not merely "doesn't crash". If clean repro is hard, invest disproportionately
in the loop; guessing without a red-capable loop is the failure mode.

## When to Use

Use for ANY technical issue:

- test failures
- production bugs
- unexpected behavior
- performance problems
- build failures
- integration issues

Especially use when under time pressure, a "quick fix" seems obvious, several
fixes already failed, the prior fix did not work, or the issue is not understood.
Do not skip because issue seems simple, time is short, or someone wants it fixed
NOW; systematic debugging is faster than thrashing.

## Prerequisites

- exact symptom/error + candidate reproduction path
- workspace + repo tests/history/config access
- `search_files`, `read_file`, `terminal`; optional `web_search`/`delegate_task`
- permission to add focused regression test + one root fix

## The Four Phases

Complete each phase before the next.

---

## Phase 1: Root Cause Investigation

**Before attempting ANY fix:**

### 1. Read Error Messages Carefully

- don't skip errors/warnings; they often contain the solution
- read complete stack traces
- record line numbers, file paths, error codes
- use `read_file` on relevant sources; `search_files` for error strings

### 2. Build and Run a Tight Feedback Loop

Ask:

- can one command trigger the exact symptom?
- does it fail for this bug and pass only after the fix?
- is it fast/repeatable and deterministic?
- for flakes, can reproduction rise high enough to debug?
- if not reproducible → gather data, don't guess

Construct a loop, roughly in order:

1. failing unit/integration/end-to-end test at the failing seam
2. HTTP script / `curl` against a running dev server
3. CLI fixture invocation with stdout/stderr assertion
4. headless Playwright/Puppeteer browser assertion on DOM/console/network
5. replay captured HAR, request payload, event log, queue message, or webhook
6. throwaway harness booting the smallest useful slice and calling the path
7. property/fuzz loop for intermittent wrong output over broad input space
8. bisection harness suitable for `git bisect run`
9. differential old/new version, config, provider, or dataset loop
10. human-in-loop script last; capture structured result

Tighten the loop:

- faster: cache setup, narrow scope, skip unrelated initialization
- sharper: assert exact symptom, not generic success
- deterministic: pin time, seed randomness, isolate filesystem, freeze network

For non-determinism, raise reproduction rather than seek perfection: run 100x,
parallelize/stress, narrow timing, or inject sleeps. 50% flake is debuggable;
1% usually is not.

Use `terminal`:

```bash
# Run a specific failing test
pytest tests/test_module.py::test_name -v

# Or run a scripted repro
python scripts/repro_bug.py

# Or run a high-repetition flaky repro
for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done
```

### 3. Check Recent Changes

Ask what changed: git diff/recent commits, new dependencies, config changes.

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

For API→service→database, CI→build→deploy, or another chain, instrument EACH
boundary before proposing a fix:

- log data entering and exiting each component
- verify environment/config propagation
- check state at every layer
- run once to show WHERE it breaks
- analyze evidence, identify failing component, investigate there

### 5. Trace Data Flow

For deep-stack errors, locate bad value origin, caller, and source; fix source,
not symptom. Use `search_files`:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion

- [ ] errors/warnings fully read and understood
- [ ] tight loop exists and ran once
- [ ] loop asserts exact symptom and can go red
- [ ] deterministic or high-repro flake
- [ ] recent changes reviewed
- [ ] logs/state/data-flow evidence gathered
- [ ] component/code isolated
- [ ] testable root-cause hypotheses stated

**STOP:** no Phase 2 until WHY is understood.

---

## Phase 2: Pattern Analysis

Find the pattern before fixing.

### 0. Minimize the Reproduction

With red loop, remove inputs, callers, config, data, and steps one at a time;
rerun after each cut. Keep only load-bearing elements. Done when removing any
remaining element makes loop green. Minimal repro narrows hypotheses and often
becomes the regression test.

### 1. Find Working Examples

Locate analogous working code; ask what works that resembles the broken path.
Use `search_files`:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

When applying a pattern, read the reference implementation COMPLETELY — every
line, no skimming; understand it before adapting.

### 3. Identify Differences

Compare working/broken and list every difference, however small; do not assume
"that can't matter".

### 4. Understand Dependencies

Record required components, settings/config/environment, and assumptions.

---

## Phase 3: Hypothesis and Testing

Scientific method:

### 1. Form Ranked Falsifiable Hypotheses

Generate 3–5 plausible hypotheses before testing any. Rank by likelihood and
cheapness to falsify. State prediction: "If X is cause, changing/observing Y
should make Z happen." Discard/sharpen hypotheses without testable predictions.
Show ranked list if user present (domain knowledge may re-rank); proceed ranked
if AFK.

### 2. Test Minimally

Test highest-ranked with smallest probe; change one variable at a time; never fix
multiple things together. Prefer debugger/REPL (one breakpoint > ten logs). If
logs are needed, tag temporary lines with unique prefix such as `[DEBUG-a4f2]`.

### 3. Verify Before Continuing

- worked → Phase 4
- failed → form NEW hypothesis
- never stack fixes

### 4. When You Don't Know

Say "I don't understand X"; don't pretend; ask user for help or research more.

---

## Phase 4: Implementation

Fix root cause, not symptom.

### 1. Create Failing Test Case

Use simplest reproduction; automate when possible; MUST exist before fix; use
`test-driven-development`.

### 2. Implement Single Fix

Address identified root cause, ONE change at a time; no "while I'm here",
bundled refactor, or unrelated improvement.

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — Rule of Three

STOP and count attempts:

- `<3` → return Phase 1 with new information
- `≥3` → question architecture; no Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

Signals: each fix reveals shared state/coupling elsewhere; fixes need "massive
refactoring"; each fix creates new symptoms. Ask:

- is the pattern fundamentally sound?
- are we sticking with it through inertia?
- refactor architecture or continue fixing symptoms?

Discuss with user before more fixes. This is wrong architecture, not merely a
failed hypothesis.

---

## Red Flags — STOP and Follow Process

Any of these → STOP, return Phase 1:

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems" before investigation
- proposing solutions before tracing data flow
- "One more fix attempt" after 2+
- each fix reveals a new problem elsewhere

If 3+ fixes failed, question architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes; process is fast. |
| "Emergency, no time for process" | Systematic debugging is FASTER than thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern; investigate first. |
| "I'll write test after confirming fix" | Untested fixes don't stick; test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked; causes new bugs. |
| "Reference too long, I'll adapt" | Partial understanding guarantees bugs; read completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" after 2+ | 3+ failures = architecture problem. |

## Quick Reference

| Phase | Key activities | Success criteria |
|-------|---------------|------------------|
| **1. Root Cause** | read errors, reproduce, changes, evidence, data flow | understand WHAT + WHY |
| **2. Pattern** | working examples, complete comparison, differences | know what's different |
| **3. Hypothesis** | ranked theory, minimal one-variable test | confirmed/new hypothesis |
| **4. Implementation** | regression test, root fix, verification | bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

- `search_files` — errors, calls, variables, patterns
- `read_file` — numbered source and precise context
- `terminal` — tests, git history, repro
- `web_search`/`web_extract` — error and library research

### With delegate_task

For complex multi-component debugging, dispatch investigation only — do NOT fix
inside the investigator prompt:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

RED failing reproduction → investigate root cause → GREEN root fix → regression
proof. Never fix bugs without a test.

## Pitfalls

- symptom patch without upstream trace
- green loop that does not assert exact user failure
- non-reproducible flake treated as known cause
- multiple variables/fixes in one probe
- incomplete reference read or ignored small difference
- temporary logs without unique cleanup prefix
- instrumentation without boundary evidence
- wrapper/parallel runner hiding interactive debugging
- third failed fix followed by Fix #4 instead of architecture discussion

## Verification

- [ ] Phase 1 complete before any fix
- [ ] minimal red repro removes non-load-bearing setup
- [ ] working/broken differences + dependencies documented
- [ ] 3–5 ranked falsifiable hypotheses tested one at a time
- [ ] regression test fails before fix and passes after
- [ ] full suite has no regressions; debug instrumentation removed
- [ ] root cause, not symptom, changed; architecture escalation after 3 failures

## Real-World Impact

From debugging sessions:

- systematic: 15–30 minutes to fix
- random: 2–3 hours of thrashing
- first-time fix rate: 95% vs 40%
- new bugs: near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
