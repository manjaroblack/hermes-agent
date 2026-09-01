---
name: google-workspace
description: Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
version: 1.2.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

role: Hermes-managed Google Workspace operator
do: choose service scopes; OAuth setup/verify/revoke; use `gws` when installed; fallback to bundled `google_api.py`; read/send/update with approval; parse JSON
inputs: service set, OAuth client-secret path/redirect code, Gmail query, event/file/sheet/doc parameters, user approval
outputs: Gmail/Calendar/Drive/Contacts/Sheets/Docs JSON, OAuth state, verified writes
¬: ask OAuth credentials in chat; request unnecessary scopes; treat email-only as needing Cloud project; send/delete/share/mutate without confirmation; timezone-less events; expose token/client secret; retry stale OAuth code without fresh URL

`gws` is preferred when installed; bundled Python client preserves the JSON
contract as fallback. `himalaya` is the 2-minute Gmail App Password path for
email-only users.

## When to Use

- Gmail search/read/send/reply/labels
- Calendar list/create/delete
- Drive search/get/upload/download/folders/sharing/trash
- Contacts, Sheets, Docs read/create/update/append
- morning brief → [references/daily-brief.md](references/daily-brief.md)

## Procedure

1. Load relevant references; choose minimal service set + host/auth topology.
   For complex Gmail queries, load
   `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
2. Run First-Time Setup only when `--check` is not fully authenticated.
3. Prefer `gws`; otherwise use bundled wrapper and its JSON contract.
4. Preview recipients/IDs/content/timezone + confirm consequential writes.
5. Execute, inspect JSON, read back mutations, and complete Verification.

## References + Scripts

- [references/gmail-search-syntax.md](references/gmail-search-syntax.md): `is:unread`, `from:`, `newer_than:`, etc.
- [references/daily-brief.md](references/daily-brief.md): schedule/conflicts/prep/urgent mail
- `scripts/setup.py`: OAuth2 setup
- `scripts/google_api.py`: `gws`-first compatibility wrapper + JSON output

## First-Time Setup (non-interactive steps)

Define:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### 0. Check

```bash
$GSETUP --check
```

`AUTHENTICATED` → skip setup. `AUTHENTICATED (partial)` may mean reauthorization
for newer write scopes.

### 1. Scope triage — ask two questions

Ask: **“What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?”**

- email only → do not use this skill; load `himalaya` (Gmail App Password via
  Settings → Security → App Passwords; no Cloud project)
- email + Calendar → `--services email,calendar`
- calendar/Drive/Sheets/Docs only → narrow set such as
  `calendar,drive,sheets,docs`
- full Workspace → `all`

Ask: **“Does your Google account use Advanced Protection (hardware security
keys required to sign in)? If you're not sure, you probably don't — it's
something you would have explicitly enrolled in.”**

No/not sure → normal path. Yes → Workspace admin must allowlist OAuth client ID
before authorization.

### 2. Create OAuth client (~5 minutes)

Tell the user:

1. create/select project:
   https://console.cloud.google.com/projectselector2/home/dashboard
2. API Library https://console.cloud.google.com/apis/library: enable Gmail,
   Calendar, Drive, Sheets, Docs, People APIs
3. credentials https://console.cloud.google.com/apis/credentials → Create
   Credentials → OAuth 2.0 Client ID
4. application type `Desktop app` → Create
5. Testing app: audience https://console.cloud.google.com/auth/audience →
   Audience → Test users → Add users
6. download JSON and provide file path

CLI note: an absolute path alone can be mistaken for slash command; send a
sentence: `The JSON file path is: ~/Downloads/client_secret_....json`.

Then:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

If only raw client ID/secret values arrive, write valid Desktop OAuth JSON to
an explicit local file (e.g. `~/Downloads/hermes-google-client-secret.json`),
then pass `--client-secret`; never request/store secrets in chat/config/commit.

### 3. Authorization URL

Use service choice:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

Returns JSON `auth_url`; saves exact URL at `~/.hermes/google_oauth_last_url.txt`.
Send exact `auth_url` as one line. Warn: browser likely fails at
`http://localhost:1` after approval; expected. User must copy the entire
redirect URL. `Error 403: access_denied` → add account at
https://console.cloud.google.com/auth/audience.

### 4. Exchange code

Accept URL `http://localhost:1/?code=4/0A...&scope=...` or code only. Pending
PKCE state is stored locally by `--auth-url`:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

Expired/used/old-tab code returns `fresh_auth_url`; immediately send it and use
only newest browser redirect.

### 5. Verify

```bash
$GSETUP --check
```

Must print `AUTHENTICATED`; refresh is automatic.

### State + revoke

- token: `~/.hermes/google_token.json`, auto-refresh
- pending OAuth session/verifier: `~/.hermes/google_oauth_pending.json` until exchange
- installed `gws` uses same token; no separate `gws auth login`
- revoke: `$GSETUP --revoke`

## Usage

Define API wrapper:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

## JSON Output Contract

All commands return JSON. Key shapes:

- Gmail search: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- Gmail get: `{id, threadId, from, to, subject, date, labels, body}`
- Gmail send/reply: `{status: "sent", id, threadId}`
- Calendar list: `[{id, summary, start, end, location, description, htmlLink}]`
- Calendar create: `{status: "created", id, summary, htmlLink}`
- Drive search: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- Drive get: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- Drive upload: `{status: "uploaded", id, name, mimeType, webViewLink}`
- Drive download: `{status: "downloaded", id, name, path, mimeType}`
- Drive create-folder: `{status: "created", id, name, webViewLink}`
- Drive share: `{status: "shared", permissionId, fileId, role, type}`
- Drive delete: `{status: "trashed" | "deleted", fileId, permanent}`
- Contacts list: `[{name, emails: [...], phones: [...]}]`
- Sheets get: `[[cell, cell, ...], ...]`
- Sheets create: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- Docs create: `{status: "created", documentId, title, url}`
- Docs append: `{status: "appended", documentId, inserted_at, characters}`

## Rules

1. Confirm first: email send, Calendar create/delete, Drive delete/share,
   Docs/Sheets modifications. Show recipients, IDs, content, role. Prefer Drive
   trash over `--permanent`.
2. Run `setup.py --check` before first use; repair setup if fail.
3. Complex Gmail query → load [references/gmail-search-syntax.md](references/gmail-search-syntax.md).
4. Calendar start/end always ISO 8601 with offset or `Z`.
5. Respect API limits; batch reads and avoid rapid-fire calls.

## Pitfalls

Troubleshooting:

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoke

```bash
$GSETUP --revoke
```

## Verification

- [ ] service scope choice and topology/Advanced Protection triage complete
- [ ] OAuth client file/token remain private; `--check` prints `AUTHENTICATED`
- [ ] API wrapper selected (`gws` or bundled fallback) and JSON contract preserved
- [ ] every mutating action received confirmation and was read back where supported
- [ ] Calendar timezone, Gmail thread/labels, Drive trash/share role, Sheets/Docs IDs recorded