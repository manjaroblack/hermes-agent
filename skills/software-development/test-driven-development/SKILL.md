---
name: test-driven-development
description: "TDD: enforce RED-GREEN-REFACTOR, tests before code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [testing, tdd, development, quality, red-green-refactor]
    related_skills: [systematic-debugging, subagent-driven-development]
---

# Test-Driven Development (TDD)

role: test-first implementation operator
do: write one behavior test; watch RED; implement minimum GREEN; watch pass; refactor; repeat; verify full suite
inputs: required behavior/API, edge cases, test framework, implementation target
outputs: behavior-focused tests, minimal implementation, green regression suite, clean refactor
¬: production code before failing test; keep prewritten implementation; tests-after; mocks instead of real behavior; horizontal test/implementation piles; skip RED/GREEN; rationalize exceptions without permission

## Overview

Write the test first; watch it fail; write minimal code to pass. If failure was
not observed, test validity is unknown. Violating the letter violates the spirit.

## When to Use

Always for:

- new features
- bug fixes
- refactoring
- behavior changes

Exceptions require the user's explicit permission first:

- throwaway prototypes
- generated code
- configuration files

"Just this once" is rationalization; stop.

## Prerequisites

- required behavior/API + edge cases
- project test command + target test path
- real implementation path; mocks only when unavoidable
- permission to delete prewritten production code predating RED

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Code before test? Delete it and start over. Do not keep as reference, adapt while
writing tests, or look at it; delete means delete. Implement fresh from tests.

## Red-Green-Refactor Cycle

### RED — Write Failing Test

Write one minimal test showing what should happen: clear behavior name, real code,
one behavior, not implementation.

Good:

```python
def test_retries_failed_operations_3_times():
    attempts = 0
    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception('fail')
        return 'success'

    result = retry_operation(operation)

    assert result == 'success'
    assert attempts == 3
```

Bad:

```python
def test_retry_works():
    mock = MagicMock()
    mock.side_effect = [Exception(), Exception(), 'success']
    result = retry_operation(mock)
    assert result == 'success'  # What about retry count? Timing?
```

Requirements: one behavior/test; split names containing "and"; test real code,
not mocks unless truly unavoidable; name behavior, not implementation.

### Verify RED — Watch It Fail

**MANDATORY; never skip.**

```bash
# Use terminal tool to run the specific test
pytest tests/test_feature.py::test_specific_behavior -v
```

Confirm: test fails, not from a typo; failure message is expected; failure is
because feature is missing. Immediate pass means existing behavior → fix test.
Error means fix test error and rerun until correct RED.

### GREEN — Minimal Code

Write simplest code that passes; nothing extra.

Good:

```python
def add(a, b):
    return a + b  # Nothing extra
```

Bad:

```python
def add(a, b):
    result = a + b
    logging.info(f"Adding {a} + {b} = {result}")  # Extra!
    return result
```

Don't add features, refactor other code, or improve beyond the test. Temporary
GREEN shortcuts are allowed: hardcode return values, copy-paste, duplicate code,
skip edge cases; fix them in REFACTOR.

### Verify GREEN — Watch It Pass

**MANDATORY.**

```bash
# Run the specific test
pytest tests/test_feature.py::test_specific_behavior -v

# Then run ALL tests to check for regressions
pytest tests/ -q
```

Confirm specific test passes, other tests pass, and output is pristine (no
errors/warnings). Test failure → fix code, not test. Other failure → fix
regression now.

### REFACTOR — Clean Up

Only after GREEN: remove duplication, improve names, extract helpers, simplify
expressions. Keep tests green; add no behavior. Refactor failure → undo
immediately and take smaller steps.

### Repeat

Write the next failing test for the next behavior; one RED→GREEN→REFACTOR cycle
at a time.

## Avoid Horizontal Slices

Do not write all tests then all implementation: RED becomes imagined test piles,
GREEN becomes making the pile pass, and tests become brittle before the interface
teaches you what behavior matters. Use vertical tracer bullets:

```text
WRONG:
  RED:   test1, test2, test3, test4
  GREEN: impl1, impl2, impl3, impl4

RIGHT:
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

Each tracer is one end-to-end behavior slice; it proves the path, teaches the next
interface, and grounds the next test.

## Why Order Matters

**"I'll write tests after to verify it works."** Tests-after pass immediately;
that proves nothing: wrong thing, implementation not behavior, forgotten edges,
and never observed bug capture. Test-first observes RED and proves the test tests
something.

**"I manually tested every edge case."** Manual testing is ad hoc: no record, no
repeatability after code changes, easy omissions under pressure; "it worked when
I tried it" ≠ comprehensive. Automation runs systematically the same way.

**"Deleting X hours is wasteful."** Sunk cost is gone. Delete/rewrite with TDD
for confidence, or keep untrusted code with likely bugs; the waste is keeping it.

**"TDD is dogmatic; pragmatism adapts."** TDD finds bugs before commit, prevents
regressions, documents behavior, and enables refactoring; shortcuts move debugging
to production and are slower.

**"Tests-after achieve the same goals; ritual is not spirit."** Tests-after ask
"What does this do?" and bias toward what was built; tests-first ask "What should
this do?" and force edge-case discovery before implementation.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after = "what"; tests-first = "what should". |
| "Already manually tested" | Ad hoc ≠ systematic; no record, can't rerun. |
| "Deleting X hours is wasteful" | Sunk cost; unverified code is technical debt. |
| "Keep as reference, write tests first" | You'll adapt it; delete means delete. |
| "Need to explore first" | Throw away exploration; start with TDD. |
| "Test hard = design unclear" | Hard to test = hard to use; simplify. |
| "TDD will slow me down" | TDD is faster than debugging. |
| "Manual test faster" | It misses edges and repeats every change. |
| "Existing code has no tests" | Add tests for code touched. |

## Red Flags — STOP and Start Over

Delete code and restart with TDD if:

- code before test; test after implementation
- test passes immediately on first run
- cannot explain why test failed
- tests added "later" or "just this once" rationalization
- manual-only verification
- "tests after achieve same purpose"
- keep/adapt existing implementation as reference
- sunk-cost defense
- "dogmatic/pragmatic" defense
- "This is different because..."

All mean: delete code; start over with TDD.

## Verification Checklist

Before completion:

- [ ] every new function/method has a test
- [ ] watched each test fail before implementation
- [ ] each failure was expected (missing feature, not typo)
- [ ] minimum code passed each test
- [ ] all tests pass with pristine output
- [ ] real code tested; mocks only unavoidable
- [ ] edge cases/errors covered

Can't check every box? TDD was skipped; start over.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API/assertion first; ask user. |
| Test too complicated | Design/interface too complicated; simplify. |
| Must mock everything | Code too coupled; use dependency injection. |
| Test setup huge | Extract helpers; still complex → simplify design. |

## Hermes Agent Integration

### Running Tests

Use `terminal` at each step:

```python
# RED — verify failure
terminal("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
terminal("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
terminal("pytest tests/ -q")
```

### With delegate_task

Enforce TDD in implementation dispatch:

```python
delegate_task(
    goal="Implement [feature] using strict TDD",
    context="""
    Follow test-driven-development skill:
    1. Write failing test FIRST
    2. Run test to verify it fails
    3. Write minimal code to pass
    4. Run test to verify it passes
    5. Refactor if needed
    6. Commit

    Project test command: pytest tests/ -q
    Project structure: [describe relevant files]
    """,
    toolsets=['terminal', 'file']
)
```

### With systematic-debugging

Bug → RED reproduction → systematic root cause → GREEN root fix → regression
proof. Never fix bugs without a test.

## Testing Anti-Patterns

- testing mock behavior instead of real behavior; mocks verify interactions, not
  replace the system under test
- testing implementation details instead of behavior/results
- happy path only; cover edges, errors, boundaries
- brittle structure tests that refactors break; verify behavior instead

## Pitfalls

- skipping RED/GREEN loses proof the test catches behavior
- immediate pass usually means wrong/existing behavior
- typo errors are not valid RED
- horizontal slices produce imagined/brittle tests
- minimum GREEN shortcuts are not permission to ship them
- refactor only after GREEN; undo if tests fail
- `scripts/run_tests.sh`/runner may differ from raw pytest; use project convention
- mocks hide integration behavior; use real code where possible
- existing untested code still needs tests at touched seams

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without the user's explicit permission.
