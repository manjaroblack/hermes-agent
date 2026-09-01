---
name: github-issue-to-pr
description: Carry a GitHub issue to a verified PR with honest CI state.
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Issues, Coding, Pull-Requests, CI]
    related_skills: [github-issues, github-pr-workflow, systematic-debugging, test-driven-development, requesting-code-review]
---

# GitHub Issue → Pull Request

role: issue-to-PR delivery owner
do: read live issue; sweep duplicates; validate premise/design intent; define acceptance; implement class-level fix; prove regression; run gates; open/shepherd PR
inputs: issue number/URL, current repository, contributor rules, credentials, acceptance contract
outputs: isolated tested branch + PR, live CI state, issue-thread resolution note
¬: code before thread/current-code read; fight intentional design; fix one sibling only; claim green/merged/released without live evidence

Sibling GitHub/development skills own connector mechanics; this skill owns
end-to-end discipline, premise validation, duplicate sweeps, class-level fixes,
and honest CI reporting.

## When to Use

- fix issue `#123` and open a PR
- implement a GitHub feature request
- carry a bug from issue report to green CI

¬use for existing-PR review or code questions without a requested change.

## Procedure

### 1. Read live issue + repository rules

Run `gh issue view <N> --comments` via `terminal`; read body and full thread.
Newest comments may contain merged fixes, root-cause analysis, maintainer
decisions, or unanswered questions. Read `AGENTS.md` and contribution docs with
`read_file`. Record requested behavior, non-goals, and open questions.
Done when: live issue state, repository rules, scope, and non-goals are recorded.

### 2. Sweep duplicate work

Run `gh pr list --search "#<N>" --state all`, at least two symptom
keyword/synonym searches such as `gh pr list --search "<subsystem> <symptom>" --state open`,
and `git log --oneline -20 -- <relevant files>`. Record all open PRs and recent
commits or explicit absence; preserve contributor credit rather than duplicating.
Done when: issue-number and symptom/synonym sweeps have recorded results.

### 3. Validate premise and intent

On the current default branch, reproduce the bug or demonstrate the missing
behavior with a failing test/fixture. Trace with `search_files` + `read_file`.
Run `git log -p -S "<symbol>"` and read the introducing commit: apparent gaps
or restrictions may be deliberate. Proceed only when current code demonstrates
the defect and the proposed change does not fight design intent.
Done when: current code reproduces the defect and history supports the change.

### 4. Define finite acceptance

Record behavior criteria, interfaces, migrations/state, compatibility,
security/privacy, rollout/rollback. Map every criterion to a test or explicit
verification.
Done when: every acceptance criterion maps to a test or explicit check.

### 5. Implement smallest complete class-level fix

Use isolated branch/worktree; load `systematic-debugging` or
`test-driven-development` as appropriate. Write regression tests first, then
implement. Search sibling call sites for the same bug shape; fix them or
explicitly rule them out. No drive-by cleanup. Done = targeted tests pass,
original failure is gone, sibling scope is accounted for.
Done when: smallest class-level fix and affected sibling call paths are covered.

### 6. Prove regression test bites

Temporarily restore the old behavior of the exact function; run the new test and
confirm failure; restore fix and confirm pass. A test passing both ways is not a
regression test.
Done when: the old behavior makes the regression test FAILS, then the fix passes.

### 7. Run gates + open PR

Run formatter, lint, typecheck, canonical affected tests, and
`requesting-code-review` on the diff. Load `github-pr-workflow`; push/open the PR
immediately so CI starts. Body must link issue and state problem, approach,
tests, risk, exclusions. Read PR back; verify base/head SHA, title, and files.
Opening the PR immediately dispatches CI while the implementation context is fresh.
Done when: PR is open with issue link, exact files/base/head, tests, and risk.

### 8. Shepherd CI + close loop

Use `gh pr checks` and `gh run view --log-failed`. Separate diff failures from
baseline/infrastructure; reproduce on default branch when uncertain; rerun once
only for a real infrastructure flake. Never claim green/merged/released without
live exact-state evidence. After merge, comment the issue with PR link + one-line
resolution.
Done when: live CI state is reported and the issue receives the PR resolution link.

## Pitfalls

- coding before thread, duplicate sweep, or current-code inspection
- changing behavior that history proves intentional
- symptom-only fix with known siblings unfixed
- regression test passes without the fix
- unrun tests or unrelated formatting churn in PR
- PR existence != delivered issue

## Verification

- [ ] full issue thread read; newest state reflected
- [ ] issue-number + two keyword duplicate searches run
- [ ] premise reproduced; design intent checked with history
- [ ] regression test fails on old behavior and passes on fix
- [ ] sibling sites fixed or explicitly ruled out
- [ ] every changed line traces to issue
- [ ] live CI state reported honestly; issue gets PR resolution comment