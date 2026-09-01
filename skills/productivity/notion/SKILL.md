---
name: notion
description: "Notion API + ntn CLI: pages, databases, markdown, Workers."
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [NOTION_API_KEY]
metadata:
  hermes:
    tags: [Notion, Productivity, Notes, Database, API, CLI, Workers]
    homepage: https://developers.notion.com
---

# Notion

role: Notion page/database/file/Worker operator
do: authenticate integration; choose `ntn` or HTTP; read/search/create/update/query; upload files; deploy Workers; use Notion Markdown; verify mutations
inputs: integration token, shared page/database, page/data-source IDs, Markdown/properties/query, Worker source/secrets/capability
outputs: pages/blocks/data-source records, files, query JSON, Worker/deployment/webhook state
¬: `ntn login`/separate OAuth; use unshared targets; expose token/webhook URL; mutate without scope; assume database/data-source IDs interchangeable; create Worker on unsupported plan/OS; treat `>`/`$` Markdown syntax as ordinary text

One integration token serves both paths:

- `ntn` official CLI: shorter syntax, one-line uploads, Workers; macOS/Linux
  only as of May 2026; default when installed
- HTTP + `curl`: cross-platform, Windows fallback

## When to Use

- search/read/create/update pages and database/data-source records
- read/write Notion-flavored Markdown or blocks
- upload files
- build/deploy syncs, tools, webhooks (Workers)
- Windows or no `ntn` → HTTP path

## Procedure

1. Configure private integration token; share exact target page/database.
2. Choose `ntn` or HTTP path from OS + installed CLI; pin API version.
3. Resolve page/database/data-source IDs and inspect current properties/blocks.
4. Execute scoped query/mutation/upload/Worker operation; respect rate limits.
5. Read back response/state and complete Verification.

## Setup

### 1. Integration token

1. Create integration: https://notion.so/my-integrations
2. Copy API key (`ntn_` or `secret_`)
3. Store in `${HERMES_HOME:-~/.hermes}/.env`:

   ```
   NOTION_API_KEY=ntn_your_key_here
   ```

4. Share target pages/databases: page `...` → `Connect to` → integration.
   Without sharing, API returns 404 even when page exists.

### 2. Install `ntn` (macOS/Linux)

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

Skip `ntn login`; use integration token headlessly:

```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

Persist exports in shell profile or `${HERMES_HOME:-~/.hermes}/.env`.

### 3. Runtime path

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl
fi
```

Windows: skip `ntn` until native support; Path B works. WSL2 provides CLI
ergonomics now.

## API Basics

All HTTP requests require `Notion-Version: 2025-09-03`; `ntn` supplies it.
In this API, “databases” are **data sources**.

## Path A — `ntn` (macOS/Linux)

### Raw API shorthand

```bash
ntn api v1/users                                  # GET
ntn api v1/pages parent[page_id]=abc123 \         # POST with inline body
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

Syntax: `key=value` string; `key[nested]=value` nested object;
`key:=value` typed bool/number/null/array.

### Search/read

```bash
ntn api v1/search query="page title"
```

```bash
ntn api v1/pages/{page_id}
```

```bash
ntn api v1/pages/{page_id}/markdown
```

```bash
ntn api v1/blocks/{page_id}/children
```

### Create/patch Markdown

```bash
ntn api v1/pages \
  parent[page_id]=xxx \
  properties[title][0][text][content]="Notes from meeting" \
  markdown="# Agenda

- Q3 roadmap
- Hiring"
```

```bash
ntn api v1/pages/{page_id}/markdown -X PATCH \
  markdown="## Update

Shipped the prototype."
```

### Query data source

```bash
ntn api v1/data_sources/{data_source_id}/query -X POST \
  filter[property]=Status filter[select][equals]=Active
```

Complex sorts/multiple/compound filters: pipe JSON:

```bash
echo '{"filter": {"property": "Status", "select": {"equals": "Active"}}, "sorts": [{"property": "Date", "direction": "descending"}]}' | \
  ntn api v1/data_sources/{data_source_id}/query -X POST --json -
```

### Files

```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

This replaces HTTP create-upload → PUT bytes → reference flow.

### Environment

| Var | Effect |
|---|---|
| `NOTION_API_TOKEN` | Auth token (overrides keychain) — set this to your integration token |
| `NOTION_KEYRING=0` | File-based creds at `~/.config/notion/auth.json` instead of OS keychain |
| `NOTION_WORKSPACE_ID` | Skip the workspace picker prompt |

## Path B — HTTP + `curl`

Common request:

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

Windows 10+ `curl` works; PowerShell also supports `Invoke-RestMethod`.

### Search/page/blocks

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03"
```

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03"
```

Markdown is easier for a model than block JSON.

```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03"
```

### Create/patch pages

`POST /v1/pages` accepts `markdown`:

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "properties": {"title": [{"text": {"content": "Notes from meeting"}}]},
    "markdown": "# Agenda\n\n- Q3 roadmap\n- Hiring\n\n## Decisions\n- Ship MVP Friday"
  }'
```

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "## Update\n\nShipped the prototype."}'
```

Create in data source/database:

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### Query/create data source

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

### Update properties/append blocks

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

### File uploads (3 steps)

```bash
# 1. Create upload
curl -s -X POST "https://api.notion.com/v1/file_uploads" \
  -H "Authorization: Bearer ***" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.png", "content_type": "image/png"}'

# 2. PUT bytes to the upload_url returned above
curl -s -X PUT "{upload_url}" --data-binary @photo.png

# 3. Reference {file_upload_id} in a page/block payload
```

## Property Types

- title: `{"title": [{"text": {"content": "..."}}]}`
- rich text: `{"rich_text": [{"text": {"content": "..."}}]}`
- select: `{"select": {"name": "Option"}}`
- multi-select: `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- date: `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- checkbox: `{"checkbox": true}`
- number: `{"number": 42}`
- URL: `{"url": "https://..."}`
- email: `{"email": "user@example.com"}`
- relation: `{"relation": [{"id": "page_id"}]}`

## API 2025-09-03: Database vs Data Source

- database became data source; query/retrieval uses `/data_sources/`
- two IDs: `database_id` + `data_source_id`
  - page creation: `parent: {"database_id": "..."}`
  - query: `POST /v1/data_sources/{id}/query`
- search returns `"object": "data_source"` with `data_source_id`

## Notion Workers (advanced; requires `ntn`)

Workers are TypeScript programs hosted by Notion:

- syncs: external API → Notion database on schedule (default 30 min)
- tools: callable inside Notion Custom Agents
- webhooks: external events (GitHub, Stripe, etc.) → Notion actions

Gating: CLI all plans; deploy requires Business/Enterprise; macOS/Linux only
as of May 2026 (Windows WSL2/wait); free through Aug 11, 2026, then Notion
credits metered.

### Minimal Worker

```bash
ntn workers new my-worker      # scaffold
cd my-worker
# Edit src/index.ts
ntn workers deploy --name my-worker
```

`src/index.ts`:

```typescript
import { Worker } from "@notionhq/workers";

const worker = new Worker();
export default worker;

worker.tool("greet", {
  title: "Greet a User",
  description: "Returns a friendly greeting",
  inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  execute: async ({ name }) => `Hello, ${name}!`,
});
```

### Webhook

```typescript
worker.webhook("onGithubPush", {
  title: "GitHub Push Handler",
  execute: async (events, { notion }) => {
    for (const event of events) {
      // event.body, event.rawBody (for signature verification), event.headers
      console.log("got delivery", event.deliveryId);
    }
  },
});
```

After deploy `ntn workers webhooks list` yields Notion URL. Treat URL as secret:
anyone with it can POST unless signature verification is added.

### Lifecycle

```bash
ntn workers deploy
ntn workers list
ntn workers exec <capability-key> -d '{"name": "world"}'
ntn workers sync trigger <key>            # run a sync now
ntn workers sync pause <key>
ntn workers env set GITHUB_WEBHOOK_SECRET=...
ntn workers runs list                     # recent invocations
ntn workers runs logs <run-id>
ntn workers webhooks list
```

Worker request: scaffold `ntn workers new`, edit `src/index.ts`, set secrets
with `ntn workers env set`, deploy. Full API: https://developers.notion.com/workers.

## Notion-Flavored Markdown

CommonMark + XML-like Notion blocks. Use **tabs** for indentation.

```
<callout icon="🎯" color="blue_bg">
	Ship the MVP by **Friday**.
</callout>

<details color="gray">
<summary>Toggle title</summary>
	Children indented one tab
</details>

<columns>
	<column>Left side</column>
	<column>Right side</column>
</columns>

<table_of_contents color="gray"/>
```

Inline forms: `<mention-user url="..."/>`,
`<mention-page url="...">Title</mention-page>`,
`<mention-date start="2026-05-15"/>`; underline
`<span underline="true">text</span>`; color `<span color="blue">text</span>`
or `{color="blue"}` first line; math `$x^2$`, `$$ ... $$`; citations
`[^https://example.com]`.

Colors: `gray brown orange yellow green blue purple pink red` + `*_bg`.
Headings 5/6 collapse to H4. Multiple `>` lines become separate quote blocks;
use `<br>` inside one `>` for multiline quote.

## Choose Path

| Task | mac / Linux | Windows |
|---|---|---|
| Read/write pages, search, query databases | `ntn api ...` | curl |
| Read a page for an agent to summarize | `ntn api v1/pages/{id}/markdown` | curl `/markdown` endpoint |
| Upload a file | `ntn files create < file` | 3-step HTTP flow |
| One-off API exploration | `ntn api ...` | curl |
| Build sync/webhook/agent tool hosted by Notion | `ntn workers ...` | WSL2 + `ntn workers ...` |

## Pitfalls

- page/database IDs UUID with or without dashes
- rate ~3 requests/sec average; CLI does not bypass
- API cannot set database **view** filters (UI only)
- `"is_inline": true` embeds new data source in page
- always `-s` on curl; pipe JSON with `jq`, e.g. `... | jq '.results[0].properties'`
- Notion MCP exists (~91% more token-efficient on DB ops than prior version);
  wire through Hermes MCP when streaming access is desired; paths above cover most one-shot tasks

## Verification

- [ ] integration token private; target page/database shared
- [ ] API version `2025-09-03`; database/data-source endpoint/ID correct
- [ ] selected path matches OS/CLI availability
- [ ] mutations/query/upload response inspected and read back where possible
- [ ] Worker plan/entitlement, secrets, deploy, runs, and webhook URL handled safely
- [ ] Markdown tabs/XML blocks preserved as intended