---
name: siyuan
description: Query and edit a SiYuan knowledge base via its API.
version: 1.0.0
author: FEUAZUR
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [SiYuan, Notes, Knowledge Base, PKM, API]
    related_skills: [obsidian, notion]
    homepage: https://github.com/siyuan-note/siyuan
prerequisites:
  env_vars: [SIYUAN_TOKEN]
  commands: [curl, jq]
required_environment_variables:
  - name: SIYUAN_TOKEN
    prompt: SiYuan API token
    help: "Settings > About in SiYuan desktop app"
  - name: SIYUAN_URL
    prompt: SiYuan instance URL (default http://127.0.0.1:6806)
    required_for: remote instances
---

# SiYuan Note API

role: SiYuan knowledge-base query/edit operator
do: configure local/remote endpoint; authenticate; search/read/create/update/delete blocks/documents; manage notebooks/attributes; export Markdown; use safe SQL; report API errors
inputs: SiYuan URL/token; query/page; notebook/document/block ID; Markdown/Kramdown; attributes; SQL SELECT; MCP config
outputs: code-checked JSON/data; block/document/notebook result; exported Markdown; explicit mutation/error status
¬: GET requests; SQL mutation; invalid IDs; process data when `code != 0`; expose token; edit database directly; assume numeric IDs; claim failed mutations succeeded

Use the self-hosted [SiYuan](https://github.com/siyuan-note/siyuan) kernel API
with `curl` and an API token. No extra tools beyond `curl` and `jq` are needed.

## When to Use

- search or read blocks/documents/notebooks
- create/update/delete notes, blocks, documents, or notebooks
- set custom block attributes
- export document Markdown
- query a knowledge base with read-only SQL

## Prerequisites and Authentication

1. Install and run SiYuan (desktop or Docker).
2. Get API token at **Settings > About > API token**.
3. Store in `${HERMES_HOME:-~/.hermes}/.env`:

   ```
   SIYUAN_TOKEN=your_token_here
   SIYUAN_URL=http://127.0.0.1:6806
   ```

`SIYUAN_URL` defaults to `http://127.0.0.1:6806` when unset.

## Procedure

### 1. Apply API contract

All calls are POST with JSON body:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/..." \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

Response:

```json
{"code": 0, "msg": "", "data": { ... }}
```

`code: 0` is success; every other code is error and `msg` is authoritative.
IDs have `14-digit timestamp + 7 alphanumeric chars`, e.g.
`20210808180117-6v0mkxr`.

### 2. Select endpoint

| Operation | Endpoint |
|-----------|----------|
| Full-text search | `/api/search/fullTextSearchBlock` |
| SQL query | `/api/query/sql` |
| Read block | `/api/block/getBlockKramdown` |
| Read children | `/api/block/getChildBlocks` |
| Get path | `/api/filetree/getHPathByID` |
| Get attributes | `/api/attr/getBlockAttrs` |
| List notebooks | `/api/notebook/lsNotebooks` |
| List documents | `/api/filetree/listDocsByPath` |
| Create notebook | `/api/notebook/createNotebook` |
| Create document | `/api/filetree/createDocWithMd` |
| Append block | `/api/block/appendBlock` |
| Update block | `/api/block/updateBlock` |
| Rename document | `/api/filetree/renameDocByID` |
| Set attributes | `/api/attr/setBlockAttrs` |
| Delete block | `/api/block/deleteBlock` |
| Delete document | `/api/filetree/removeDocByID` |
| Export as Markdown | `/api/export/exportMdContent` |

### 3. Search/read

Full-text:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/search/fullTextSearchBlock" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"query": "meeting notes", "page": 0}' | jq '.data.blocks[:5]'
```

SQL is restricted to SELECT:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/query/sql" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"stmt": "SELECT id, content, type, box FROM blocks WHERE content LIKE '\''%keyword%'\'' AND type='\''p'\'' LIMIT 20"}' | jq '.data'
```

Useful columns: `id`, `parent_id`, `root_id`, `box` (notebook ID), `path`,
`content`, `type`, `subtype`, `created`, `updated`.

Block Kramdown:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getBlockKramdown" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data.kramdown'
```

Children, human path, and attributes:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getChildBlocks" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/getHPathByID" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/attr/getBlockAttrs" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### 4. List/create

Notebooks:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/lsNotebooks" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.data.notebooks[] | {id, name, closed}'
```

Documents in a notebook:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/listDocsByPath" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"notebook": "NOTEBOOK_ID", "path": "/"}' | jq '.data.files[] | {id, name}'
```

Document:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/createDocWithMd" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{
    "notebook": "NOTEBOOK_ID",
    "path": "/Meeting Notes/2026-03-22",
    "markdown": "# Meeting Notes\n\n- Discussed project timeline\n- Assigned tasks"
  }' | jq '.data'
```

Notebook:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/createNotebook" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "My New Notebook"}' | jq '.data.notebook.id'
```

### 5. Mutate blocks/documents

Append:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/appendBlock" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{
    "parentID": "DOCUMENT_OR_BLOCK_ID",
    "data": "New paragraph added at the end.",
    "dataType": "markdown"
  }' | jq '.data'
```

`/api/block/prependBlock` uses the same params and inserts at beginning;
`/api/block/insertBlock` uses `previousID` instead of `parentID` to insert after
a specific block.

Update:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/updateBlock" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BLOCK_ID",
    "data": "Updated content here.",
    "dataType": "markdown"
  }' | jq '.data'
```

Rename:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/renameDocByID" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID", "title": "New Title"}'
```

Custom attributes must use `custom-` prefix:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/attr/setBlockAttrs" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BLOCK_ID",
    "attrs": {
      "custom-status": "reviewed",
      "custom-priority": "high"
    }
  }'
```

Delete block/document/notebook:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/deleteBlock" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "BLOCK_ID"}'
```

Use `/api/filetree/removeDocByID` with `{"id": "DOC_ID"}` for a document and
`/api/notebook/removeNotebook` with `{"notebook": "NOTEBOOK_ID"}` for a
notebook. Confirm destructive actions with the user before sending them.

Export:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/export/exportMdContent" \
  -H "Authorization: Token ***" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID"}' | jq -r '.data.content'
```

### 6. Interpret block types

| Type | Description |
|------|-------------|
| `d` | Document (root block) |
| `p` | Paragraph |
| `h` | Heading |
| `l` | List |
| `i` | List item |
| `c` | Code block |
| `m` | Math block |
| `t` | Table |
| `b` | Blockquote |
| `s` | Super block |
| `html` | HTML block |

## Pitfalls

- all endpoints are POST, including reads; never use GET
- SQL must be SELECT only; never send INSERT/UPDATE/DELETE/DROP
- validate IDs against `YYYYMMDDHHmmss-xxxxxxx`; reject other values
- check `code != 0` and report `msg` before processing `data`
- large documents/exports need SQL `LIMIT` and focused `jq` extraction
- resolve notebook ID with `lsNotebooks` before notebook-specific work
- token belongs in secret config only, never chat/log/source/durable notes

## Alternative: MCP Server

For native integration instead of `curl`, configure SiYuan MCP:

```yaml
# In ~/.hermes/config.yaml under mcp_servers:
mcp_servers:
  siyuan:
    command: npx
    args: ["-y", "@porkll/siyuan-mcp"]
    env:
      SIYUAN_TOKEN: "your_token"
      SIYUAN_URL: "http://127.0.0.1:6806"
```

## Verification

- `SIYUAN_URL` resolves to intended instance and token is present without disclosure
- a known full-text search returns JSON and `code: 0`
- read operations return expected block/document data only after status check
- mutations are user-authorized, use validated IDs, and report response `code`/`msg`
- exported Markdown comes from `.data.content`
- SQL queries remain SELECT-only and bounded when result may be large