---
name: sdlc-review
description: Review Kanban handoffs and route verified outcomes.
version: 1.1.0
author: Jakub Wolniewicz (@frizikk) + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, review, quality, verification]
    category: devops
    requires_toolsets: [kanban]
environments:
  - kanban
---

# SDLC Review Skill

role: independent Kanban review worker
do: inspect implementation/evidence; map acceptance criteria; run relevant checks; approve, request changes, or escalate
inputs: task body, acceptance criteria, handoff, workspace/deliverable, prior review history
outputs: one evidence-backed verdict through the Kanban lifecycle
¬: take over implementation; edit deliverable; rubber-stamp summary; use blocker for ordinary rework

## When to Use

Use iff all hold:

- dispatcher spawned this run from the `review` lane
- implementer submitted a `review_requested` handoff
- independent verdict is required before completion

¬use for a separate downstream review card: that card is ordinary scoped work
with review-oriented acceptance criteria and its own lifecycle.

## Prerequisites

- current Kanban worker context/task/run identifiers
- native tools: `kanban_show`, `kanban_comment`, `kanban_complete`,
  `kanban_request_changes`, `kanban_block`
- code workspace access via `read_file`, `search_files`, `terminal`
- original specification, acceptance criteria, handoff, and prior runs via
  `kanban_show`

## How to Run

1. Call `kanban_show`; inspect the complete task, handoff, prior attempts,
   comments, and child cards.
2. Inspect changed files with `read_file`/`search_files`; run focused checks via
   `terminal` where the artifact permits.
3. Record concrete evidence, then select exactly one terminal lifecycle action.
Done when: the verdict is independently reproducible from task state and checks.

## Quick Reference

| Verdict | When | Final action |
|---|---|---|
| Approve | Acceptance criteria and verification pass | `kanban_complete` |
| Request changes | Correctable implementation defects remain | `kanban_comment`, then `kanban_request_changes` |
| Escalate | A human decision or external prerequisite is required | `kanban_block` |

A requested-changes transition returns the task to its original implementer.
When that implementer requests review again without naming a reviewer, persisted
reviewer provenance routes the re-review to the same reviewer profile.

## Review Lenses

Current round = count `changes_requested` entries in prior attempts + 1.
Baseline procedure remains required every round. Read Prior attempts on this task
from the durable context; never infer the round from memory.

| Round | Lens | How to apply it |
|---|---|---|
| 1 | Artifact | Read the diff or deliverable cold, before the implementer's summary. Form an independent judgment, then compare it against the handoff narrative and investigate every mismatch. |
| 2 | Execution | Check out the work and actually run it via `terminal`: build, test, and exercise the reported behavior yourself. Verify each handoff claim empirically instead of re-reading the artifact. |
| 3+ | Contract | Re-read the ORIGINAL task body and acceptance criteria, then audit the deliverable strictly against them. Also verify that every item from every prior `kanban_request_changes` round actually landed. |

For ad-hoc `delegate_task` review fan-outs, assign distinct lenses (diff-only,
full-context, checkout-and-run); identical briefs yield correlated findings.

## Procedure

### 1. Orient from durable state

Call `kanban_show` first. Extract original criteria; latest summary/metadata;
changed paths, commit IDs, and tests; comments/decisions; prior findings.
Treat handoff claims as hypotheses, not proof.

### 2. Map request to deliverable

For each acceptance criterion identify concrete implementation/output evidence;
record omissions, semantic changes, and unrelated scope.

Code path:

1. Inspect changed files and callers with `read_file` + `search_files`.
2. Inspect diff and run focused tests, lint, type checks, or build via
   `terminal`.
3. Exercise reported failure path plus an ordinary control path when practical.
4. Check errors, edge cases, concurrency, data preservation, security,
   cross-platform behavior.
5. Reject tests that only snapshot source text or changeable constants.

Non-code path: inspect the complete artifact; check correctness, completeness,
format/provenance; validate material external references with native tools.

### 3. Choose exactly one verdict

Approve iff criteria + evidence pass:

```text
kanban_complete(
    summary="Reviewed and approved. <what was verified>",
    metadata={"review_outcome": "approved", "reviewer_checks": [...]}
)
```

Include exact passing checks and bounded non-blocking caveats.

Correctable defect → record actionable findings, then return the same card:

```text
kanban_comment(
    task_id="<current-task-id>",
    body="Changes requested:\n1. <file or artifact + defect>\n2. <required correction>",
)
```

```text
kanban_request_changes(
    reason="<concise summary of the required corrections>"
)
```

State location, reproduction, violated criterion, and minimum correction.

Human decision/external prerequisite only → escalate:

```text
kanban_block(
    reason="escalation: <decision or prerequisite required>"
)
```

State the smallest missing input. Requested changes do not use blocker
recurrence accounting.

## Role Boundary

Do not edit implementation while reviewing. Return defects to the implementer;
re-review the next candidate independently. A downstream child review is not a
reason to request same-card review.

## Pitfalls

- passing handoff summary != independent evidence
- reviewer edits hide ownership and weaken re-review
- vague findings give no reproducible correction target
- style-only preference != blocking defect
- skipping earlier-round corrections risks regression
- ordinary rework → `kanban_request_changes`; `kanban_block` only external/human
- approval without named checks/artifacts is unsupported

## Verification

- [ ] `kanban_show` read for current task/run
- [ ] every criterion mapped to evidence
- [ ] complete deliverable inspected
- [ ] focused checks run, or execution impossibility recorded
- [ ] prior requested changes re-tested
- [ ] unrelated regressions/scope considered
- [ ] exactly one terminal lifecycle action selected
- [ ] summary contains concrete non-secret evidence
- [ ] reviewer edited no implementation files