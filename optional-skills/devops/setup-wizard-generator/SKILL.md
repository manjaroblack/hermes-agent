---
name: setup-wizard-generator
description: "Generate a bash wizard guiding a human through manual setup."
version: 1.0.0
author: "Matt Pocock (mattpocock/skills, wizard) + Hermes Agent"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wizard, setup, onboarding, credentials, secrets, migration, bash, human-in-the-loop]
    related_skills: []
---

# Setup Wizard Generator

role: manual-setup wizard author
do: inspect repo; map human-only stages; author staged bash wizard; validate statically; hand off run path
inputs: setup/migration procedure; URLs; captured values; destinations; secret/public status
outputs: ordered wizard script; bash/shellcheck result; value-destination trace
¬: use wizard for agent-executable steps; invent UI paths; expose secrets; run wizard end-to-end; hand-edit library above `STAGES`

Generates an interactive bash **wizard** for a human-only procedure. It opens
URLs, states clicks/copies, captures values, writes destinations (`.env`,
GitHub secrets), confirms stages, and reports remaining stages.

Ported from mattpocock/skills' MIT-licensed `wizard` skill.

## When to Use

- infrastructure/third-party provisioning (Stripe, Supabase, DNS, OAuth apps)
  where only a human can navigate the dashboard
- credentials, CI secrets, or repo variables
- one-off migrations/cutovers with irreversible human-gated steps
- any procedure the user will hand to a teammate

Do NOT use for agent-executable steps; perform those directly.

## Prerequisites

- `bash`; `gh` only when stages write GitHub secrets/variables
- library template: `templates/template.sh` in this skill directory

## Procedure

### 1. Scope the procedure

Identify every manual step and captured value. Read the repo first; do not ask cold:

- setup: `.env`, `.env.example`, `README`, `docker-compose*`, framework config,
  `.github/workflows/*`; every `secrets.*` / `vars.*` reference is a wizard value
- migration/cutover: current state, target state, irreversible actions

Show the ordered stage list and produced values; user may add, drop, or reorder.
Done when every stage is ordered and each value has (a) source, (b) destination
(`.env`, GitHub secret, both, or nowhere), and (c) secret (hidden) or public status.

### 2. Map each stage's journey

For each stage, record URL, clicks, and value location — e.g. "Dashboard →
Developers → API keys → Reveal test key → copy". Unknown UI/command → say so,
check docs, or ask; never invent steps.

### 3. Author the wizard

Copy `templates/template.sh` from this skill directory to the target. Replace
the example with one `stage` per step in dependency order. Set `TOTAL_STAGES` to
the number of stages.

Library helpers: `stage`, `say`/`step`/`note`/`warn`, `open_url`,
`ask`/`ask_secret`, `write_env`, `set_secret`/`set_var`, `pause`/`confirm`,
`banner`, `finish`. The library above the `STAGES` marker is identical in
every wizard — never hand-edit it; that consistency is the point.

Template bar: open URL before asking for value; `ask_secret` for secrets;
`write_env` for every persisted value; `set_secret` only for CI-needed values;
`confirm` before irreversible actions. Each `stage` clears the screen, so keep
one focused task per stage.

Wizard is ephemeral by default: save to scratch or `scripts/`, delete after the
job. Commit only when the user wants a repeatable repo setup path.

### 4. Verify and hand off

- `bash -n <script>`; run `shellcheck` if available; `chmod +x <script>`
- Do NOT run end-to-end: it opens browsers and blocks on human input. Static
  trace: every step-1 value is captured/delivered as declared; every `set_secret`
  name exactly matches a CI `secrets.*` reference.
- Tell the user how to run it; if repeatable, commit and link from README.

## Pitfalls

1. **Editing library.** Above `STAGES` is the shared library; author only below.
2. **Inventing dashboard paths.** UIs drift; verify docs or mark approximate.
3. **Misusing `set_secret`.** Push only values referenced by CI workflows.
4. **Running wizard.** Human input blocks; use static tracing + `bash -n`.
5. **One mega-stage.** Screen clearing hides instructions; split focused stages.

## Verification

- [ ] Stage list confirmed with the user before authoring
- [ ] `bash -n` passes; script is executable
- [ ] Every captured value traced to its declared destination
- [ ] Every `set_secret` name matches a CI `secrets.*` reference
- [ ] Library section untouched from the template
