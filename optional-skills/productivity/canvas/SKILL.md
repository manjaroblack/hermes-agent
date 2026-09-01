---
name: canvas
description: Fetch Canvas LMS courses and assignments via API token.
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [CANVAS_API_TOKEN, CANVAS_BASE_URL]
metadata:
  hermes:
    tags: [Canvas, LMS, Education, Courses, Assignments]
---

# Canvas LMS

role: read-only Canvas course/assignment information operator
do: configure token/base URL; list active/all courses; list/order assignments; paginate; report auth/rate-limit failures
inputs: Canvas instance URL; API token; enrollment state; course ID; due-date ordering
outputs: course/assignment JSON; full-assignment URL; pagination-aware results; troubleshooting guidance
¬: modify LMS data; expose tokens; guess institution URL; treat 401/403 as empty data; report truncated description as complete

Read-only Canvas LMS access for listing courses and assignments. Helper:
`scripts/canvas_api.py`; calls use Canvas REST API with an API token.

## When to Use

- list active courses or all enrollment states
- list assignments for a course, optionally ordered by due date
- inspect course metadata or assignment links/descriptions

## Prerequisites

1. Log in to the Canvas instance in a browser.
2. Open **Account → Settings**.
3. In **Approved Integrations**, select **+ New Access Token**.
4. Name token (e.g. "Hermes Agent"), optionally set expiry, select **Generate Token**.
5. Store token and no-trailing-slash base URL in `${HERMES_HOME:-~/.hermes}/.env`:

```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://yourschool.instructure.com
```

Base URL is the browser URL while logged in; do not invent an institution.

## Procedure

### 1. Query courses and assignments

```bash
CANVAS="python $HERMES_HOME/skills/productivity/canvas/scripts/canvas_api.py"

# List all active courses
$CANVAS list_courses --enrollment-state active

# List all courses (any state)
$CANVAS list_courses

# List assignments for a specific course
$CANVAS list_assignments 12345

# List assignments ordered by due date
$CANVAS list_assignments 12345 --order-by due_at
```

### 2. Parse output

`list_courses` returns:

```json
[{"id": 12345, "name": "Intro to CS", "course_code": "CS101", "workflow_state": "available", "start_at": "...", "end_at": "..."}]
```

`list_assignments` returns:

```json
[{"id": 67890, "name": "Homework 1", "due_at": "2025-02-15T23:59:00Z", "points_possible": 100, "submission_types": ["online_upload"], "html_url": "...", "description": "...", "course_id": 12345}]
```

Descriptions are truncated to 500 characters; `html_url` is the full Canvas
assignment page.

### 3. Use direct API when needed

```bash
# List courses
curl -s -H "Authorization: Bearer ***" \
  "$CANVAS_BASE_URL/api/v1/courses?enrollment_state=active&per_page=10"

# List assignments for a course
curl -s -H "Authorization: Bearer ***" \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments?per_page=10&order_by=due_at"
```

Canvas paginates via `Link` headers; the Python helper follows pagination.

## Pitfalls

- read-only: helper fetches only; never modify courses/assignments
- first use: run `$CANVAS list_courses`; 401 means guide token setup, not an empty course list
- rate limit is approximately 700 requests per 10 minutes; inspect `X-Rate-Limit-Remaining` when near limit
- 403 means token lacks permission for that course
- empty list: try `--enrollment-state active` or omit flag for all states
- wrong institution: verify `CANVAS_BASE_URL` matches browser URL
- timeout: check connectivity to Canvas instance
- keep API token out of messages, logs, and durable notes

## Verification

| Problem | Fix |
|---------|-----|
| 401 Unauthorized | Token invalid or expired — regenerate in Canvas Settings |
| 403 Forbidden | Token lacks permission for this course |
| Empty course list | Try `--enrollment-state active` or omit the flag to see all states |
| Wrong institution | Verify `CANVAS_BASE_URL` matches the URL in your browser |
| Timeout errors | Check network connectivity to your Canvas instance |

Successful verification returns parseable course/assignment JSON, expected
course IDs, and assignment `html_url` values without revealing credentials.