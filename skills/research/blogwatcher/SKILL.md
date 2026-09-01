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

role: blog/RSS/Atom monitoring operator
do: install and configure `blogwatcher-cli`; discover feeds; scrape fallback; import OPML; scan/read/manage articles
inputs: blog name/URL/feed URL/scrape selector, OPML, filters, DB path, worker/confirmation flags
outputs: tracked blogs, scan results, unread/all article lists, read-state updates
¬: lose the DB on Docker restart; use wrong binary name; assume RSS fallback without `--scrape-selector`; expose private feed data

Track feed updates with automatic discovery, HTML scraping fallback, OPML import,
and read/unread management. Database defaults to
`~/.blogwatcher-cli/blogwatcher-cli.db`; override with `--db` or
`BLOGWATCHER_DB`.

## When to Use

- add/list/remove blogs and import subscriptions
- scan all or one blog for new articles
- list/filter/read/unread articles
- configure worker count, DB path, silent mode, or confirmation behavior

## Prerequisites

Choose one install:

- Go: `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- Docker: `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- Linux amd64 binary:
  `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- Linux arm64 binary:
  `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- macOS Apple Silicon:
  `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- macOS Intel:
  `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

All releases: https://github.com/JulienTant/blogwatcher-cli/releases

## Installation + Storage

```bash
# Named volume (simplest)
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# Host bind mount
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

Host DB migration from `Hyaxia/blogwatcher`:

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

Binary changed from `blogwatcher` to `blogwatcher-cli`. Docker needs a volume or
`BLOGWATCHER_DB`; otherwise restart loses state.

## Quick Reference

| Task | Command |
|---|---|
| Add blog | `blogwatcher-cli add "My Blog" https://example.com` |
| Add explicit feed | `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml` |
| Add HTML scraping | `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"` |
| List/remove blogs | `blogwatcher-cli blogs`; `blogwatcher-cli remove "My Blog" --yes` |
| Import OPML | `blogwatcher-cli import subscriptions.opml` |
| Scan all/one | `blogwatcher-cli scan`; `blogwatcher-cli scan "My Blog"` |
| Unread/all articles | `blogwatcher-cli articles`; `blogwatcher-cli articles --all` |
| Filter articles | `blogwatcher-cli articles --blog "My Blog"`; `blogwatcher-cli articles --category "Engineering"` |
| Read/unread | `blogwatcher-cli read 1`; `blogwatcher-cli unread 1` |
| Mark all read | `blogwatcher-cli read-all`; `blogwatcher-cli read-all --blog "My Blog" --yes` |

## Environment Variables

All flags accept `BLOGWATCHER_`-prefixed environment variables:

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Path to SQLite database file |
| `BLOGWATCHER_WORKERS` | Concurrent scan workers (default: 8) |
| `BLOGWATCHER_SILENT` | Output only "scan done" when scanning |
| `BLOGWATCHER_YES` | Skip confirmation prompts |
| `BLOGWATCHER_CATEGORY` | Default article category filter |

## Procedure

1. Verify `blogwatcher-cli --help`; select persistent DB path/volume.
2. Add blogs with feed URL when known; otherwise allow RSS/Atom discovery; add
   `--scrape-selector` for HTML fallback when RSS fails.
3. Import OPML when bulk-loading Feedly, Inoreader, NewsBlur, or similar lists.
4. Scan all/selected blogs; inspect new article counts.
5. List/filter articles; mark IDs read/unread; re-list after state changes.
6. Use `blogwatcher-cli <command> --help` for unlisted flags.

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

## Pitfalls

- default DB is `~/.blogwatcher-cli/blogwatcher-cli.db`; Docker restart loses it
  without volume/`BLOGWATCHER_DB`
- original binary/DB names differ: `blogwatcher` → `blogwatcher-cli`
- feed discovery is automatic only when `--feed-url` omitted; HTML fallback needs
  `--scrape-selector`
- RSS/Atom categories are filterable; OPML bulk import preserves subscriptions
- `BLOGWATCHER_YES` skips confirmations; use deliberately

## Verification

- `blogwatcher-cli --help` succeeds and DB path is persistent
- expected blogs/feed URLs appear in `blogwatcher-cli blogs`
- scan output distinguishes source, found, and new counts
- article filters match requested blog/category; read-state changes persist
- OPML import and Docker storage behavior confirmed when used
