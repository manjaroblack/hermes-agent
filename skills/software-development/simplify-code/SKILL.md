---
name: simplify-code
description: "Parallel 4-agent cleanup of recent code changes."
version: 1.1.0
author: Hermes Agent (inspired by Claude Code /simplify)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, cleanup, refactor, delegation, subagent, parallel, simplify]
    related_skills: [requesting-code-review, test-driven-development]
---

# Simplify Code — Parallel Review & Cleanup

role: post-change cleanup orchestrator
do: identify diff; run four focused reuse/quality/efficiency/altitude reviews; aggregate/dedupe; apply SAFE/CAREFUL fixes; verify touched files
inputs: recent diff/scope, optional focus (`reuse|quality|simplification|efficiency|altitude`), dry-run flag, repo path
outputs: applied cleanup, risky findings for human review, targeted test/lint results, grouped summary
¬: auto-run without explicit request; bug-hunt as cleanup; fan out >4; split diff; remove intentional shims; auto-apply RISKY changes; refactor untouched code

Four narrow reviewers run in parallel against the complete diff. This is cleanup
of code that already works: remove duplication/complexity/waste and deepen
band-aids; correctness bug hunting belongs to `requesting-code-review`.

## When to Use

- “simplify”, “simplify my/recent changes”
- “review my code/recent changes”, “clean up my changes”
- `/simplify`

Honor modifiers:

- focus efficiency/reuse/quality (`simplification` alias)/altitude → run/weight that reviewer
- dry run/just report → apply nothing; ask before applying
- last commit/staged/file/branch → narrow diff source

Do not append to unrelated edits; four subagents cost real tokens.

## Prerequisites

- git repo and recent changes or explicitly named files
- `terminal`, `read_file`, `search_files`; `delegate_task` when available
- targeted project tests/lint/typecheck commands
- user intent for scope/focus; no credentials needed

## Procedure

### 1. Identify changes

Default sources:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If that's empty, include staged changes
git diff HEAD

# 3. Scoped variants the user may request:
git diff --staged                 # "staged changes"
git diff HEAD~1                    # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If both diffs empty and no repo, use explicitly named/recent files; otherwise say
nothing can be simplified and stop. Capture complete diff + size. >2000 changed
lines → warn: four full copies are token-heavy; offer per-directory/commit scope.

### 2. Run four reviewers in parallel

Use `delegate_task` batch `tasks` array. If unavailable (leaf, disabled, budget),
run all four angles sequentially inline and state that handoff clearly.

Give every reviewer complete diff + absolute repo path + `terminal`, `file`,
`search`. Require existing-code search, `git blame` before removal (Chesterton's
Fence), and this finding format:

```
file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
```

Skip nits/style-only churn. Risk meanings:

- SAFE = proven behavior-neutral (unused imports/comments/pass-through wrappers) → auto-apply
- CAREFUL = semantic-preserving improvement (local rename/flatten/extract) → apply one file at a time + tests
- RISKY = behavior/public-contract/memory-lifecycle/concurrency impact → human review, no auto-apply

Reviewer 1 — **Code Reuse**: search utilities/shared helpers/adjacent files for
duplicated functions/constants/patterns; flag hand-rolled strings/paths/env checks,
type guards, parsing; name existing symbol + location.

Reviewer 2 — **Code Quality**: inspect redundant state, parameter sprawl,
copy-paste variation, leaky abstractions, stringly-typed code against registries,
3+ level conditionals, AI slop (`as any`, unnecessary null checks/comments,
inconsistent patterns); give concrete refactor.

Reviewer 3 — **Efficiency**: inspect repeated computation/reads/API/N+1,
missed concurrency, startup/per-request blocking work, TOCTOU checks, unbounded
memory/listener/handle/closure lifetime, broad reads, swallowed/ignored errors;
state faster/safer fix.

Reviewer 4 — **Altitude**: find call-site band-aids over shared infrastructure:
caller special cases/type checks/magic escapes, sibling symptom patches, stacked
workarounds, wrappers avoiding needed change, flags routing around broken default.
Read surrounding code/blame; identify deeper fix or mark as separate task. Do not
flag deliberate compat shims, staged migrations, or vendored isolation.

### 3. Aggregate and apply

Wait for all four.

1. Merge/dedupe same line/mechanism.
2. Discard weak/false findings.
3. Resolve conflicts: correctness > stated focus > readability/reuse > micro-perf;
   touch less code when equally defensible; note alternative.
4. Apply in order:
   - SAFE: unused imports/comments/pass-through/redundant assertions; test
   - CAREFUL: locals/ternaries/helpers/dupes, one file at a time; test each, revert breakage
   - RISKY: N+1/public API/concurrency/error-handling/altitude; report for human, do not auto-apply
   - dry run: present all, apply none
5. Run touched-file tests + repo lint/typecheck; revert a fix that breaks tests.
6. Summarize applied fixes by reviewer/risk and skipped findings; state inline-vs-parallel review.

## Pitfalls

- >4 reviewers increases cost/conflict without coverage gain
- each reviewer needs whole diff; fragments hide cross-file issues
- finding without `file:line` and existing-symbol evidence is noise
- cleanup scope = recent diff + minimal required surroundings; do not rewrite module
- genuine correctness bug is a separate prominent finding, not cleanup change
- altitude deeper fix is flagged, not unilaterally implemented
- honor AGENTS/CLAUDE/HERMES/linter conventions
- large diff should be scoped before delegation
- `knip`/`ts-prune`/`depcheck` miss dynamic uses; search symbol before removal
- public exports/routes/DB/config names are contracts; rename = RISKY
- intentional empty catches/error handling are flagged, not removed
- compat/staged/vendored special cases need blame/context; low confidence if unclear

## Verification

- requested scope and diff source captured; empty/no-repo handled honestly
- four angles completed in parallel or all inline, with complete diff
- findings have concrete cost, evidence, confidence, and risk
- SAFE/CAREFUL changes only applied within scope; RISKY changes not auto-applied
- targeted tests + linter/typecheck pass after each applied file
- summary groups applied/skipped work and identifies genuine bugs separately

## Related

`subagent-driven-development` covers parallel review during implementation;
this skill is after-the-fact cleanup. `requesting-code-review` is the pre-commit
security/quality bug hunt; this skill improves already-working code.
