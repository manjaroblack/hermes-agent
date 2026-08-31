---
name: apple-reminders
description: "Apple Reminders via remindctl: add, list, complete."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Reminders, tasks, todo, macOS, Apple]
prerequisites:
  commands: [remindctl]
---

# Apple Reminders

role: macOS Reminders operator
do: manage Reminders.app through `remindctl`; preserve iCloud sync to Apple devices
¬: cron alerts, calendar events, project trackers; do not infer which "remind me" means

## When to Use

- user says "reminder" or "Reminders app"
- create personal to-dos with due dates synced to iOS
- manage Apple Reminders lists or tasks intended for iPhone/iPad

¬use: agent alerts → `cronjob`; calendar events → Apple Calendar/Google Calendar; project work → GitHub Issues/Notion/etc. If "remind me" could mean an agent alert, clarify first.

## Prerequisites

- macOS + Reminders.app
- install: `brew install steipete/tap/remindctl`
- grant Reminders permission when prompted
- inspect/request authorization: `remindctl status` / `remindctl authorize`

## Quick Reference

### View

```bash
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date
```

### Lists

```bash
remindctl list               # List all lists
remindctl list Work           # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list
```

### Create

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### Due time vs alarm / early nudge

`--due` writes the reminder due date/time. `--alarm` writes the EventKit alarm/notification trigger. Timed due reminders may default to an alarm at due time; pass `--alarm` explicitly for an earlier nudge:

```bash
remindctl add --title "Hairdresser" --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

Edit an existing reminder:

```bash
remindctl edit 87354 --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

The UI may group by alarm time because that is when notification fires; verify actual fields with JSON, not UI placement:

```bash
remindctl today --json
```

Expected fields:
- `dueDate`: actual due time
- `alarmDate`: notification / early-nudge time

Apple's public `EKReminder` docs list reminder-specific properties; alarm support comes from inherited `EKCalendarItem` behavior exposed by remindctl's `--alarm` flag.

### Complete / delete

```bash
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID
```

### Output formats

```bash
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

## Date Formats

`--due` and date filters accept:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

## Procedure

1. Resolve Apple Reminders vs cron/calendar/project intent; clarify ambiguous "remind me".
2. Confirm reminder content and due date before creation; confirm list and alarm when supplied.
3. Use `--json` for programmatic parsing; use IDs returned by listing for completion/deletion/edit.
4. After edits involving an alarm, inspect `dueDate` and `alarmDate` separately.

## Pitfalls

- Never equate alarm time with due time; the notification may make the UI appear to move.
- Do not create before confirming content and due date.
- `--force` deletion is destructive; verify ID and user intent.
- `remindctl` and these commands require macOS Reminders permissions.

## Verification

- `remindctl status` succeeds and authorization is present
- list output or `--json` confirms target list/ID
- create/edit: verify `dueDate`, `alarmDate`, title, and list
- complete/delete: rerun a list query and confirm the intended ID changed state
