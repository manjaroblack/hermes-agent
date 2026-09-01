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

Review recent code changes with four focused reviewers in parallel; aggregate
findings; apply only justified fixes. This is cleanup of already-working code:
remove duplication/complexity/waste and deepen band-aids; correctness bug hunting
belongs to `requesting-code-review`.

Core principle: four narrow reviewers beat one broad reviewer. Each searches one
problem class — reuse, quality, efficiency, altitude — without diluted attention;
concurrency costs one review's latency, not four.

## When to Use

Triggers:

- "simplify" / "simplify my changes" / "simplify these changes"
- "review my code" / "review my recent changes" / "clean up my changes"
- `/simplify` (Claude Code habit)

Honor modifiers:

- Focus: "simplify focus on efficiency" → run only or weight `efficiency`;
  recognized: `reuse`, `quality`/`simplification`, `efficiency`, `altitude`.
- Dry run: "simplify but don't change anything" / "just report" → run all four,
  present findings, apply NOTHING; ask before applying.
- Scope: "simplify the last commit" / "simplify staged" / "simplify src/foo.py"
  → narrow diff source (Phase 1).

¬ auto-run after every edit or append to unrelated tasks; four subagents cost
real tokens; invoke only on explicit request.

## Prerequisites

- git repo + recent changes or explicitly named/recent files
- `terminal`, `read_file`, `search_files`; `delegate_task` when available
- targeted project tests/lint/typecheck commands
- user intent for scope/focus; no credentials

## The Process

### Phase 1 — Identify the changes

Capture the complete diff and choose source by request:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If empty, include staged changes
git diff HEAD

# 3. Scoped variants
git diff --staged                 # "staged changes"
git diff HEAD~1                   # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If `git diff` and `git diff HEAD` are empty and there is no repo/no change, use
files explicitly named or recently created/edited this session; otherwise state
there is nothing to simplify and stop. Record diff size. >2000 changed lines →
warn: four full diff copies are token-heavy; offer per-directory/per-commit scope.

### Phase 2 — Launch four reviewers in parallel

Use `delegate_task` batch mode with all four tasks in one `tasks` array; four is
within `delegation.max_concurrent_children` on default installs. If unavailable
(leaf, disabled, budget exhausted), work all four angles sequentially inline; do
not skip angles, and state in summary that review was inline, not fan-out.

Give every reviewer the complete diff (not fragments), absolute repo path, and
`terminal`, `file`, `search` toolsets (`git`, `read_file`, `search_files`/grep).
Require:

- existing-code search, not diff-only reasoning
- `git blame` before removal (Chesterton's Fence); unclear purpose →
  `confidence: low`, never guess
- structured finding:

  ```
  file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
  ```

Cost is mandatory: a finding with no concrete cost is likely a nit. Skip
style-only churn. Risk:

- SAFE = proven behavior-neutral (unused imports, commented code, pass-through
  wrappers, redundant assertions) → auto-apply
- CAREFUL = semantic-preserving (local rename, flatten, extract, consolidate)
  → one file at a time + tests
- RISKY = behavior/public-contract/memory-lifecycle/concurrency impact → human
  review; no auto-apply

Reviewer 1 — Code Reuse:
search utility/shared-helper/adjacent files for duplicate functions, constants,
or patterns; hand-rolled string/path/env checks, type guards, or parsing. Name
the existing symbol and location.

Reviewer 2 — Code Quality:
inspect redundant/derivable state and needless caches; parameter sprawl;
copy-paste variation; leaky abstractions; raw strings against canonical
constant/enum/registry; 3+ level conditionals. Flag AI slop (`as any`, comments
restating code such as `// increment counter` above `count++`, unnecessary null
checks, inconsistent patterns). Check 3+ level `if/else` pyramids. Give concrete
refactor.

Reviewer 3 — Efficiency:
inspect repeated computation/file reads/API calls/N+1; missed concurrency;
startup/per-request `heavy/blocking` hot-path work; TOCTOU pre-checks; unbounded memory,
missing cleanup, listener/handle leaks; long-lived closures capturing whole
scope (prefer small class or explicit-fields struct); broad reads; silent
failures (`except: pass`, empty catches, ignored returns, `.catch(() => {})`,
error-propagation gaps). Give faster/safer fix and rationale.

Reviewer 4 — Altitude:
find call-site band-aids over shared infrastructure: special cases such as
`if (caller == X)`, type checks, magic escapes; sibling symptom patches; stacked workarounds; wrappers
avoiding needed change; flags/config routing around broken defaults. Read context
and blame; identify deeper fix or separate task. Do not flag deliberate compat
shims, staged migrations, or vendored isolation.

### Phase 3 — Aggregate and apply

Wait for all four (batch returns together), then:

1. Merge findings; dedupe same line/mechanism.
2. Discard weak/false positives; no obligation to argue with reviewer.
3. Resolve conflicts: correctness > stated focus > readability/reuse > micro-perf;
   prefer less code when equally defensible and note alternatives. Do not trade
   clarity for perf unless path is genuinely hot.
4. Apply risk order:
   - SAFE: unused imports/comments/pass-through/redundant assertions; test.
   - CAREFUL: locals/ternaries/helpers/dupes, one file at a time; test each,
     revert breakage.
   - RISKY: N+1/public API/concurrency/error-handling/altitude; report with risk
     and coverage, never auto-apply; let user choose deeper fix vs follow-up.
   - dry run: present all tiers, apply none.
5. Run touched-file tests plus project lint/typecheck; revert any fix that breaks.
6. Summarize applied fixes by reviewer/risk, skipped findings + reasons, and
   inline-vs-parallel mode.

## Pitfalls

- ¬ >4 reviewers; cost/conflict rises without coverage
- whole diff required; fragments hide cross-file duplication/N+1
- reuse finding without `file:line` existing-symbol evidence = noise
- cleanup scope = recent diff + minimal surroundings, not module rewrite
- correctness bug = prominent separate finding, not cleanup change
- altitude deep fix = flag, don't unilaterally implement
- honor AGENTS/CLAUDE/HERMES/linter conventions
- scope large diff before delegation; 5000-line copies may truncate
- `knip`/`ts-prune`/`depcheck` miss dynamic uses; search symbol before removal
- public exports/routes/DB columns/config keys are contracts; rename = RISKY
- intentional empty catches/error handling are flagged, not removed
- compat/staged/vendored special cases need blame/context; uncertainty → low confidence

## Verification

- [ ] requested scope and diff source captured; empty/no-repo handled honestly
- [ ] four angles completed in parallel or all inline, with complete diff
- [ ] findings include cost, evidence, confidence, risk
- [ ] SAFE/CAREFUL changes remain in scope; RISKY changes not auto-applied
- [ ] targeted tests + linter/typecheck pass after each applied file
- [ ] summary groups applied/skipped work and isolates genuine bugs

## Related

If installed, optional `subagent-driven-development` covers parallel review
during implementation, per task. This skill is standalone after-the-fact cleanup.
Use `requesting-code-review` for the pre-commit security/quality bug hunt; this
skill improves already-working code.
