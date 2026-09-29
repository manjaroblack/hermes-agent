# Plan: finish or tidy open overlay PRs

## Goal

Make the three open house PRs reviewable: either leave a precise next-diff on each branch, or recommend close as superseded. Do not merge.

## Non-goals

- No GitHub merge.
- No rebase onto `main` (that is the Nous mirror). If rebase is needed, rebase onto current `local/runtime`.
- No Nous PRs.
- No gateway restart.

## Current PRs

1. [#10](https://github.com/manjaroblack/hermes-agent/pull/10) bounded GitHub delivery controller — **conflicting**. First job: rebase onto `local/runtime` or close if a later overlay already covers it. Prove with `git fetch` + live PR files, not memory.
2. [#7](https://github.com/manjaroblack/hermes-agent/pull/7) complex task-graph validation — mergeable. Address review comments only. Add invariant tests via `scripts/run_tests.sh`.
3. [#5](https://github.com/manjaroblack/hermes-agent/pull/5) web / ui-tui npm advisories — mergeable. Confirm advisories still exist on current `local/runtime`. If already cleared, recommend close.

## Tasks

1. `gh pr view` each PR; record head, base, mergeable, checks.
2. Diff against current `local/runtime`.
3. One bounded follow-up commit per PR that still has a real gap, or a PR comment recommending close with evidence.
4. Run focused tests with `scripts/run_tests.sh`.
5. Stop. Owner names merge.

## Tests

- Kanban/graph: tests under `tests/` that cover the PR’s claimed invariant, run through `scripts/run_tests.sh`.
- Deps: `npm audit` (or repo equivalent) on `web/` and `ui-tui/` after the advisory fix.

## Risks / rollback

A conflicted rebase can drop later `local/runtime` fixes. Prefer rebase onto `local/runtime`, then `git diff` against that base. Never squash-merge from a stale branch (see root `AGENTS.md`).

## Acceptance

Each PR has either a green exact-head check plus a written “ready for owner merge” note, or a written close recommendation with evidence. No merge from Cursor.

## Stop

Conflict that would require rewriting unrelated overlay history, or any need to change live gateway config.
