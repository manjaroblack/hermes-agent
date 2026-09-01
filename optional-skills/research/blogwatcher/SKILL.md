---
name: blogwatcher
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool."
version: 2.0.0
author: JulienTant (fork of Hyaxia/blogwatcher)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites:
  commands: [blogwatcher-cli]
---

# Blogwatcher

role: blog/RSS feed monitor and article triage operator
do: install/configure `blogwatcher-cli`; add/scan/filter feeds; manage read state; automate changed-output digests
inputs: blog/feed URLs; OPML; categories; database path; cron delivery target
outputs: tracked feeds; unread/all article lists; changed-output digest; article URL for `web_extract`
¬: use bare schedule for recurring watch; re-scrape articles by hand; use this for one-off page-change monitoring; expose database secrets

Track blog and RSS/Atom updates with `blogwatcher-cli`: automatic feed discovery,
HTML scraping fallback, OPML import, and read/unread management.

## When to Use

- recurring blog/RSS/Atom monitoring with `blogwatcher-cli`
- feed discovery, OPML import, article filtering, or read-state management
- article reading after retrieval from `blogwatcher-cli articles`
- one-off page changes → use cronjob `monitor` with an http(s) URL instead
- analysis/citations → prefer `competitor-news-monitor`

## Working with Hermes tools (read this first)

`blogwatcher-cli` owns the feed database; Hermes tools automate it:

- recurring watch → cronjob `monitor`, not bare schedule; run
  `blogwatcher-cli scan >/dev/null 2>&1 && blogwatcher-cli articles` each tick;
  deterministic changed output wakes the agent with the diff, unchanged ticks
  cost zero LLM calls; set `deliver` for chat/channel digests and
  `continuity: true` for deduplication
- requested article → `web_extract([url])` on the URL from
  `blogwatcher-cli articles`; do not re-scrape
- one-off page change without feed semantics → cronjob `monitor` accepts an
  http(s) URL directly; skip this skill
- company/competitor analysis + citations → prefer `competitor-news-monitor`;
  blogwatcher is the lighter raw-feed layer

## Installation

Choose one method:

- **Go:** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker:** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **Binary (Linux amd64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (Linux arm64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Apple Silicon):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Intel):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

All releases: https://github.com/JulienTant/blogwatcher-cli/releases

### Docker with persistent storage

Default database: `~/.blogwatcher-cli/blogwatcher-cli.db`; Docker loses it on
restart. Persist with `BLOGWATCHER_DB` or a volume mount:

```bash
# Named volume (simplest)
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# Host bind mount
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### Migrating from the original blogwatcher

If upgrading from `Hyaxia/blogwatcher`, move your database:

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

Binary name: `blogwatcher-cli` (formerly `blogwatcher`).

## Common Commands

### Managing blogs

- Add a blog: `blogwatcher-cli add "My Blog" https://example.com`
- Add with explicit feed: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- Add with HTML scraping: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- List tracked blogs: `blogwatcher-cli blogs`
- Remove a blog: `blogwatcher-cli remove "My Blog" --yes`
- Import from OPML: `blogwatcher-cli import subscriptions.opml`

### Scanning and reading

- Scan all blogs: `blogwatcher-cli scan`
- Scan one blog: `blogwatcher-cli scan "My Blog"`
- List unread articles: `blogwatcher-cli articles`
- List all articles: `blogwatcher-cli articles --all`
- Filter by blog: `blogwatcher-cli articles --blog "My Blog"`
- Filter by category: `blogwatcher-cli articles --category "Engineering"`
- Mark article read: `blogwatcher-cli read 1`
- Mark article unread: `blogwatcher-cli unread 1`
- Mark all read: `blogwatcher-cli read-all`
- Mark all read for a blog: `blogwatcher-cli read-all --blog "My Blog" --yes`

## Environment Variables

All flags accept the `BLOGWATCHER_` environment prefix:

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Path to SQLite database file |
| `BLOGWATCHER_WORKERS` | Number of concurrent scan workers (default: 8) |
| `BLOGWATCHER_SILENT` | Only output "scan done" when scanning |
| `BLOGWATCHER_YES` | Skip confirmation prompts |
| `BLOGWATCHER_CATEGORY` | Default filter for articles by category |

## Example Output

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

## Notes

- auto-discovers RSS/Atom feeds from homepages without `--feed-url`
- falls back to HTML scraping when RSS fails and `--scrape-selector` is set
- stores RSS/Atom categories for filtering
- imports OPML from Feedly, Inoreader, NewsBlur, etc.
- stores database at `~/.blogwatcher-cli/blogwatcher-cli.db` by default; override with `--db` or `BLOGWATCHER_DB`
- use `blogwatcher-cli <command> --help` for all flags/options
