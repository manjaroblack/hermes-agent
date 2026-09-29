# Plan: control-plane hardening A–F / P0–P2

## Goal

Produce a **design-only** revision of Hermes control-plane hardening (gateway hooks, fleet credentials, kanban state/leases, lifecycle correlation, test isolation) that can pass an independent security gate.

## Non-goals

- Do not implement A–F or P0–P2 in code.
- Do not waive the current security NO-GO.
- Do not restart the gateway, cut over runtime, merge, or change live listeners/firewall.
- Do not inspect or print credentials.

## Current verdict

Latest independent security gate: **NO-GO**. `implementation_authorized=false`. Empty approved command set.

Known blockers (must be closed in a new hashed design packet, not in a drive-by patch):

1. Event and request intent are not mutually hash-bound.
2. Overlap verifier omits `issued_at >= not_before`.
3. Strict T0/T1 tool / action-class boundary is unclosed.
4. Human exposure disposition for all-interface listeners is missing (owner/firewall decision, not Cursor).
5. Command/probe set is not fully executable and hash-bound.
6. Earlier gates also cited privileged-credential equivalence and sealed-FD/gateway contracts that pulled excluded paths (`hermes_cli/_parser.py`, `hermes_cli/main.py`, `gateway/run.py`).

## Design

Keep work on a feature branch from `local/runtime`. Output is a design packet markdown file plus tests **described**, not landed, until GO.

Suggested packet sections:

- Exact path allowlist (no excluded god-files unless the new design proves they are required)
- Hash-bound request ↔ event contract
- Overlap-key issuance cutoff
- Zero-credential bootstrap (explicit, no inference)
- Test plan using `scripts/run_tests.sh` against a temp `HERMES_HOME`
- Rollback: drop the branch; never cut over

## Tasks

1. Read root `AGENTS.md`, `cron/AGENTS.md`, `gateway/AGENTS.md`, `hermes_cli/AGENTS.md`.
2. Read the three open overlay PRs so the design does not fight in-flight kanban work.
3. Write `docs/plans/control-plane-hardening-packet.md` on this branch covering each blocker above with exact paths/symbols.
4. List the tests that would prove each blocker closed. Do not add the tests until GO.
5. Open a **docs-only** PR against `local/runtime`. Do not merge.

## Tests

None until GO. After a named GO: `scripts/run_tests.sh` on the named suites, never bare `pytest`.

## Risks / rollback

Implementing against a NO-GO would ship fail-open control-plane changes onto a live agent. Rollback is “do not merge / do not cut over.”

## Acceptance

- Packet names every current blocker and a concrete close condition.
- PR is docs-only against `local/runtime`.
- No runtime files changed.
- Owner still names any later implementation GO, merge, and cutover.

## Stop

If the work requires host listener/firewall changes or editing excluded parser/gateway facades, stop and ask the owner.
