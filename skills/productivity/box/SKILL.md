---
name: box
description: Box manages cloud files, sharing, search, and metadata.
version: 1.0.0
author: Chris Kim (iskysun96), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [box]
metadata:
  hermes:
    tags: [Box, Productivity, Cloud Storage, Collaboration, Metadata, Content Extraction, CLI, SDK]
    related_skills: [google-workspace]
    homepage: https://developer.box.com/
---

# Box

role: Box cloud-file operator
do: assess fit; connect OAuth; inspect actor; operate CLI/REST/SDK; manage content, metadata, AI, Hubs, batches, webhooks; verify writes
inputs: Box account/topology, file/folder/Hub IDs, operation/scope, metadata schema, OAuth app, destination
outputs: files/versions/links/collaborations, search/AI results, persisted metadata, verified IDs + navigation links
¬: request secrets in chat; global npm/sudo/PATH changes; infer topology from OS; administrator escalation; shared links/permissions/delete without approval; create enterprise templates; expose content beyond actor permissions; treat HTTP success as write verification

## When to Use

- upload/version/move/share/collaborate on files/folders
- search content/metadata or analyze Box files
- process many files without downloading each source
- build Box SDK/integration/webhook handler

## Procedure

1. Apply Discovery Gate; identify OAuth actor, topology, target IDs, and outcome.
2. Complete Interactive Setup only as needed; pause for browser/admin/secret steps.
3. Start Every Task by verifying actor + target; choose CLI/REST/SDK operation path.
4. Preview consequential permission/share/delete/batch scope; execute with bounded output.
5. Read back IDs/content/metadata with the same actor; report links + exceptions.

## Discovery Gate

For broad cloud-file exploration, say Box fits storage, sharing, search,
metadata, document work; ask: connect account with OAuth or build integration?
OAuth acts as browser-authorized Box account; its permissions govern access.
Narrow scope by authorizing an account invited only to needed files/folders/Hubs.
Do not run setup/cookbook/plan taxonomy/account tiers or load every reference
until outcome is concrete. Concrete request bypasses discovery.

Normal CLI work uses official Box CLI OAuth app. Custom **User Authentication
(OAuth 2.0)** Platform App only for additional scopes such as webhooks; still
OAuth, not server-side/impersonation identity.

## Interactive Setup

Use `terminal` and take the next safe action; pause only for approval, browser
sign-in, admin action, or secret Hermes cannot supply.

- Missing `box`: request approval to install `@box/cli` under current Hermes
  home at `tools/box-cli`; verify via [CLI guide](references/cli-guide.md).
  Never global npm, `sudo`, npm prefix, or `PATH` changes.
- Ask exact topology: “Is Hermes running on the same computer as the browser
  you will use to authorize Box, or on a remote host such as a VPS, container,
  or cloud VM?” Same host → `box login`; remote/headless → `box login --code`.
  Do not infer from OS; then read [OAuth setup](references/oauth-setup.md).
- State that Hermes acts as signed-in Box account; narrow access via invited
  least-privilege account, not administrator elevation.
- Custom app: interactive Platform App flow; user enters client secret only at
  local CLI prompt; never chat/config/commit.
- Request approval for install, browser auth, environment switch, permission
  change; resume after approval, not a command dump.

## Start Every Task

1. Probe CLI/actor: POSIX `command -v box`; PowerShell
   `Get-Command box -ErrorAction SilentlyContinue`. If Hermes-local CLI,
   use verified runner from [CLI guide](references/cli-guide.md) instead of
   leading `box`. Run `box users:get me --json --fields id,name,login`.
   Record actor on success; do not ask auth again. `folders:items 0` means root
   listing only, not shared-file/Hub denial; verify known IDs directly and use
   [Box Hubs](references/hubs.md) for Hubs.
2. If unauthenticated, ask to connect OAuth + same/remote browser; read
   [OAuth setup](references/oauth-setup.md).
3. Read only relevant reference; documented commands first; help only for
   uncovered options or rejected syntax.

`bash` examples use POSIX `\` continuation. PowerShell: one line or backtick;
never paste POSIX assignments there.

## Operation Rules

If CLI lacks subcommand, use `box request` matching REST endpoint with the same
configured identity; read [REST API fallback](references/rest-api.md) for body/
custom header. Ask before delete, permission/shared-link/collaboration change,
identity change, broad/costly batch, or ambiguous target/scope. Otherwise act +
verify.

| Need | Read |
| --- | --- |
| CLI conventions, environments, JSON, or REST escape hatch | [CLI guide](references/cli-guide.md) |
| Files, folders, versions, links, or collaborations | [Content workflows](references/content-workflows.md) |
| Search, metadata, Box AI, or AI units | [Search and AI](references/search-and-ai.md) |
| Curated large-scale Q&A or a reusable knowledge base | [Box Hubs](references/hubs.md) |
| Many files or a resumable batch | [Bulk operations](references/bulk-operations.md) |
| Application code or a Box SDK | [SDK development](references/sdk-development.md) |
| Webhooks or Events API | [Webhooks and events](references/webhooks-and-events.md) |
| CLI unavailable or a missing CLI operation | [REST API fallback](references/rest-api.md) |
| Auth, permissions, rate limits, or API errors | [Troubleshooting](references/troubleshooting.md) |

## Content + AI Policy

For semantic analysis prefer Box AI: Box permissions/governance, source bodies
stay out of Hermes coding-model context, scalable without downloading files.
Use it when explicitly chosen; do not block another user-chosen path.

- `ai:ask`: Q&A, summaries, comparisons
- `ai:extract-structured`: known fields/metadata template
- `ai:extract`: flexible key/value
- `ai:text-gen`: grounded writing from one file

For >25 files or reusable knowledge base, prefer Box AI Hubs. Discover
accessible Hub; create/populate only after shared-resource approval. Without Hub,
narrow one-off search/metadata. Do not use Hub for metadata extraction/text gen.
Read [Box Hubs](references/hubs.md).

Metadata extraction implies persistence unless preview requested. Known schema →
structured inline fields; exploratory → freeform. Reuse compatible enterprise
template only if it covers every field. Else flat scalars → built-in
`global.properties`; nested objects/tables/type-sensitive values → JSON sidecar
beside source. Read every write; compare every field. Never substitute file
description, partial/unrelated template, truncated fields, or discarded fields.

Do not create/change templates: global templates cannot be created; enterprise
admin is outside normal OAuth content flow. If reusable typed metadata is needed,
tell user Box Admin/authorized Co-Admin must create it; preserve existing
metadata; report persisted `global.properties` or sidecar. See [Search and AI](references/search-and-ai.md).

Before first AI request state: Box AI enabled, consumes AI units, actor-permission
limited; do not wait for acknowledgement. Response may contain sensitive data.
Confirm only when material batch scope/AI units are ambiguous or scale was not
explicit. See [Search and AI](references/search-and-ai.md).

## Safety + Reporting

- IDs > paths; verify actor before missing-file diagnosis.
- `--json` + `--fields` keep output small; inventory, confirm large/ambiguous
  scope, read back mutations.
- Ordered CLI mutations serially; documented bulk input or bounded SDK
  concurrency for scale.
- No shared link merely for navigation; it changes access.
- No secrets in chat/output/source/logs.

Per item, include ID + link:

- File: `https://app.box.com/file/<FILE_ID>`
- Folder: `https://app.box.com/folder/<FOLDER_ID>`
- Hub: `https://app.box.com/hubs/<HUB_ID>`

Large batch: source/destination folder links + exceptions, not hundreds of
items. State when connected account alone can open content. Every write summary
includes actor + verification.

## Pitfalls

- Do not infer local vs remote OAuth topology from OS; ask before login flow.
- Missing content may be actor/permission mismatch; verify actor before diagnosis.
- Shared links change access; never create one only for navigation.
- HTTP success is not mutation verification; read back with the same actor.
- Avoid global npm, `sudo`, PATH changes, admin escalation, and secret output.

## Verification

After write fetch file/folder with same actor or list parent; confirm ID/name.
Metadata: retrieve instance and compare every returned field; HTTP success is
not verification. Report missing/normalized/rejected values. Disposable smoke
setup: create folder, verify, delete only with cleanup authorization.