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
    related_skills: [plan, requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

role: in-repo Hermes skill author/editor
do: choose tier/category; inspect peers; author frontmatter/body/references; audit platforms/links; run tests/docs generation; commit and hand off
inputs: reusable workflow, target `skills/` or `optional-skills/` path, human attribution, repo conventions, tests/docs generator
outputs: committed SKILL.md, supporting references, templates, or scripts as needed, focused tests/docs, verified metadata and links
¬: write private skills into repo; use `skill_manage(create)` for in-repo creation; invent categories/routers; credit agent alone; use machine-local paths; skip tests/docs/validation

Two locations:

1. User-local `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal;
   create with `skill_manage(action='create')`.
2. In-repo `skills/<category>/<name>/SKILL.md` or
   `optional-skills/<category>/<name>/SKILL.md` — committed/shipped; use
   `write_file` + `git add`. `skill_manage(action='create')` does not target it.

Repo hardline standards are in AGENTS.md; this skill is the operational path.

## When to Use

- add a skill in the current repo/branch/commit
- commit a reusable workflow shipped with hermes-agent
- edit an existing `skills/` or `optional-skills/` skill
- audit frontmatter, platform gating, references, docs, or hygiene

Don't use for personal `~/.hermes/skills/`; use `skill_manage`.

## Prerequisites

- target tier/category and existing skill inventory
- human contributor attribution
- repo test/docs generator and AGENTS.md
- `search_files`, `read_file`, `write_file`, `patch`, `terminal`

## Procedure

### 1. Decide tier and category

- **Bundled** `skills/<category>/`: broad daily-driver, low footprint; credible
  use ≥5 sessions/month.
- **Optional** `optional-skills/<category>/`: niche/vertical, recurring-job,
  heavy, or one-app; install via `hermes skills install official/<category>/<skill>`.
- When uncertain → optional; promotion is easier than demotion.
- Choose category by what tool/workflow is, not its vibe. Inspect categories with
  `search_files(pattern='*', target='files', path='skills')`.
- No router/index/hub skill; catalog + sibling `When to Use` already route.

Done when tier/category/overlap decision is recorded and peers are known.

### 2. Required frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`.
Hard requirements: first bytes `---`; closing `\n---\n`; YAML mapping; `name`,
`description`; non-empty body. Repo shape:

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

#### Description hardline

- ≤60 chars; one sentence; ends period; capability, not implementation/name
- no marketing (`powerful`, `comprehensive`, `seamless`, `advanced`)
- trigger/capability must be self-contained within 57 chars + index ellipsis
- quote descriptions containing `:`; quotes do not count

Good: `Track named companies for material news with cited digests.`
Bad: 240-char trigger paragraph.

#### Author + links

- human first, then `Hermes Agent`: `Ben Barclay (benbarclay), Hermes Agent`
- maintainer style: `Teknium (teknium1), Hermes Agent`
- each `related_skills` entry must resolve to an in-repo skill in this tree;
  verify with `search_files` in `skills/` and `optional-skills/`.

### 3. Audit platform gating

`platforms:` gates by host OS; infer from prose/scripts:

| Skill uses only… | `platforms:` |
|---|---|
| Hermes tools + stdlib Python + cross-platform CLIs | `[linux, macos, windows]` |
| bash pipelines and POSIX text-filter chains, heredocs | `[linux, macos]` |
| `osascript`, `defaults`, `pmset` | `[macos]` |
| `apt`/`systemctl`/`/proc` | `[linux]` |

Search scripts for POSIX signals: `fcntl`, `termios`, `pty`, `os.fork`,
`os.killpg`, `signal.SIGKILL`, `os.kill(pid, 0)`, hardcoded `/tmp` `/proc` `/etc`.
Prefer cross-platform fixes (`tempfile.gettempdir()`, `pathlib.Path`,
`psutil.pid_exists`); narrow only for genuine platform dependencies and explain
why in Pitfalls.

### 4. Author body and size

Target ~100 lines simple, ~200 complex; hard max 100,000 chars
(`MAX_SKILL_CONTENT_CHARS`). Move bulky examples/procedures to
`references/*.md`, `templates/`, or `scripts/`; link them. Minimum structure:

```
# <Skill> Skill
2-3 sentence intro: what it does, what it doesn't do, dependency stance.

## When to Use          — bulleted triggers (+ "Don't use for:" counter-triggers)
## Prerequisites        — exact env vars, installs, API key sourcing
## How to Run           — canonical invocation through the `terminal` tool
## Quick Reference      — flat command list, no narration
## Procedure            — numbered steps, each with a checkable completion criterion
## Pitfalls             — known limits, things that look broken but aren't
## Verification         — how to prove the skill worked
```

When a capability is needed, name Hermes tools: `terminal`, `read_file`,
`write_file`, `patch`, `search_files`, `web_search`, `web_extract`,
`browser_navigate`, `vision_analyze`, `delegate_task`, `cronjob`. Do not name
wrapped shell utilities as the agent API; map text search to `search_files`, file
reads to `read_file`, edits to `patch`, and file enumeration to
`search_files (target='files')`. CLI wrappers
should frame calls as `terminal(command="<tool> ...", timeout=...)`.

Use repo-relative paths (`skills/...`, `tools/...`); never commit machine-local
paths. Each ordered step ends with a checkable criterion.

### Quality principles

1. Optimize process predictability; cut behavior-neutral lines.
2. Keep expensive routing description short; put depth in body/references.
3. State exhaustive completion criteria.
4. Co-locate rules with the concept governed.
5. Lead with strong words: tight loop, root cause, regression test.
6. Remove duplication/no-ops such as “be careful” and “best practices.”

### 5. Tests and docs

1. Tests: `tests/skills/test_<skill>_skill.py`, stdlib + pytest + `unittest.mock`,
   no live network. Run:

   ```bash
   scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q
   ```

2. Docs: run `python website/scripts/generate-skill-docs.py`; revert generated
   unrelated drift. Final diff: SKILL.md, one per-skill page, one catalog row,
   one `website/sidebars.ts` insertion. Verify sidebar slug with
   `search_files(pattern='<your-slug>', path='website/sidebars.ts')` = exactly one.
3. New env vars only: one clearly delimited commented block in `.env.example`;
   touch nothing else.

### 6. Validate and hand off

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

Also verify every related skill exists in-repo, add focused tests, regenerate
scoped docs, inspect diff, then `git add` + commit on intended branch/open PR.
Current session loader is cached; new skills appear after a new session.

## Editing Existing In-Repo Skills

- small fix: `skill_manage(action='patch', ...)` or `patch`
- major rewrite: `write_file` whole SKILL.md
- supporting files: `write_file` under `references/`, `templates/`, `scripts/`
- always commit; rerun docs generator when frontmatter changes

## Pitfalls

- `skill_manage(action='create')` writes profile-local state, not repo tree
- validator allows 1024-char descriptions; repo hardline is 60
- contributed skill must credit human first
- leading blank/BOM before `---` fails validation
- generic/late trigger gets truncated from index
- related skill may be user-local/planned/sibling-PR only; verify in-repo
- duplicate sibling means survey/extend first
- no docs regen or blind unrelated regen; scope generator output
- current session cannot see newly authored skill until reload
- when adding a rule, remove superseded sediment

## Verification Checklist

- [ ] Tier deliberate: bundled ≥5 sessions/month; else `optional-skills/`
- [ ] Correct repo path; frontmatter starts byte 0 and closes correctly
- [ ] `name`, `description`, `version`, `author`, `license`, `platforms`, and
      `metadata.hermes.{tags, related_skills}` present
- [ ] Description ≤60 chars, one sentence, period, no marketing
- [ ] Human contributor credited first
- [ ] Platforms audited against actual prose/scripts
- [ ] Related skills resolve in-repo
- [ ] Body has routing, prerequisites, actionable procedure, pitfalls, verification
- [ ] Hermes tool names and repo-relative paths used
- [ ] Ordered steps have checkable criteria
- [ ] Focused skill test passes via `scripts/run_tests.sh`
- [ ] Docs regenerated with unrelated drift reverted; one sidebar entry
- [ ] Intended files staged/committed; PR opened
