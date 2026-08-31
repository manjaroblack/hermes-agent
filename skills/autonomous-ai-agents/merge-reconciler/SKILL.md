---
name: merge-reconciler
description: "Neutral third-party resolution of agent merge conflicts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Multi-Agent, Git, Merge-Conflict, Kanban, Arbitration]
    related_skills: [hermes-agent]
---

# Merge Reconciler

role: impartial third-party merge arbiter
do: resolve conflicts between two agent branches from both diffs + stated intents; retain every justified change
inputs: halted merge/rebase, branch names, both intent sources, project test/build command
outputs: conflict-free merge commit + explicit hunk decisions
¬: self-adjudicating one agent's own conflict; generated/lockfile conflicts that should be regenerated; drive-by edits

## When to Use

- parallel kanban engineering, multi-worktree refactor, or parallel PR branches collide
- `git merge`/`git rebase` halts and neither original agent should decide

Prefer a third profile. Agents resolving against a peer tend to overwrite the peer or abandon their own context.

## Prerequisites

- checkout containing halted merge, or both branch names + permission to merge
- both intent sources: kanban completion summaries (`terminal` running `hermes kanban show <task-id>`), PR bodies, or commit messages
- project build/test command

## How to Run

`delegate_task` prompt must include repo path, branch names, both intent summaries verbatim, and this skill. Preferred kanban shape:

```text
kanban_create(title="reconcile branch-a x branch-b", assignee="reconciler", parents=["t_a", "t_b"])
```

The third profile must not be either worker. Parent links carry completion summaries; card body names repo path + branches.

## Quick Reference

`git status`; `git merge-base <A> <B>`; `git diff <base>..<side> -- <file>`; `read_file` each conflict; `patch`/`write_file` conflict regions; `git add`; project build/tests; `git commit` only after both intents are represented.

## Hunk Classes

| Class | Meaning | Resolution |
|---|---|---|
| disjoint-intent | Different goals; coexist | Combine both |
| same-question-different-answer | One design question; answers differ | Pick ONE using stated intents; expose choice |
| superseded | One premise no longer holds after the other change | Keep surviving side; explain |

Impartiality contract: never favor spawning side; change only conflict regions; every design choice appears in hand-back summary.

## Procedure

### 1. Gather

- Run `terminal`: `git status`; confirm halted state + conflicted files.
- Run `git merge-base <A> <B>`.
- For each side: `git log --oneline <base>..<side>` and `git diff <base>..<side> -- <file>` for every conflict.
- In halted merge, `HEAD` is one side and `MERGE_HEAD` the other.
- Retrieve intent via `hermes kanban show <task-id>`, PR body, or commit messages. State one sentence per side before editing.
- Done iff both intents and both diffs for every conflicted file are available.

### 2. Classify

- Open each file with `read_file`; locate each `<<<<<<<`/`=======`/`>>>>>>>` block.
- Assign every hunk exactly one class; judge by intent, not aesthetics.
- Split a hunk into sub-decisions when it contains independent choices.
- Record class + one-line rationale per hunk.

### 3. Resolve

Use `patch` or `write_file` only for conflict regions:
- disjoint → merge both fully
- same question → choose answer best serving stated intent; never invent a hybrid
- superseded → remove dead premise, keep surviving side

If intents tie or are missing, escalate instead of guessing. `git add` each resolved file. Done iff `search_files` finds no `<<<<<<<` markers in repo and all resolved files are staged.

### 4. Verify + commit

Run project build/tests with `terminal`; import/execute touched modules at minimum. Confirm both intents are observable, or explicitly name the dropped one. Then `git commit` with default merge message plus hunk decisions. Done iff checks pass and merge commit exists.

### 5. Hand back

For every hunk report:

`file:lines — class — which side(s) kept — rationale`

For each same-question choice, name design question + chosen answer so a human can veto. Kanban: `kanban_complete(summary=...)`; standalone: print it.

## Pitfalls

- self-favoring: prefer third profile; deliberately weigh the other intent
- split-the-difference hybrids satisfy neither design
- per-file classification hides mixed hunk classes; classify per hunk
- drive-by edits make merge unreviewable
- missing intents require escalation, not guesses
- repeated conflicts on one path are a hotspot; add `hotspot: <path> — <reason>` kanban comment and ask orchestrator to decompose it

## Verification

- `git status`: clean target branch + merge commit
- `search_files` pattern `<<<<<<<`: no matches
- build/tests pass
- summary enumerates every hunk, class, rationale, and any intentionally dropped side
