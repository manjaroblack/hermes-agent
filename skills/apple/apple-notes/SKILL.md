---
name: apple-notes
description: "Manage Apple Notes via memo CLI: create, search, edit."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
---

# Apple Notes

role: macOS Notes operator
do: manage Notes.app through `memo`; preserve iCloud sync across Apple devices
outputs: listed, created, edited, deleted, moved, or exported notes
¬: Bear Notes; agent-only memory; unsupported image/attachment edits

## When to Use

- create, view, search, or organize Apple Notes
- save information to Notes.app for iPhone/iPad/Mac access
- filter by folder; export to Markdown or HTML

## Prerequisites

- macOS + Notes.app
- install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- grant Automation access to Notes.app when prompted: System Settings → Privacy → Automation

## Quick Reference

### View

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create

```bash
memo notes -a                     # Add a note (opens your $EDITOR)
memo notes -a -f "Folder Name"    # Add a note into a specific folder
```

`-a`/`--add` is a bare flag; it opens `$EDITOR` and accepts no title argument. Set `$EDITOR` first, e.g. `export EDITOR=vim`. Use `-f/--folder` for the destination folder.

### Edit, delete, move

```bash
memo notes -e                     # Interactive selection to edit
memo notes -d                     # Interactive selection to delete
memo notes -m                     # Move note to folder (interactive)
```

### Export

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Procedure

1. Confirm macOS, Notes.app, `memo`, and Automation permission.
2. Resolve intent: cross-device note → Notes; Markdown-native knowledge base → `obsidian`; ephemeral agent note → `memory`.
3. For interactive commands (`-e`, `-d`, `-m`, or editor composition), use a terminal with `pty=true`.
4. Run the narrowest command above; report result and destination folder/path.

## Pitfalls

- Notes containing images or attachments cannot be edited.
- Interactive prompts require terminal access; use `pty=true` when needed.
- macOS only; Apple Notes.app is required.
- Do not claim cross-device sync unless the user is using iCloud-backed Apple Notes.

## Verification

- list/search result matches requested folder or query
- after create/edit/move/export, rerun the relevant `memo` command and confirm the result
- confirm exported HTML/Markdown path
- preserve boundaries: `obsidian` for Obsidian vaults, `memory` for agent-internal notes, no Bear support
