---
name: airtable
description: Airtable REST API via curl. Records CRUD, filters, upserts.
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [AIRTABLE_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Airtable, Productivity, Database, API]
    homepage: https://airtable.com/developers/web/api/introduction
---

# Airtable — Bases, Tables + Records

role: Airtable REST operator via Hermes `terminal`
do: authenticate PAT; inspect bases/schema; read/filter/sort/page; create/update/upsert/delete records; verify and respect limits
inputs: PAT, base/table/record IDs, field names, formula/filter, JSON body, mutation scope
outputs: JSON records/schema, deterministic filtered results, verified mutations
¬: legacy `key...` keys; wrong-base access; guess IDs/fields; hand-encode formulas; `PUT` by default; delete broad scope without count+confirmation; print token

## When to Use

- CRUD records with `curl`
- filter/sort/page/query Airtable data
- inspect schema before mutation
- idempotent upsert by merge field
- batch inserts/deletes under API limits

## Procedure

1. Resolve PAT scopes + exact base/table IDs; inspect schema before field writes.
2. Choose read/filter/sort/page or create/update/upsert/delete path below.
3. Encode formulas/JSON mechanically; preview record count + mutation scope.
4. Execute within batch/rate limits; back off on `429` without duplicate writes.
5. Read back records/schema and complete Verification.

## Prerequisites

1. Create PAT: https://airtable.com/create/tokens (prefix `pat...`).
2. Minimum scopes: `data.records:read`, `data.records:write`,
   `schema.bases:read`.
3. Add every target base to token **Access**; PATs are per-base and wrong-base
   access returns `403`.
4. Store in `${HERMES_HOME:-~/.hermes}/.env` or `hermes setup`:

   ```
   AIRTABLE_API_KEY=pat_your_token_here
   ```

Legacy `key...` API keys were deprecated Feb 2024; PAT/OAuth only.

## API Contract

- endpoint: `https://api.airtable.com/v0`
- auth: `Authorization: Bearer $AIRTABLE_API_KEY`
- JSON bodies require `Content-Type: application/json` for POST/PATCH/PUT
- IDs: bases `app...`, tables `tbl...`, records `rec...`, fields `fld...`;
  IDs stable, names mutable → prefer IDs in automations
- rate: 5 requests/sec/base; `429` → back off

Base request:

```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=5" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

Keep `-s`; pretty-print with `python -m json.tool` (always present) or `jq`.

## Field Shapes

| Field type | Write shape |
|---|---|
| Single line text | `"Name": "hello"` |
| Long text | `"Notes": "multi\nline"` |
| Number | `"Score": 42` |
| Checkbox | `"Done": true` |
| Single select | `"Status": "Todo"` (name must already exist unless `typecast: true`) |
| Multi-select | `"Tags": ["urgent", "bug"]` |
| Date | `"Due": "2026-04-01"` |
| DateTime (UTC) | `"At": "2026-04-01T14:30:00.000Z"` |
| URL / Email / Phone | `"Link": "https://…"` |
| Attachment | `"Files": [{"url": "https://…"}]` (Airtable fetches + rehosts) |
| Linked record | `"Owner": ["recXXXXXXXXXXXXXX"]` (array of record IDs) |
| User | `"AssignedTo": {"id": "usrXXXXXXXXXXXXXX"}` |

Top-level `"typecast": true` lets Airtable coerce values, create select
options, and convert `"42"` → `42`.

## Reads

List bases:

```bash
curl -s "https://api.airtable.com/v0/meta/bases" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

List base tables/schema (always before mutation):

```bash
curl -s "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

This confirms field names/IDs, select `options.choices`, and primary field.

Records:

```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=10" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

Formula filters require URL encoding; use Python stdlib, never hand-encode:

```bash
FORMULA="{Status}='Todo'"
ENC=$(python -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$FORMULA")
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?filterByFormula=$ENC&maxRecords=20" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

Formula patterns: exact `{Email}='user@example.com'`; contains
`FIND('bug', LOWER({Title}))`; multiple `AND({Status}='Todo', {Priority}='High')`;
OR `OR({Owner}='alice', {Owner}='bob')`; nonempty `NOT({Assignee}='')`;
date `IS_AFTER({Due}, TODAY())`.

Sort/select:

```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?sort%5B0%5D%5Bfield%5D=Priority&sort%5B0%5D%5Bdirection%5D=asc&fields%5B%5D=Name&fields%5B%5D=Status" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

Square brackets must be `%5B`/`%5D`.

Named view:

```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?view=Grid%20view&maxRecords=50" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

View applies saved filter + sort server-side.

## Mutations

Create:

```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Name":"New task","Status":"Todo","Priority":"High"}}' | python -m json.tool
```

Batch create (max 10):

```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "typecast": true,
    "records": [
      {"fields": {"Name": "Task A", "Status": "Todo"}},
      {"fields": {"Name": "Task B", "Status": "In progress"}}
    ]
  }' | python -m json.tool
```

Loop batches of 10 with a short sleep; respect 5 req/sec/base.

PATCH merges/preserves omitted fields:

```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Status":"Done"}}' | python -m json.tool
```

Upsert by merge field:

```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{
    "performUpsert": {"fieldsToMergeOn": ["Email"]},
    "records": [
      {"fields": {"Email": "user@example.com", "Status": "Active"}}
    ]
  }' | python -m json.tool
```

New merge value creates; existing value patches; useful for idempotent sync.

Delete one:

```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

Delete up to 10:

```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE?records%5B%5D=rec1&records%5B%5D=rec2" \
  -H "Authorization: Bearer ***" | python -m json.tool
```

## Pagination

At most 100 records/page. If response has `"offset"`, pass it until absent:

```bash
OFFSET=""
while :; do
  URL="https://api.airtable.com/v0/$BASE_ID/$TABLE?pageSize=100"
  [ -n "$OFFSET" ] && URL="$URL&offset=$OFFSET"
  RESP=$(curl -s "$URL" -H "Authorization: Bearer ***")
  echo "$RESP" | python -c 'import json,sys; d=json.load(sys.stdin); [print(r["id"], r["fields"].get("Name","")) for r in d["records"]]'
  OFFSET=$(echo "$RESP" | python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("offset",""))')
  [ -z "$OFFSET" ] && break
done
```

## Hermes Runbook

1. Auth probe: `curl -s -o /dev/null -w "%{http_code}\n" https://api.airtable.com/v0/meta/bases -H "Authorization: Bearer ***"`; expect `200`.
2. Find base: list bases or ask for `app...` when token lacks schema scope.
3. Inspect `GET /v0/meta/bases/$BASE_ID/tables`; cache exact field/primary names
   in session before writes.
4. Read before write: filter to resolve `rec...`, then PATCH; never guess IDs.
5. Batch related creates in 10-record requests.
6. Delete: echo filter + count and confirm; API deletion is not undoable.

## Pitfalls

- URL-encode `filterByFormula`; fields with spaces/non-ASCII need encoding;
  `{My Field}` → `%7BMy%20Field%7D`; use Python `urllib.parse.quote`.
- Missing response field usually means empty value, not absent schema; inspect schema.
- PATCH merges; PUT replaces and clears omitted fields → default PATCH.
- Single-select option must exist; `typecast: true` can create it; otherwise
  `INVALID_MULTIPLE_CHOICE_OPTIONS`.
- 403 on one base with another working usually means token Access omission;
  grant at https://airtable.com/create/tokens.
- Limit is per base: 5 req/s on each base is fine; 6 on one throttles;
  inspect `Retry-After` on `429`.

## Hermes Notes

- Use `terminal` + `curl`; `web_extract` cannot send auth headers and
  `browser_navigate` requires slow UI auth.
- `AIRTABLE_API_KEY` loads from `${HERMES_HOME:-~/.hermes}/.env`; no repeated export.
- `{Status}` is literal in heredoc; dynamic formula strings go through
  `python urllib.parse.quote` before URL splicing.
- Prefer `python -m json.tool`; use `jq` only for filtering/projection.
- Pagination is hard 100/page; loop `offset`.
- Read `errors` on non-2xx: `AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS`,
  `MODEL_ID_NOT_FOUND`, `INVALID_MULTIPLE_CHOICE_OPTIONS` identify causes.

## Verification

- [ ] PAT scopes + target-base Access confirmed; token hidden.
- [ ] schema read before field mutation; IDs not guessed.
- [ ] formulas/query brackets encoded; pagination reaches offset absence.
- [ ] writes respect 10-record/5 req/s limits and use PATCH/upsert where apt.
- [ ] delete scope/count confirmed; response/errors inspected; result read back.