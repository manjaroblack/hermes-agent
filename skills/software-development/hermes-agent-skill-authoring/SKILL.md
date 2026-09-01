---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md files: frontmatter and structure."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

role: in-repo Hermes skill author/editor
do: choose tier/category; inspect peers; author frontmatter/body/references; audit platforms/links; run tests/docs generation; commit and hand off
inputs: reusable workflow, target `skills/` or `optional-skills/` path, human attribution, repo conventions, tests/docs generator
outputs: committed SKILL.md, supporting references, templates, or scripts as needed, focused tests/docs, verified metadata and links
¬: write private skills into repo; use `skill_manage(create)` for in-repo creation; invent categories/routers; credit agent alone; use machine-local paths; skip tests/docs/validation

## Overview

Two SKILL.md locations:

1. User-local: `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal,
   not shared; create with `skill_manage(action='create')`.
2. In-repo: `skills/<category>/<name>/SKILL.md` or
   `optional-skills/<category>/<name>/SKILL.md` inside hermes-agent — committed
   and shipped; use `write_file` + `git add`; `skill_manage(action='create')`
   does NOT target this tree.

In-repo skills must meet AGENTS.md `Skill authoring standards (HARDLINE)`;
that section is source of truth, this skill is the operational walkthrough.
Reviewers reject violations; satisfy hardline before review.

## When to Use

- user asks to add a skill "in this branch / repo / commit"
- commit a reusable workflow shipped with hermes-agent
- edit an existing `skills/` or `optional-skills/` skill; `patch` for small
  edits, `write_file` for rewrites (`skill_manage` can patch in-repo, not `create`)
- ¬ personal `~/.hermes/skills/` work; use `skill_manage`

## Prerequisites

- target tier/category; existing skill inventory and 2–3 peers
- human contributor attribution; repo conventions and AGENTS.md
- repo test/docs generator
- `search_files`, `read_file`, `write_file`, `patch`, `terminal`

## Decide Tier and Category First

- Bundled `skills/<category>/`: daily-driver, broadly useful, low footprint;
  credible use ≥5 sessions/month.
- Optional `optional-skills/<category>/`: niche/vertical (blockchain, gaming,
  finance, one app), recurring-job/task, or heavy; install with
  `hermes skills install official/<category>/<skill>`.
- When uncertain → optional; promotion is easy, demotion causes churn. "Useful
  to anyone who ever needs this" argues optional, not bundled.
- Category follows what the tool/workflow IS, not its vibe (AI-agent CLI →
  `autonomous-ai-agents/` even if it feels productivity). Confirm with
  `search_files(pattern='*', target='files', path='skills')`; don't invent top-level
  categories casually.
- ¬ router/index/hub skill: catalog + sibling `When to Use` triggers already route;
  a routing table only adds indirection and duplicates triggers.

Done when tier/category/overlap decision is recorded and peers are known.

## Required Frontmatter

Validator source: `tools/skill_manager_tool.py::_validate_frontmatter`.
Hard requirements:

- first bytes `---` (no leading blank/BOM)
- closing `\n---\n` before body
- YAML mapping
- `name` and `description`
- description validator ceiling 1024 chars (repo hardline is stricter)
- non-empty body after closing `---`

Repo shape (all fields expected even where validator is permissive):

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Concise capability statement, under sixty chars.
version: 0.1.0                    # semver; new skills start at 0.1.0
author: Real Name (github-handle), Hermes Agent
license: MIT
platforms: [linux, macos, windows]   # audit, don't guess — see Platform Gating
metadata:
  hermes:
    tags: [Short, Descriptive, Tags]
    related_skills: [other-in-repo-skill]
---
```

### Description rules (HARDLINE)

- ≤60 chars; one sentence; period-terminated
- capability, not implementation or repeated skill name
- ¬ marketing: `powerful`, `comprehensive`, `seamless`, `advanced`
- trigger/capability self-contained within 57 chars + index `...`
- description containing `:` → double-quote it; YAML otherwise parses mapping;
  quotes don't count
- good: `Track named companies for material news with cited digests.`
- bad: `Use when a user asks to monitor named competitors or companies for product launches, pricing changes, funding, ...` (240 chars)

### Author rules

- human first, then `Hermes Agent`: `Ben Barclay (benbarclay), Hermes Agent`
- never `author: Hermes Agent` alone for contributed work
- maintainer style: `Teknium (teknium1), Hermes Agent`

### Related-skill rules

- every entry resolves to an existing in-repo skill in the same tree state as
  the change; ¬ planned, sibling-PR, or `~/.hermes/skills/` only
- verify with `search_files(pattern='<name>', target='files', path='skills')`
  and `optional-skills/`

## Platform Gating: Audit, Don't Trust

`platforms:` gates loading by host OS; infer from prose/scripts:

| Skill uses only… | `platforms:` |
|---|---|
| Hermes tools + stdlib Python + cross-platform CLIs | `[linux, macos, windows]` |
| bash pipelines, grep/awk/sed chains, heredocs | `[linux, macos]` |
| `osascript`, `defaults`, `pmset` | `[macos]` |
| `apt`/`systemctl`/`/proc` | `[linux]` |

Search `scripts/` for POSIX signals: `fcntl`, `termios`, `pty`, `os.fork`,
`os.killpg`, `signal.SIGKILL`, `os.kill(pid, 0)`, hardcoded `/tmp` `/proc` `/etc`.
Default: fix cross-platform first (`tempfile.gettempdir()`, `pathlib.Path`,
`psutil.pid_exists`); narrow only for genuine platform-bound dependencies and
explain why in `## Pitfalls`.

## Size Limits

- hard max 100,000 chars (`MAX_SKILL_CONTENT_CHARS`)
- target ~100 lines simple, ~200 complex; peers commonly 8–14k chars
- move bulky or branch-specific material to `references/*.md`, `templates/`,
  `scripts/`; point to it, don't inline
- non-trivial parsers/logic belong in helper scripts, not re-written each call

## Body Structure

```text
# <Skill> Skill
2-3 sentence intro: what it does, what it doesn't do, dependency stance.

## When to Use          — triggers + "Don't use for:" counter-triggers
## Prerequisites        — exact env vars, installs, API key sourcing
## How to Run           — canonical invocation through `terminal`
## Quick Reference      — flat command list, no narration
## Procedure            — numbered steps, each checkable
## Pitfalls             — known limits and deceptive failures
## Verification         — proof the skill worked
```

When/Procedure/Pitfalls/Verification are minimum actionable structure; Quick
Reference may not apply to pure-procedure work. Cut marketing intros, no-op
"Setup Check" sections, and repeated env-var explanations.

### Reference Hermes tools, not raw shell

Name proper tools: `terminal`, `read_file`, `write_file`, `patch`, `search_files`,
`web_search`, `web_extract`, `browser_navigate`, `vision_analyze`,
`delegate_task`, `cronjob`. Map wrapped shell utilities: grep→`search_files`,
cat→`read_file`, sed/awk→`patch`, find/ls→`search_files(target='files')`.
CLI wrappers frame calls as `terminal(command="<tool> ...", timeout=...)`, not bare
shell prose such as "run `foo --version`". If an MCP server is required, name it
and document setup in Prerequisites.

### Never use machine-local paths

Use repo-relative `skills/...`, `tools/skill_manager_tool.py`; a baked
`/home/<you>/...` path breaks other users and is an instant review flag.

## Writing Quality Principles

A skill makes the agent's process predictable:

1. cut behavior-neutral lines; optimize process predictability
2. description is paid every turn; put detail in body/references
3. end ordered steps with checkable, exhaustive criteria ("every modified file
   accounted for" > "summarize changes")
4. co-locate rules with governed concepts
5. lead with strong terms: "tight loop", "root cause", "regression test"
6. prune duplication/no-ops ("be careful", "use best practices")

## Tests and Docs (Required for Repo Skills)

1. Tests: `tests/skills/test_<skill>_skill.py`; stdlib + pytest +
   `unittest.mock`, no live network. Run
   `scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q`.
   Generic `tests/tools/test_skill_manager_tool.py` passing proves nothing about
   the authored skill.
2. Docs: run `python website/scripts/generate-skill-docs.py`. It rewrites EVERY
   auto-gen page; use `git checkout --` for unrelated drift. Final diff: SKILL.md,
   one per-skill page, one catalog row, one `website/sidebars.ts` insertion.
   Verify sidebar slug with
   `search_files(pattern='<your-slug>', path='website/sidebars.ts')` = exactly one
   hit; otherwise page is orphaned.
3. New env vars only: one clearly delimited commented block in `.env.example`;
   touch nothing else.

## Workflow

1. Survey category peers with `search_files(target='files')` (or
   `search_files target='files'`); read 2–3 peer
   SKILL.md files; extend an existing skill before creating a narrow sibling.
2. Decide tier/category above; when in doubt optional, ask before pushing.
3. Draft with `write_file` to `skills/<category>/<name>/SKILL.md` or
   `optional-skills/...`.
4. Validate locally:

   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 60, f"description {len(fm['description'])} chars — hardline is 60"
   assert fm["description"].endswith(".")
   assert "platforms" in fm
   assert len(content) <= 100_000
   ```

   Also verify every `related_skills` entry exists in-repo.
5. Add focused tests and regenerate docs with scope discipline.
6. `git add` + commit on active branch; open a PR.
7. Current session's loader is cached: `skill_view` / `skills_list` see new
   skills only after a new session; expected, not a bug.

## Editing Existing In-Repo Skills

- small fix: `skill_manage(action='patch', ...)` or `patch`
- major rewrite: `write_file` whole `SKILL.md`
- supporting files: `write_file` under `references/`, `templates/`, `scripts/`
- always commit; rerun docs generator when frontmatter changes

## Common Pitfalls

1. `skill_manage(action='create')` writes `~/.hermes/skills/`, not repo tree;
   use `write_file`.
2. Validator allows 1024-char descriptions; review hardline is 60 and also
   checks `platforms`, author, tests, docs.
3. `author: Hermes Agent` alone erases contributor credit; human first.
4. Leading whitespace/BOM before `---` fails validation.
5. Generic trigger or capability past char 57 is truncated.
6. `related_skills` may point only to in-repo skills; verify state.
7. Duplicate sibling means survey/extend first.
8. No docs regen creates orphan; blind generator regen pushes unrelated drift.
9. Current session cannot see new skill until reload.
10. Adding rules without removing superseded wording accumulates sediment.

## Verification Checklist

- [ ] tier deliberate: bundled ≥5 sessions/month; else `optional-skills/`
- [ ] correct repo path; frontmatter byte 0 `---`, closes correctly
- [ ] `name`, `description`, `version`, `author`, `license`, `platforms`,
      `metadata.hermes.{tags, related_skills}` present
- [ ] description ≤60 chars, one sentence, period, no marketing
- [ ] human contributor first in `author`
- [ ] platforms audited against prose/scripts, not copied
- [ ] every related skill resolves in-repo
- [ ] body has routing, prerequisites, actionable procedure, pitfalls, verification
- [ ] Hermes tool names + repo-relative paths used; no machine-local paths
- [ ] ordered steps have checkable criteria
- [ ] focused skill test passes via `scripts/run_tests.sh`
- [ ] docs regenerated with unrelated drift reverted; exactly one sidebar entry
- [ ] intended files staged/committed; PR opened
