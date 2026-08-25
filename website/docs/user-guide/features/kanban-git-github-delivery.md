---
sidebar_position: 13
title: "Kanban Git/GitHub delivery lifecycle"
description: "Guarded Git and GitHub merge lifecycle for Kanban delivery tasks"
---

# Guarded Git/GitHub delivery

The delivery coordinator is an explicit, opt-in workflow for moving one Kanban
implementation through a fork-local Git/GitHub change. Its merge boundary is
policy-driven: Tier A allow-listed fork-local changes may be authorized by the
durable automated policy after exact-head review/check evidence, Tier B changes
need additional automated evidence, and Tier C/protected or unknown scopes
escalate to an attributable human operator or approved external controller.
The worker never authorizes its own merge, and a runtime cutover remains an
externally authorized handoff.

This page is the operator and reviewer contract. The durable delivery record,
not chat history or a worker's claim, is the source of truth.

## State machine

A delivery starts at `intake`. Transitions are explicit; there is no generic
state setter and no transition may skip an authorization or verification gate.

```text
intake
  ├─ upstream_sync_pending
  │    ├─ upstream_sync_not_required / upstream_sync_verified
  │    └─ upstream_sync_review_pending
  │           → upstream_sync_ci_green
  │           → upstream_sync_authorization_pending
  │           → upstream_sync_verified → workspace_admitted
  └─ upstream_sync_not_required → workspace_admitted

workspace_admitted → worktree_ready → editing → validated → committed
  → fork_pushed → fork_pr_open → fork_review_pending → fork_ci_green
  → merge_authorization_pending → fork_merge_verified
  → completed                         (fork-only target)

fork_merge_verified → runtime_cutover_pending → rollback_pack_ready
  → runtime_materialized → activation_pending → activation_verified
  → completed                         (external runtime target)
```

The following are recovery or terminal states:

- `blocked` — a required gate, dependency, identity, provider read-back, or
  external input is unavailable. It can return to the safe prior work phase
  after the problem is resolved.
- `needs_input` — the coordinator needs an operator decision or missing
  information. Supply it through the durable operator surface, then resume.
- `aborted` — terminal stop. Abort does not delete, rewrite, force-push, or
  otherwise mutate external refs.
- `completed` — terminal success after the applicable merge or activation
  verification.

Every normal phase may also transition to `blocked` or `aborted`. A completed
or aborted delivery is not resumed by changing its state; start a new, linked
card if additional work is needed.

### What each phase proves

| State or transition | Required evidence or effect |
|---|---|
| `intake` → workspace admission | Repository identity, target policy, remotes, and base are validated. |
| Upstream sync states | The `upstream` remote is fetch-only. A changed upstream base gets its own fork-local sync branch, PR, independent review/check packet, and explicit sync authorization before admission. If already at the configured base, admission can be recorded without a sync PR. |
| `workspace_admitted` → `committed` | A designated worktree is prepared, edits are validated, and one clean attributed commit is recorded. |
| `committed` → `fork_pr_open` | The configured fork ref is pushed and exactly one open, non-draft PR with the expected repository, branch, base, and head SHA is read back. |
| `fork_pr_open` → `fork_ci_green` | The GitHub provider re-reads required checks for the recorded head SHA, an independent approval for that exact head, and live base-branch protection. The submitted packet is an immutable identity/audit record, not the authority for those gates. Green CI alone is not approval. |
| `fork_ci_green` → `merge_authorization_pending` | The configured risk classifier records its tier, changed paths, protected-path rules, policy identity, exact-head review/check evidence, rollback artifact, and reason. Tier A may auto-authorize; Tier B additionally requires configured evidence; Tier C requires attributable human authorization. |
| `merge_authorization_pending` → `fork_merge_verified` | The provider confirms the merge and a read-back confirms merged state plus a merge commit SHA. An ambiguous provider response is never retried blindly. |
| `fork_merge_verified` → `completed` | For `fork_only`, permitted cleanup is complete or intentionally omitted, then the delivery is finalized. |
| Runtime target states | Runtime release authorization, rollback pack, external materialization evidence, and independent live identity/health evidence are recorded. Hermes records and verifies these handoffs; it does not perform the runtime cutover. |

## Risk-tiered authorization contract

Merge authorization is a safety boundary, not a review status. Every automated
decision records the classifier inputs and policy identity. The default policy
is configured under `kanban.delivery.risk_policy` in `config.yaml`; operators
should review the path globs before enabling autonomous delivery.

### Tier A — autonomous fork-local scope

Tier A requires all changed paths to match the explicit allow-list, no protected
path match, an open/non-draft PR read back at the exact head/base identity,
green required checks fetched for that exact head, live branch protection, and an
independent approval from a different model family. The merge request itself is
also pinned to the recorded head SHA; a moved head fails closed. The durable
authorization also records a rollback artifact (normally the immutable Git
parent/head/scope tuple). No chat message, packet-only check result, silence, or
review label is sufficient by itself.

### Tier B — additional evidence

Dependency, packaging, lockfile, runtime-sensitive, or broader allow-listed
changes are Tier B. The configured `required_tier_b_evidence` keys must be
recorded by an attributable policy/controller actor with `record-risk-evidence`
before merge. The default keys cover a security scan, staged health evidence,
and a rollback artifact. Missing, stale, or failed evidence escalates instead
of bypassing the gate.

### Tier C — human escalation

Protected paths (including gateway/auth/security/deployment/credential-like,
core tool-boundary, and prompt-cache paths), unknown scopes, invalid paths, and
denied policy decisions are Tier C. The default allow-list is intentionally
narrow and does not allow arbitrary Python files; protected-path matching takes
precedence over any allow-list match.
The attempted merge records the classifier inputs, protected rules, automated
evidence seen, rollback context, policy identity, and escalation reason. A
human may then use `authorize-merge` with explicit confirmation; the worker and
gateway cannot create that authorization.

All tiers additionally require the exact packet hash, configured merge method,
immutable repository/branch/base/head identity, attributable actor, reason,
confirmation, and unexpired authorization. A stale authorization for a
different head, packet, method, or PR is never reusable.

Gateway and delegated worker processes are not authorization boundaries: their
worker environment is checked before merge, automated authorization, or Tier B
risk-evidence writes. Those operations must run from the external operator CLI
or an approved controller.

The same contract applies to fork-local upstream synchronization. Runtime
cutover has a separate external release authorization and must also name the
verified merged commit.

## Commands and evidence

The human/controller surface is the `delivery` command family. These examples
use placeholders only; replace them with the task's actual values and never
put credentials in arguments, URLs, packets, logs, or comments.

```bash
hermes kanban delivery start <task-id> \
  --project-path /absolute/path/to/repository \
  --repository <fork-owner>/<fork-repository> \
  --target fork_only --method squash

hermes kanban delivery status <task-id> --json
hermes kanban delivery controller --task <task-id> --once --json
hermes kanban delivery validate <task-id> --tree-sha <40-char-sha> \
  --command "<validation command>" --command "<second validation command>"
hermes kanban delivery commit <task-id> "<attributed commit message>" \
  --path <changed-file> --path <second-changed-file>
hermes kanban delivery push <task-id>
hermes kanban delivery open-pr <task-id> --title "<title>" --body "<body>"
hermes kanban delivery request-review <task-id> --reviewer <independent-reviewer>
hermes kanban delivery record-review <task-id> \
  --packet /absolute/path/to/review-packet.json
hermes kanban delivery record-risk-evidence <task-id> \
  --actor <policy-controller> --evidence /absolute/path/to/risk-evidence.json
hermes kanban delivery authorize-merge <task-id> \
  --actor <authenticated-owner> --source operator_cli \
  --packet-hash <packet-hash> --method squash \
  --reason "<durable reason>" --confirm
hermes kanban delivery merge <task-id>
hermes kanban delivery cleanup <task-id> [--remove-worktree] \
  [--delete-remote-branch]
```

For a `fork_with_upstream_sync` target, use the fetch-only and fork-local
sequence before the ordinary workspace/PR sequence:

```bash
hermes kanban delivery sync-upstream <task-id> --source upstream/main
hermes kanban delivery record-upstream-review <task-id> \
  --packet /absolute/path/to/upstream-review-packet.json
hermes kanban delivery authorize-upstream-sync <task-id> \
  --actor <authenticated-owner> --packet-hash <packet-hash> \
  --method squash --confirm
hermes kanban delivery merge-upstream-sync <task-id>
```

For a runtime-target delivery, the release controller owns the external
cutover and supplies these durable handoff records; Hermes does not execute
the cutover itself:

```bash
hermes kanban delivery authorize-cutover <task-id> \
  --actor <release-owner> --runtime-remote <runtime-remote> \
  --runtime-branch <runtime-branch> --approved-merge-sha <40-char-sha> \
  --confirm
hermes kanban delivery prepare-cutover <task-id> \
  --output /absolute/path/to/rollback-pack
hermes kanban delivery mark-materialized <task-id> \
  --before-sha <40-char-sha> --after-sha <40-char-sha> \
  --main-pid <positive-pid> --service-interpreter <identity>
hermes kanban delivery verify-cutover <task-id> \
  --evidence /absolute/path/to/live-identity.json
```

The command output and durable events should make the following evidence
available to a reviewer or later recovery run:

- task id and delivery state;
- repository URL/name and remote role (`origin` fork versus `upstream`);
- PR URL and number;
- branch and base branch;
- immutable head SHA and base SHA;
- review packet hash, reviewer actor, model family, check results, branch-protection result, and timestamps;
- risk tier, classifier inputs/changed paths, protected path rules, policy identity,
  automated evidence, escalation reason, and rollback-artifact reference;
- authorization event id, actor, source, method, reason, confirmation, expiry,
  and timestamp;
- merge commit SHA, provider actor, and provider read-back timestamp;
- for runtime handoff: approved merge SHA, runtime remote/branch, rollback-pack
  path and SHA-256, before/after SHAs, process/interpreter identity, and health
  evidence.

A review packet is an evidence object, not a secret container. Keep it bounded,
referential, and reproducible. Do not include access tokens, cookies,
passwords, private keys, embedded credentials in remote URLs, or raw secret
values. Credential-shaped values are rejected or redacted by the coordinator;
operators should remove them at the source rather than relying on redaction.

## Fail-closed gates

Stop and leave the delivery blocked when any identity or evidence is missing,
stale, ambiguous, or inconsistent. In particular:

- closed, draft, unknown, or unavailable PR state is not acceptable;
- a PR with a different repository, branch, base, or exact head is a conflict;
- pending, failed, missing, or non-exact-head checks are not green;
- packet-only checks, review fields, or branch-protection flags are never used
  when the live provider evidence is unavailable;
- a review by the implementer is not independent;
- an actor that cannot be matched to authenticated provider identity cannot
  authorize;
- an expired authorization cannot be reused;
- a provider timeout or uncertain response requires read-back before retry;
- a worktree with a live task claim cannot be removed;
- a worktree path that is not the canonical delivery worktree cannot be
  removed;
- a runtime evidence file that is unreadable, incomplete, unhealthy, or names
  the wrong merged SHA cannot verify activation.

Do not weaken a gate to make a delivery advance. Record the diagnostic in the
same task and ask an operator to resolve the specific failure.

## Recovery, retry, and rollback

### Safe retry

`status` and `resume` are safe diagnostic/recovery operations. External effects
are idempotency-keyed. When an effect is `started` or `ambiguous`, the next
attempt reads the provider first and only records the already-applied result;
it does not issue a second PR creation, merge, or cleanup effect. Retry only
after the provider read-back is authoritative.

A changed implementation or changed review feedback is not a retry of the old
head. Use same-card rework, clear the old review/check and merge authorization
through the coordinator, create a new commit, and obtain a new exact-head
review packet. Never reuse an old packet hash or authorization.

### Same-card rework

A reviewer may request changes on the same delivery card. The card returns to
`editing` while preserving its delivery identity, but review/check snapshots,
scope hash, and merge authorization are cleared. The implementer creates a new
head, validates it, and repeats PR review and authorization. Normal review
feedback is not a `blocked` escalation.

If independent cards produce stacked PRs or collide, do not silently rewrite a
peer's branch. Preserve the branch identities and create a neutral
reconciliation card with both cards as parents. The reconciler resolves and
verifies the combined result; it does not self-authorize the eventual merge.

### Conflicts and CI

A merge conflict, changed base, changed head, or failed check invalidates the
current evidence. Stop, record the conflict, rebase or reconcile in a fresh
work phase, and repeat validation and independent review. A provider's
"retrying CI" or a pending check is not true green; record green only after the
exact-head check run is complete and successful.

Closed, draft, foreign, or diverged PRs are not repaired by changing the
recorded URL or number. Block and obtain a fresh provider-verified PR identity.

### Abort and rollback

To stop without external mutation:

```bash
hermes kanban delivery abort <task-id> \
  --reason "<durable, non-secret reason>"
```

Abort is fail-safe: it does not delete branches, remove worktrees, rewrite
history, force-push, or undo a provider merge. If a merge has already been
confirmed, rollback is an explicitly authorized follow-up operation owned by
the runtime or release controller. For a runtime-target delivery, prepare the
rollback pack before external materialization and retain its manifest and
SHA-256. Hermes records the handoff and verification; it does not restart a
gateway, deploy, or mutate production.

## Remotes, branches, and cleanup

- `origin` is the configured fork used for delivery. `upstream` is read-only
  and may be used only by the fetch-only upstream synchronization phase.
- Never push to upstream as part of this lifecycle. A fork-local sync PR is the
  only merge path for admitting upstream changes.
- Preserve the immutable repository, PR, branch, base, and SHA identity in every
  handoff. Do not silently retarget a foreign or changed PR.
- Worktrees and branches are preserved until provider-confirmed merge and
  explicit cleanup. Cleanup is optional and separately recorded.
- Removing a worktree requires no live Kanban claim and an exact canonical
  worktree path. Remote branch deletion is opt-in; it is never implied by
  merge or abort.
- Scratch workspaces follow normal Kanban scratch cleanup rules. A delivery
  that needs post-merge inspection must use a preserved `worktree` or `dir`
  workspace, not scratch.

## Compatibility and non-goals

Existing Kanban cards and legacy boards remain valid. This lifecycle is
additive and opt-in: do not auto-migrate cards, rewrite legacy task history,
or infer delivery records for old work. A normal worker can continue using
`kanban_complete`, same-card review, downstream review cards, and
`kanban_block` according to the worker-lane contract.

This lifecycle explicitly does not authorize or perform:

- deployment, runtime restart, gateway restart, or public exposure;
- production mutation or live service administration;
- upstream pushes or force-pushes;
- mutation of an unrelated or pre-existing PR;
- secret discovery, storage, or transmission.

For a safe operator decision, inspect `delivery status`, verify exact-head
review/check evidence, record attributable authorization through the CLI or
approved controller, then run the guarded effect and read back its result. To
abort safely, use `delivery abort`; do not manually delete or rewrite external
refs as a substitute for the durable abort record.
