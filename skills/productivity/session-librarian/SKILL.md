---
name: session-librarian
description: "Organize sessions by prompt: find, rename, archive, prune."
version: 1.0.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Sessions, Organization, Cleanup, Library, Productivity]
    category: productivity
    related_skills: [weekly-review-planning]
---

# Session Librarian

role: session-library operator
do: find/summarize sessions; plan mutations; rename/archive/export/delete; fork or delegate workstreams; report/read back state
inputs: topic, metadata filters, session IDs/titles, cleanup scope, retention choice
outputs: `@session:` links, goal/outcome summaries, mutation plan, verified library state
¬: mutate before plan/approval; delete without dry-run + explicit confirmation; use `session_search` for metadata; confuse archive with delete; manage another profile's DB; drive other live sessions

Prompt examples: “find sessions about Q3 pricing,” “keep useful ones and clean
duplicates,” rename, archive stale work, fork follow-up, or split per ticket.

## When to Use

- topic/decision discovery
- meaningful renames
- stale/duplicate cleanup
- fork/follow-up or one-session-per-ticket work

## Surfaces

| Task | Surface |
|---|---|
| Find sessions by topic, read content, summarize decisions | `session_search` tool (FTS5 over the message store) |
| List/filter by metadata (age, source, cost, tokens, workspace) | `hermes sessions list` / `stats` via terminal |
| Rename | `hermes sessions rename <session_id> <title...>` |
| Bulk soft-hide (reversible) | `hermes sessions archive <filters>` |
| Delete (destructive) | `hermes sessions delete` / `hermes sessions prune <filters>` |
| Export before deleting anything valuable | `hermes sessions export --session-id <id> --format md` |
| Continue work in a new place | `/branch` (fork current session) or start a fresh session and cite the summary |

## Procedure

1. **Discover.** `session_search(query=..., limit=5-10)`; vary feature,
   symptom, project terms. Metadata sweep example:
   `hermes sessions list --source telegram --limit 50`.
2. **Summarize.** Use discovery `bookend_start` (goal), match window, and
   `bookend_end` (resolution). Full dump `session_search(session_id=...)` only
   for depth. Format: `@session:` link — goal — outcome.
3. **Plan before mutation.** Show table: rename target, archive set, deletion
   candidates + reason (duplicate keeper/stale/empty). Wait for go-ahead.
   Exception: single explicitly dictated rename.
4. **Use safest primitive.** Prefer archive. Run destructive `--dry-run`, show
   output, then after confirmation rerun `--yes`. Offer Markdown export first
   for meaningful content.
5. **Report.** Renames; archive count + undo listing
   `--include-archived`; exports; skipped items/reasons.

## Parallel Workstreams

For one session per ticket, use `delegate_task` once per workstream; each
subagent has its own session. Synthesize summaries. Mention delegation
transcripts remain searchable via `session_search`; do not drive other live
sessions yourself.

## Pitfalls

- standing “clean up” authorizes proposal, not prune
- `session_search` content != metadata; combine search + CLI
- titles identify `/resume <title>`; keep short, unique, prefix-friendly; warn collision
- archived sessions remain in DB, hidden from default listing
- `@session:<profile>/<id>` cross-profile links read-only; management uses current DB

## Verification

Re-run discovery query and `hermes sessions list`; keepers have new titles,
archived sessions are absent from default listing, and planned deletions match
the approved dry-run.