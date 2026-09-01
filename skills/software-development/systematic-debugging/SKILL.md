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

Random fixes mask causes and create bugs. Complete every phase before the next.

## When to Use

Use for test/production bugs, unexpected behavior, performance/build/integration
failures—especially under time pressure, after multiple failed fixes, or when the
cause is unclear. “Simple,” urgent, or obvious issues do not exempt the process.

## Prerequisites

- exact symptom/error and a candidate reproduction path
- active workspace plus repo tests/history/config access
- `search_files`, `read_file`, `terminal`, and optional `web_search`/`delegate_task`
- permission to add a focused regression test and one root fix

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If Phase 1 is incomplete, do not propose a fix.

## Feedback Loop Rule

Before building theory, create/identify a **tight** command that goes red on the
exact symptom and green after the fix. It is fast, deterministic, agent-runnable,
and specific—not merely “doesn't crash.” If clean reproduction is hard, spend
more effort on the loop; guessing without a red-capable loop is failure.

## Procedure

### Phase 1: Root Cause Investigation

#### 1. Read errors

- read all errors/warnings and complete stack trace
- record line numbers, paths, error codes
- `read_file` relevant source; `search_files` error string

#### 2. Build and run tight loop

Ask: exact symptom? red before/green after? fast/repeatable? deterministic? For
flakes, high enough reproduction? If not reproducible → gather data, do not guess.

Ways to construct, roughly ordered:

1. failing unit/integration/E2E test at seam
2. HTTP script/curl against dev server
3. CLI fixture invocation + stdout/stderr assertion
4. headless browser assertion on DOM/console/network
5. replay HAR/request/event/queue/webhook trace
6. smallest throwaway harness
7. property/fuzz loop
8. `git bisect run` harness
9. differential old/new config/provider/dataset loop
10. human-in-loop script as last resort, capturing structured result

Tighten after creation: cache setup/narrow scope; assert exact symptom; pin time,
seed randomness, isolate filesystem, freeze network. For non-determinism, raise
reproduction: 100 runs, parallel/stress, timing narrowing/sleeps; 50% flake is
debuggable, 1% usually is not.

```bash
# Run a specific failing test
pytest tests/test_module.py::test_name -v

# Or run a scripted repro
python scripts/repro_bug.py

# Or run a high-repetition flaky repro
for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done
```

#### 3. Check recent changes

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

Check new dependencies/config as well as code.

#### 4. Gather boundary evidence

For API→service→DB, CI→build→deploy, or other multi-component chains, instrument
each boundary before fixing:

- data entering/exiting each component
- environment/config propagation
- state at each layer

Run once; identify failing component; investigate there.

#### 5. Trace data flow upstream

For deep-stack errors, ask where bad value originates, who passed it, and keep
tracing until source. Fix source, not symptom. Use `search_files`:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

#### Phase 1 completion

- [ ] all errors understood
- [ ] tight loop exists and ran once
- [ ] loop asserts exact symptom and can go red
- [ ] deterministic or high-repro flake
- [ ] recent changes reviewed
- [ ] logs/state/data-flow evidence gathered
- [ ] component/code isolated
- [ ] testable root-cause hypotheses stated

**STOP:** no Phase 2 until why is understood.

### Phase 2: Pattern Analysis

#### 0. Minimize reproduction

With red loop, remove inputs/callers/config/data/steps one at a time; rerun after
each cut. Done when removing any remaining element makes loop green. Minimal repro
becomes regression test and narrows hypotheses.

#### 1. Find working examples

Locate analogous working code:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

#### 2. Read reference completely

When applying a pattern, read reference implementation every line; do not skim.

#### 3. List every difference

Compare working/broken; record even small differences; do not assume irrelevance.

#### 4. Understand dependencies

Record components, settings/config/environment, and assumptions.

### Phase 3: Hypothesis and Testing

1. Generate 3-5 plausible, falsifiable hypotheses; rank by likelihood + cheapness.
   State prediction: “If X causes it, changing/observing Y makes Z.” Discard
   hypotheses without predictions. Show ranked list if user present; proceed if AFK.
2. Test highest-ranked with smallest probe; change one variable; prefer debugger/
   REPL; temporary logs use unique prefix such as `[DEBUG-a4f2]`.
3. Verify: works → Phase 4; fails → new hypothesis; never stack fixes.
4. If unknown: say “I don't understand X”; do not pretend; ask user or research.

### Phase 4: Implementation

#### 1. Create failing regression test

Smallest repro, automated when possible, **before fix**; use `test-driven-development`.

#### 2. Implement one root fix

One change at a time; no “while I'm here,” bundled refactor, or unrelated cleanup.

#### 3. Verify

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

#### 4. Rule of Three

If fix fails: STOP and count. `<3` → Phase 1 with new information. `≥3` →
architecture discussion; no Fix #4.

#### 5. Question architecture after 3 failures

Signals: each fix finds shared state/coupling elsewhere; fixes require massive
refactor; each creates new symptoms. Ask whether pattern is sound, inertia-driven,
or needs architectural refactor; discuss with user before further fixes. This is
wrong architecture, not merely failed hypothesis.

## Red Flags

Any thought below → STOP, return Phase 1:

- quick fix now/investigate later
- try X without evidence
- multiple changes then tests
- skip test/manual verify
- probably X
- do not fully understand
- adapt reference differently
- list solutions before data flow
- one more fix after 2+
- each fix reveals another location

≥3 failures → Phase 4 architecture question.

## Common Rationalizations

| Excuse | Reality |
|---|---|
| “Issue is simple, don't need process” | Simple issues have root causes; process is fast. |
| “Emergency, no time for process” | Systematic debugging is faster than thrashing. |
| “Just try this first” | First fix sets pattern; investigate first. |
| “I'll write test after” | Untested fixes don't stick; test first proves it. |
| “Multiple fixes save time” | Cannot isolate result; creates bugs. |
| “Reference too long” | Partial understanding guarantees bugs; read completely. |
| “I see the problem” | Symptom ≠ root cause. |
| “One more fix” after 2+ | 3+ failures indicate architecture. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|---|---|---|
| **1. Root Cause** | Read errors, reproduce, changes, evidence, data flow | Understand WHAT + WHY |
| **2. Pattern** | Working examples, complete comparison, differences | Know what's different |
| **3. Hypothesis** | Ranked theory, minimal one-variable test | Confirmed/new hypothesis |
| **4. Implementation** | Regression test, root fix, verification | Bug resolved, tests pass |

## Hermes Agent Integration

### Investigation Tools

- `search_files`: errors, calls, variables, patterns
- `read_file`: numbered source and precise context
- `terminal`: tests, git history, repro
- `web_search`/`web_extract`: error/library research

### Complex investigation with `delegate_task`

Investigation only; do not fix in the investigator prompt:

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

1. RED: failing reproduction
2. investigate root cause
3. GREEN: root fix
4. regression test remains proof

## Pitfalls

- symptom patch without upstream trace
- green loop that does not assert exact user failure
- non-reproducible flake treated as known cause
- multiple variables/fixes in one probe
- incomplete reference read or ignored small difference
- temporary logs without unique cleanup prefix
- instrumentation added but boundary evidence not collected
- wrapper/parallel runner hides interactive debugging
- third failed fix followed by Fix #4 instead of architecture discussion

## Verification

- Phase 1 checklist complete before any fix
- minimized red repro removes any non-load-bearing setup
- working/broken differences and dependencies documented
- 3-5 ranked falsifiable hypotheses tested one at a time
- regression test fails before fix and passes after
- full suite has no regressions; no debug instrumentation remains
- root cause, not symptom, changed; architecture escalation used after 3 failures

## Real-World Impact

Reported comparison from debugging sessions:

- systematic: 15-30 minutes vs random: 2-3 hours
- first-time fix: 95% vs 40%
- new bugs: near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
