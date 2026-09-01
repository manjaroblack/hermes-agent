---
name: plan
description: Write a markdown plan to .hermes/plans/; no execution.
version: 2.0.0
author: Hermes Agent (writing-craft adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow, design, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Plan Mode

role: implementation-plan author
do: inspect context read-only; design approach; write actionable Markdown plan; save under `.hermes/plans/`; report saved path
inputs: user request/current context, repo structure, requirements, constraints, likely files/tests
outputs: timestamped Markdown plan; no implementation or external mutation
¬: implement code; edit project files beyond plan; run mutating commands; commit/push/external actions; invent missing requirements; save outside active workspace

Use when the user wants a plan instead of execution. This turn is planning only;
the deliverable is a concrete Markdown file in the active workspace.

## When to Use

- user asks for a plan, design, breakdown, or `/plan`
- multi-step feature/bug work needs implementation guidance
- delegation needs exact tasks/context
- future implementer needs paths, code shape, tests, risks

Don't use for execution, production changes, or personal notes outside the active
workspace. If request is clear, write directly; if genuinely underspecified, ask a
brief clarifying question rather than guessing.

## Prerequisites

- active workspace/backend path
- read-only `search_files`, `read_file`, and inspection commands as needed
- `.hermes/plans/` destination
- current conversation requirements and constraints

## Core Behavior

- do not implement code
- do not edit project files except plan Markdown
- do not run mutating terminal commands, commit, push, or external actions
- inspect repo/context read-only when needed
- save plan inside active workspace under `.hermes/plans/`

## Output Requirements

Include when relevant: Goal; current context/assumptions; proposed approach;
step-by-step plan; likely changed files; tests/validation; risks/tradeoffs/open
questions. Code-related plans include exact paths, test targets, and verification.

## Save Location

Use:

- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Resolve relative to active working directory/backend workspace; this keeps plans
with local, Docker, SSH, Modal, and Daytona workspaces. Use a runtime-provided
exact target when given; otherwise create a sensible timestamped filename.

## Procedure

1. Understand requirements, design docs, acceptance criteria, and constraints.
2. Explore repo/context with read-only tools; identify similar code/tests.
3. Decide architecture, file organization, dependencies, and test strategy.
4. Write sequential bite-sized tasks to the save path.
5. Review plan for exactness/completeness; save and report path.
6. If execution follows, offer `subagent-driven-development` handoff.

## Writing the Plan Well

Assume implementer has zero domain/codebase context but strong engineering skill.
Document enough to make implementation obvious: files, code, commands, tests,
docs, verification, and risks. Apply DRY, YAGNI, TDD, frequent commits.

### Bite-Sized Task Granularity

Each task = 2-5 minutes focused work; each step = one action:

- write failing test
- run it and verify failure
- write minimal implementation
- run tests and verify pass
- commit

Too big:

```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

Right size:

```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

### Plan Document Structure

Every plan starts:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

Each task:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

### Read-Only Codebase Exploration

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Task Ordering

1. setup/infrastructure
2. core functionality, TDD for each
3. edge cases
4. integration
5. cleanup/documentation

For each task include exact file paths, complete code examples (not vague
“add validation”), exact commands with expected output, and proof-oriented checks.

### Review the Plan

- [ ] tasks sequential and logical
- [ ] each task bite-sized (2-5 min)
- [ ] paths exact
- [ ] code examples complete/copy-pasteable
- [ ] commands exact with expected output
- [ ] no missing context
- [ ] DRY, YAGNI, TDD applied

## Principles

### DRY

Bad: copy validation in three places. Good: extract a validation function and
reuse it.

### YAGNI

Bad:

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

Specify only current requirements; do not add future flexibility.

### TDD

Every code task includes:

1. failing test
2. run and verify failure
3. minimal code
4. run and verify pass

See `test-driven-development` for full workflow.

### Frequent Commits

Commit each task:

```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

- vague “add authentication” → name concrete model/fields/files
- “add validation” without complete code → include implementation shape
- “test it works” → exact command + expected output
- missing file paths → exact create/modify/test paths

## Execution Handoff

After saving:

> Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?

When executing, use `subagent-driven-development`: fresh delegate per task; spec
compliance review; code-quality review; proceed only after both approve.

## Pitfalls

- plan mode is not implementation; only plan Markdown may be written
- relative plan path must resolve to active backend workspace
- no mutating commands, commits, pushes, or external actions during plan turn
- do not guess genuinely missing requirements; ask one brief clarification
- task granularity must permit focused execution and independent verification
- code-related plans need exact paths/tests, not generic file references
- current plan filename should be timestamped and slugged when no target is given

## Verification

- saved file exists under `.hermes/plans/` at the active workspace
- filename matches `YYYY-MM-DD_HHMMSS-<slug>.md` or supplied target
- goal/context/approach/tasks/files/tests/risks included as applicable
- each task has one objective, exact paths, actionable steps, expected checks
- no project files or external state changed
- final response names the saved path and execution handoff status
