---
name: watchers
description: Poll RSS, JSON APIs, and GitHub with watermark dedup.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [cron, polling, rss, github, http, automation, monitoring]
    category: devops
    requires_toolsets: [terminal]
    related_skills: []
---

# Watchers

role: watermark-deduplicated polling operator
do: select watcher; fetch source; compare bounded watermark; save state; emit only new items; wire cron; inspect/replay state; report fetch errors
inputs: RSS/Atom URL, JSON endpoint/item path/id field, GitHub repo/scope, watcher name, interval, state directory
outputs: new-item stdout (`## title`, URL, optional body), persistent state, silent no-change poll, non-zero fetch failure
¬: print no-change headers; replay baseline on first run; grow watermark unbounded; write state where sandbox cannot; expose GitHub token; claim host-path visibility on remote backend

Poll RSS/Atom, JSON APIs, or GitHub on an interval and react only to new items. Run scripts ad hoc or wire them into cron; use Hermes `terminal`.

## When to Use

- watch RSS/Atom entries
- watch GitHub issues, pulls, releases, commits
- poll arbitrary JSON and notify on new items
- “watch X” / “notify me when X changes”

## Mental Model

`fetch → compare with watermark → atomically save → print new items or nothing`.

Scripts live at `$HERMES_HOME/skills/devops/watchers/scripts/`; state defaults to `$HERMES_HOME/watcher-state/`, keyed by `--name`.

| Script | What it watches | Dedup key |
|---|---|---|
| `watch_rss.py` | RSS 2.0 or Atom feed URL | `<guid>` / `<id>` |
| `watch_http_json.py` | Any JSON endpoint returning a list of objects | Configurable id field |
| `watch_github.py` | GitHub issues / pulls / releases / commits for a repo | `id` / `sha` |

All: first run records baseline; watermark max 500 IDs; output `## <title>\n<url>\n\n<optional body>`; empty stdout means no new; non-zero means fetch error.

## Procedure

### Run RSS

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_rss.py \
  --name hn --url https://news.ycombinator.com/rss --max 5
```

### Run GitHub

Set `GITHUB_TOKEN` in `${HERMES_HOME:-~/.hermes}/.env` to avoid anonymous 60 req/hr limit:

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_github.py \
  --name hermes-issues --repo NousResearch/hermes-agent --scope issues
```

### Run JSON API

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_http_json.py \
  --name api --url https://api.example.com/events \
  --id-field event_id --items-path data.events
```

### Wire cron

Prompt pattern:

```text
Every 15 minutes, run watch_rss.py --name hn --url https://news.ycombinator.com/rss. If it prints anything, summarize headlines and deliver them. If empty, stay silent.
```

Use the terminal inside the cron agent loop; no cron built-in `--script` change required.

### Inspect/reset state

State file: `$HERMES_HOME/watcher-state/<name>.json`.

```bash
cat $HERMES_HOME/watcher-state/hn.json
```

Delete to make next run a first poll. Custom scripts should import `scripts/_watermark.py` for atomic writes, bounded IDs, and first-run baseline.

## Pitfalls

- empty delta must produce empty stdout; “no new items” spam breaks callers
- first run intentionally emits nothing; delete state after baseline for an initial digest
- shared watermark caps at 500; tune custom implementation for churn/filesystem
- `$HERMES_HOME/watcher-state/` is writable; Docker/Modal backends may not see arbitrary host paths

## Verification

- first run creates state and emits no existing items
- second unchanged run has empty stdout
- new source item emits title/URL/body once
- repeat item is deduplicated
- fetch failure exits non-zero
- cron prompt remains silent on no-change

## Preserved Source Examples

### Original example 1

```bash
rm $HERMES_HOME/watcher-state/hn.json
```
