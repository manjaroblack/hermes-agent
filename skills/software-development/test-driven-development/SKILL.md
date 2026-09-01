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
    related_skills: [systematic-debugging, plan, subagent-driven-development]
---

# Test-Driven Development (TDD)

role: test-first implementation operator
do: write one behavior test; watch RED; implement minimum GREEN; watch pass; refactor; repeat; verify full suite
inputs: required behavior/API, edge cases, test framework, implementation target
outputs: behavior-focused tests, minimal implementation, green regression suite, clean refactor
¬: production code before failing test; keep prewritten implementation; tests-after; mocks instead of real behavior; horizontal test/implementation piles; skip RED/GREEN; rationalize exceptions without permission

Write the test first, watch it fail, then write the minimum code to pass. If the
failure was not observed, test validity is unknown.

## When to Use

Always for new features, bug fixes, refactors, and behavior changes. Exceptions
only after asking user: throwaway prototypes, generated code, configuration.
“Just this once” is rationalization.

## Prerequisites

- required behavior/API and edge cases
- project test command and target test location
- real implementation path; mocks only when unavoidable
- permission to delete prewritten production code if it predates RED

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Code before test → delete it (do not keep/adapt/reference it); implement fresh
from tests.

## Procedure

### RED — Write one failing test

One behavior/test, clear name, real code, behavior not implementation:

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

Requirements: one behavior; split names containing “and”; use mocks only when
unavoidable; test real code.

Bad:

```python
def test_retry_works():
    mock = MagicMock()
    mock.side_effect = [Exception(), Exception(), 'success']
    result = retry_operation(mock)
    assert result == 'success'  # What about retry count? Timing?
```

### Verify RED — watch failure (mandatory)

```bash
# Use terminal tool to run the specific test
pytest tests/test_feature.py::test_specific_behavior -v
```

Confirm failure is expected, not typo/error, and feature is missing. Immediate
pass = existing behavior → fix test. Error → fix test error until correct RED.

### GREEN — minimum implementation

Simplest code that passes, nothing extra:

```python
def add(a, b):
    return a + b  # Nothing extra
```

Do not add features/refactor beyond test. Hardcoding/copy-paste/duplication/edge
case omissions are temporarily allowed in GREEN; fix in REFACTOR.

Bad:

```python
def add(a, b):
    result = a + b
    logging.info(f"Adding {a} + {b} = {result}")  # Extra!
    return result
```

### Verify GREEN — watch pass (mandatory)

```bash
# Run the specific test
pytest tests/test_feature.py::test_specific_behavior -v

# Then run ALL tests to check for regressions
pytest tests/ -q
```

Confirm test + suite pass and output has no errors/warnings. Test failure → fix
code, not test; other failure → fix regression now.

### REFACTOR — clean only after GREEN

Remove duplication, improve names, extract helpers, simplify expressions. Keep
tests green; add no behavior. Refactor failure → undo immediately and take smaller
steps. Repeat one RED→GREEN→REFACTOR cycle per behavior.

## Avoid Horizontal Slices

Do not write all tests then all implementation. Use vertical tracer bullets:

```text
WRONG:
  RED:   test1, test2, test3, test4
  GREEN: impl1, impl2, impl3, impl4

RIGHT:
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

Each tracer is one end-to-end behavior; it proves path and teaches the next
interface.

## Why Order Matters

Tests-after pass immediately and may test implementation, wrong behavior, or
missed edges; manual testing is unrecorded/unrepeatable; sunk cost does not make
unverified code trustworthy. TDD finds bugs before commit, prevents regressions,
documents behavior, and enables refactoring. Tests-first asks “what should this
do?”; tests-after asks “what does this do?”

## Common Rationalizations

| Excuse | Reality |
|---|---|
| “Too simple to test” | Simple code breaks; test takes 30 seconds. |
| “I'll test after” | Immediate pass proves nothing. |
| “Tests after achieve same goals” | Tests-after = what; tests-first = should. |
| “Already manually tested” | Ad-hoc, no record/re-run, misses cases. |
| “Deleting hours is wasteful” | Sunk cost; unverified code is debt. |
| “Keep as reference” | You will adapt it; delete means delete. |
| “Need to explore first” | Throw away exploration, restart TDD. |
| “Test hard = design unclear” | Hard to test = hard to use; simplify. |
| “TDD slows me down” | Faster than production debugging. |
| “Manual test faster” | Does not prove edges; every change repeats it. |
| “Existing code has no tests” | Add tests for code touched. |

## Red Flags — STOP and Start Over

Delete/restart TDD if: code before test; test-after; immediate first pass; cannot
explain RED; tests “later”; “just this once”; manual-only verification; reference/
adapt existing implementation; sunk-cost defense; “dogmatic/pragmatic” defense;
“This is different because…”.

## Verification Checklist

- [ ] every new function/method has a test
- [ ] watched each test fail before implementation
- [ ] failure was expected feature absence, not typo
- [ ] minimum code passed each test
- [ ] all tests pass with pristine output
- [ ] real code tested; mocks only unavoidable
- [ ] edge cases/errors covered

Missing box → TDD skipped; restart.

## When Stuck

| Problem | Solution |
|---|---|
| Don't know how to test | Write wished-for API/assertion; ask user. |
| Test too complicated | Simplify design/interface. |
| Must mock everything | Decouple with dependency injection. |
| Test setup huge | Extract helpers; simplify if still complex. |

## Hermes Agent Integration

### Running tests

```python
# RED — verify failure
terminal("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
terminal("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
terminal("pytest tests/ -q")
```

### Delegated implementation

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

- test mock behavior instead of real behavior
- test implementation details instead of behavior/results
- happy path only; cover edges/errors/boundaries
- brittle structure tests that refactors break

## Pitfalls

- skipping RED/GREEN loses proof the test catches behavior
- immediate pass usually means wrong/existing behavior
- test typo errors are not valid RED
- horizontal slices produce imagined/brittle tests
- “minimum GREEN” is not permission to ship cheating shortcuts
- refactor only after GREEN; undo if tests fail
- `scripts/run_tests.sh`/runner may differ from raw pytest; use project convention
- mocks hide integration behavior; use real code where possible
- existing untested code still needs tests at touched seams

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without explicit user permission.
