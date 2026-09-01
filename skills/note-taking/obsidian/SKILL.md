---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Obsidian, Notes, Markdown, Vault]
    related_skills: []
---

# Obsidian Vault

role: filesystem-first vault editor
do: resolve vault path; read/list/search/create/append/edit notes; add wikilinks
inputs: concrete vault path, note path/pattern, Markdown content, stable edit anchor
outputs: note content, file matches, created/updated Markdown
¬: pass unresolved `$OBSIDIAN_VAULT_PATH` to file tools; use shell text rewriting when native file tools suffice; assume fallback vault exists

## When to Use

- read or search vault notes
- list Markdown notes/subfolders
- create, append, or make targeted edits
- add Obsidian wikilinks

## Procedure

1. Resolve `OBSIDIAN_VAULT_PATH` or fallback to a concrete existing absolute path.
2. Choose read/list/search/create/append/targeted-edit operation below.
3. Use native file tools with resolved paths; keep edits anchored and scoped.
4. Re-read changed notes; verify Markdown + wikilinks and report exact path.

## Resolve Vault Path

Use `OBSIDIAN_VAULT_PATH`, commonly loaded from
`${HERMES_HOME:-~/.hermes}/.env`; fallback = `~/Documents/Obsidian Vault`.
File tools do not expand shell variables: resolve to a concrete absolute path
before `read_file`, `write_file`, `patch`, or `search_files`. Paths may contain
spaces, so prefer native file tools. If unknown, `terminal` may resolve the env
value or test the fallback; then return to file tools.

## Operations

### Read

`read_file` with the resolved absolute note path; it provides line numbers and
pagination and is preferred over raw shell file reads.

### List

`search_files(target="files", path=<resolved-vault>)`; use `pattern="*.md"`
for all Markdown or the subfolder's absolute path for a narrower list. Prefer
this over unscoped filesystem enumeration.

### Search

- filename: `search_files(target="files", pattern=<filename-pattern>)`
- contents: `search_files(target="content", pattern=<regex>, file_glob="*.md")`

Prefer this over raw text search or unscoped filesystem enumeration.

### Create

`write_file` with resolved absolute path + complete Markdown. Avoid shell
heredocs/`echo` quoting problems.

### Append

1. Read target with `read_file`.
2. Use `patch` for a stable anchor (after heading or before known trailing block).
3. Use `write_file` when a full rewrite is clearer/safer.
4. For no stable context, `terminal` is acceptable for a simple append.

Anchored append = replace anchor with anchor + new content.

### Targeted edit + links

Use `patch` with stable current context; avoid shell rewriting. Obsidian links
use `[[Note Name]]`; add them when creating related notes.

## Pitfalls

- unresolved env syntax yields a literal, nonexistent tool path
- fallback path is a default, not proof of the active vault
- `search_files` path/pattern must be scoped to the resolved vault
- append only after reading current note; avoid fragile unanchored rewrites

## Verification

- [ ] vault path is concrete and intended
- [ ] operation used correct file-tool target/mode
- [ ] created/edited note remains valid Markdown
- [ ] append/edit preserves existing content and anchor intent
- [ ] wikilinks use `[[Note Name]]` syntax