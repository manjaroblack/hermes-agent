---
name: openclaw-migration
description: Import an OpenClaw setup (memories, skills) into Hermes.
version: 1.0.0
author: Hermes Agent (Nous Research)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Migration, OpenClaw, Hermes, Memory, Persona, Import]
    related_skills: [hermes-agent]
---

# OpenClaw → Hermes Migration

role: OpenClaw-to-Hermes migration operator
do: dry-run; summarize; resolve conflicts via structured choices; choose preset; require workspace path; execute; report JSON truth and output directory
inputs: OpenClaw source; preset; SOUL/skill conflict policy; workspace target; explicit secret-migration consent; optional include/exclude
outputs: Hermes persona/memory/skills/config/assets; backups/archive; `report.json`/`summary.md`; migrated/conflict/skipped counts and reasons
¬: migrate secrets by default; overwrite silently; execute unresolved decisions; infer workspace target; claim skipped items migrated; call `clarify` with fake fields; guess paths

Use `scripts/openclaw_to_hermes.py` to move an OpenClaw setup with minimal
manual cleanup. The command and `hermes setup` wizard use the same migration
logic; the wizard detects `~/.openclaw` before configuration begins.

## When to Use

- user wants OpenClaw memories, persona, skills, settings, or workspace assets in Hermes
- user asks for preview, conflict resolution, secret-free import, or full compatible migration

## Procedure

### 1. CLI entry points

```bash
hermes claw migrate              # Full interactive migration
hermes claw migrate --dry-run    # Preview what would be migrated
hermes claw migrate --preset user-data   # Migrate without secrets
hermes claw migrate --overwrite  # Overwrite existing conflicts
hermes claw migrate --source /custom/path/.openclaw  # Custom source
```

Use the agent-guided flow for dry-run previews and per-item conflict decisions.

### 2. Resolve installed script path

The helper is `scripts/openclaw_to_hermes.py`; Skills Hub path:
`~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py`.
Do not guess `~/.hermes/skills/openclaw-migration/...`.

1. prefer the installed migration path
2. if missing, inspect installed skill directory and resolve relative to installed `SKILL.md`
3. use `search_files (target='files')` only if installed location is missing or manually moved
4. terminal `workdir` must be absolute or omitted; never pass `"~"`

### 3. Know migration coverage

The script can:

- import `SOUL.md` as Hermes `SOUL.md`
- transform OpenClaw `MEMORY.md`/`USER.md` into Hermes memory entries
- merge command-approval patterns into Hermes `command_allowlist`
- migrate compatible messaging settings such as `TELEGRAM_ALLOWED_USERS`
- map OpenClaw workspace settings to Hermes working-directory config
- copy skills to `~/.hermes/skills/openclaw-imports/`
- optionally copy workspace instructions to an explicit Hermes workspace
- mirror compatible assets such as `workspace/tts/` to `~/.hermes/tts/`
- archive docs without a direct Hermes destination
- emit structured migrated/conflict/skipped/reason report

`--migrate-secrets` imports only the allowlisted `TELEGRAM_BOT_TOKEN`; tokens,
auth blobs, device credentials, and raw gateway config remain excluded otherwise.

### 4. Default decision flow

1. dry-run unless user explicitly says immediate execution
2. summarize migratable, unsupported, archived, conflicts, large assets, and memory overflow
3. resolve `SOUL.md` conflict
4. resolve imported skill conflicts
5. resolve migration mode
6. resolve workspace instructions and obtain absolute target if copying
7. restate exact command/flags in plain language
8. execute
9. report `report.summary`, output directory, migrated items, archive, skips, conflicts, and reasons

Default to `user-data only` when user is unsure. Include `workspace-agents` only
after explicit destination path or explicit skip/defer choice.

### 5. `clarify` interaction contract

When `clarify` is available, use it for choices: one choice at a time, 2-4
plain string options, automatic `Other` free text, no true multi-select. Every
call has non-empty `question`; use `choices` only for selectable prompts; never
use `...`, padded/stylized choices, fake fields, blank lines, underscores, or
"enter directory here". Ask an open-ended plain sentence only for an absolute
path.

If a `clarify` call errors, inspect text, correct payload, retry once. After a
dry run reports any required decision, the NEXT action must be `clarify`; do not
send prose such as "Here are the options" first. If several decisions remain,
call the next required `clarify` immediately after each answer.

Treat `workspace-agents` as unresolved when dry-run item has
`kind="workspace-agents"`, `status="skipped"`, and reason containing
`No workspace target was provided`. Absence of a target is not permission to
skip or execute.

Choice flow:

1. SOUL conflict: `keep existing` | `overwrite with backup` | `review first`
2. skill conflicts: `keep existing skills` | `overwrite conflicting skills with backup` | `import conflicting skills under renamed folders`
3. workspace instructions: `skip workspace instructions` | `copy to a workspace path` | `decide later`
4. if copy selected, follow up with open-ended absolute-path question
5. migration mode: `user-data only` | `full compatible migration` | `cancel`

Mode semantics: `user-data only` migrates user data/compatible config without
allowlisted secrets; `full compatible migration` adds allowlisted secrets when
present. If `clarify` is unavailable, ask normal text but constrain answer to
those three mode choices.

Default payloads:

- `{"question":"Your existing SOUL.md conflicts with the imported one. What should I do?","choices":["keep existing","overwrite with backup","review first"]}`
- `{"question":"One or more imported OpenClaw skills already exist in Hermes. How should I handle those skill conflicts?","choices":["keep existing skills","overwrite conflicting skills with backup","import conflicting skills under renamed folders"]}`
- `{"question":"Choose migration mode: migrate only user data, or run the full compatible migration including allowlisted secrets?","choices":["user-data only","full compatible migration","cancel"]}`
- `{"question":"Do you want to copy the OpenClaw workspace instructions file into a Hermes workspace?","choices":["skip workspace instructions","copy to a workspace path","decide later"]}`
- `{"question":"Please provide an absolute path where the workspace instructions should be copied."}`

Decision priority: SOUL conflict → imported skill conflicts → migration mode →
workspace destination. After migration-mode answer, check workspace-agents again;
if unresolved, next action is workspace `clarify`. Never promise choices later.

### 6. Map decisions to flags

- SOUL `keep existing` → no `--overwrite`
- SOUL `overwrite with backup` → `--overwrite`
- SOUL `review first` → stop; review files before execution
- skills `keep existing skills` → `--skill-conflict skip`
- skills `overwrite conflicting skills with backup` → `--skill-conflict overwrite`
- skills `import conflicting skills under renamed folders` → `--skill-conflict rename`
- `user-data only` → `--preset user-data`; no `--migrate-secrets`
- `full compatible migration` → `--preset full --migrate-secrets`
- absolute workspace path only → add `--workspace-target <path>`
- workspace skip/defer → no `--workspace-target`

Execution gate: no unresolved `clarify` decision; no unresolved
`workspace-agents` skip. Valid workspace resolutions are explicit skip, explicit
decide-later, or an absolute path after copy choice.

### 7. Presets

Prefer `user-data` or `full`; category-level `--include`/`--exclude` is advanced.

`user-data` categories:

- `soul`
- `workspace-agents`
- `memory`
- `user-profile`
- `messaging-settings`
- `command-allowlist`
- `skills`
- `tts-assets`
- `archive`

`full` = `user-data` plus `secret-settings`.

### 8. Execute

Dry run with discovery:

```bash
python ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py
```

Absolute terminal invocation pattern:

```json
{"command":"python /home/USER/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py","workdir":"/home/USER"}
```

Dry run user data:

```bash
python ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --preset user-data
```

Execute user data:

```bash
python ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict skip
```

Execute full compatible migration:

```bash
python ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset full --migrate-secrets --skill-conflict skip
```

Execute with workspace instructions:

```bash
python ~/.hermes/skills/migration/openclaw-migration/scripts/openclaw_to_hermes.py --execute --preset user-data --skill-conflict rename --workspace-target "/absolute/workspace/path"
```

Never default workspace target to `$PWD` or home. Ask for an explicit absolute
path first.

### 9. Report JSON truth

After execution, `report` is authoritative:

1. counts come from `report.summary`
2. list under Successfully Migrated only items with status exactly `migrated`
3. never claim conflict resolution, SOUL overwrite, backup, or migration without that status
4. if `report.summary.conflict > 0`, show a conflict section
5. reconcile listed items with counts before responding
6. include `output_dir` when present for `report.json`, `summary.md`, backups, archive
7. overflow: only claim archive if archive path exists; if `details.overflow_file`, report exported full list there
8. renamed skill: report final destination and `details.renamed_from`
9. use `report.skill_conflict_mode` as selected policy truth
10. skipped means not overwritten/backed up/migrated/resolved
11. SOUL skipped with `Target already matches source` → left unchanged; no backup claim
12. renamed skill with empty `details.backup` → imported copy placed in new destination; existing folder remained; cite `details.renamed_from`, do not imply rename/backup

## Pitfalls

- secrets are excluded by default; full mode requires explicit consent
- unsupported auth blobs remain skipped even in secret mode
- non-empty Hermes targets are not silently overwritten; overwrite keeps backups
- primary `~/.openclaw/workspace/` wins; use `workspace.default/` only when primary files are missing
- large assets, conflicting SOUL, and overflowed memory need separate pre-run notice
- category `--include`/`--exclude` is advanced, not normal UX
- no workspace target means unresolved workspace decision, not permission to execute
- `clarify` choices must be structured and immediate; use plain free text only for absolute path
- migration report, especially skipped items, is mandatory post-run output

## Verification

- dry run ran before writes unless explicit immediate execution
- chosen preset/flags match recorded user decisions
- workspace instructions copied only to explicit absolute path
- output contains persona state, converted memory, imported skills under `~/.hermes/skills/openclaw-imports/`, and compatible config/assets as selected
- report counts and item lists match `report.summary`; conflicts/skips/archives are explicit
- `output_dir` shared when present; user can inspect `report.json`, `summary.md`, backups, overflow, and archive
- no secret migration claimed unless full mode and report show it