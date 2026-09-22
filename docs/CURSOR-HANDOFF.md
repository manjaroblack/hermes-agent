# Cursor handoff — manjaroblack/hermes-agent

GitHub is the queue. Hermes kanban is not.

This is the **house fork**, not upstream Nous. Cursor does overlay/product coding on this repo. Hermes remains the live control plane.

## Clone this

- Repo: `manjaroblack/hermes-agent`
- Start from branch **`local/runtime`** (what actually runs). `main` is a fast-forward mirror of Nous `upstream/main`. Do not land house docs or overlays on `main`.
- Do **not** edit the live Unraid checkout `/root/.hermes/hermes-agent`. Clone GitHub.
- GitHub **issues are disabled** on this fork. Use the plan files under `docs/plans/` and open PRs. Do not ask to enable issues unless the owner says so.

Connect the Cursor GitHub app. Kickoff: `@cursor` on a PR, or a Cloud Agent against `local/runtime`.

Upstream `AGENTS.md` at the repo root is the coding guide. Also read the area `AGENTS.md` in the routing table. House constraints are in `.cursor/rules/house.mdc`.

## Open PRs (do not merge)

| PR | Title | Notes |
| --- | --- | --- |
| [#10](https://github.com/manjaroblack/hermes-agent/pull/10) | feat(kanban): add bounded GitHub delivery controller | OPEN, **conflicting**. Continue or close; do not merge. |
| [#7](https://github.com/manjaroblack/hermes-agent/pull/7) | feat(kanban): validate complex task graphs | OPEN, mergeable. Continue review comments only. Do not merge. |
| [#5](https://github.com/manjaroblack/hermes-agent/pull/5) | fix(deps): clear web and ui-tui npm advisories | OPEN, mergeable. Continue review comments only. Do not merge. |

See `docs/plans/open-overlay-prs.md`.

## Remaining workstreams

1. **Open overlay PRs** — `docs/plans/open-overlay-prs.md`
2. **Control-plane hardening A–F / P0–P2** — `docs/plans/control-plane-hardening.md`  
   Security gate is **NO-GO**. Do not implement. Design/docs only until the owner names a fresh GO.
3. **Nous sync / prune / live cutover** — not Cursor. External owner shell only. See house rule: never restart the gateway.

## Stays on Hermes (not Cursor)

- Live gateway restart, cutover, `hermes update` on the Unraid host
- LCARS / Unraid / firewall / listener exposure
- Applying security packets
- PRs to `NousResearch/hermes-agent` unless the owner names that
- LifeOS cron apply, profile SOUL overlays, reading-log host packets

## Stop

Stop for merge, deploy, gateway restart, live cutover, Nous PRs, or any work that mutates the running host.
