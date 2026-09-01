---
name: weekly-review-planning
description: "Weekly reset: commitments, stalled work, next-week plan."
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Weekly-Review, Planning, Tasks, Calendar, Productivity]
    related_skills: [obsidian, notion, airtable, google-workspace, email-inbox-triage]
---

# Weekly Review + Planning

role: bounded cross-system weekly reviewer
do: set window/sources; review calendar; clear capture; reconcile projects; inspect waiting/commitments; fit capacity plan; apply approved updates/read back
inputs: timezone, completed week, 1–2 week horizon, task/project store, calendar, notes, inboxes, write scope
outputs: wins, risks, waiting, stalled projects, capacity-aware plan, proposed updates, coverage gaps
¬: generic productivity method; daily brief (use `google-workspace`); single-inbox triage (use `email-inbox-triage`); mutate without approval; carry everything as priority; infer silence = completion

The `weekly-review` Automation Blueprint schedules the recurring cron job.

## When to Use

- run weekly review/reset
- find commitments/slippage, stale projects, waiting items
- plan next week from calendar/tasks/notes
- execute scheduled weekly-review tick

## Procedure

### 1. Scope

Confirm timezone, review period, horizon, authoritative task/project store,
calendars, inboxes, and allowed writes. Default recommendations/drafts; declare
winner for source conflicts.
Done when: scope, authority, period, horizon, and write boundary are explicit.

### 2. Calendar evidence

Use `google-workspace` or calendar connector. Inspect completed-week meetings /
commitments and next 1–2 weeks for deadlines, travel, prep, capacity, implied
follow-ups, and conflicts.
Done when: calendar load, constraints, and follow-ups are captured with sources.

### 3. Capture inboxes

Review task inbox, `obsidian`, `notion`, flagged email (`email-inbox-triage`
owns thread triage), and declared capture points. Classify next action, project,
waiting, scheduled, someday, reference, archive, or delete proposal. Count
remaining unprocessed items; do not mutate before approval.
Done when: every capture point is classified and unprocessed count is stated.

### 4. Active projects

For each: outcome, next action, owner, deadline, blocker, last meaningful
activity, source link. Flag no-next-action, missed date, duplicate, or
contradictory status. Every project actionable or explicitly paused.
Done when: each project has outcome, next action, owner, date, blocker, and status.

### 5. Waiting + commitments

Find user promises and items owed by others. Propose follow-up date/channel;
silence never implies completion. Each waiting item gets owner + next review date.
Done when: every waiting item has owed party, owner, and next review date.

### 6. Capacity plan

Estimate fixed load; choose small weekly outcomes + near-term actions. Rank
consequence, deadline, dependency, effort; do not fill every free hour. Name
deferred work.
Done when: outcomes fit fixed load and deferred work is named.

### 7. Approved updates

Only approved task/project changes, calendar holds, archive actions, and drafts.
Read every changed record back; verify against summary.
Done when: approved writes read back and match the review summary.

## Output Shape

1. Wins/completed commitments
2. Overdue/at risk
3. Waiting/follow-ups
4. Stalled/ambiguous projects
5. Next-week outcomes/calendar constraints
6. Proposed updates awaiting approval
7. Coverage gaps

## Pitfalls

- plan without calendar capacity
- promote every unfinished item
- call project active without next action
- silently delete/reschedule personal commitments
- treat others' silence as completion

## Verification

- [ ] Completed week + horizon covered, or gaps stated.
- [ ] Stalls/waiting trace to record/event/thread.
- [ ] No mutation without approval; approved writes read back.
- [ ] Deferred work named explicitly.