---
name: here-now
description: Publish sites to {slug}.here.now and store files in Drives.
version: 1.15.3
author: here.now
license: MIT
prerequisites:
  commands: [curl, file, jq]
platforms: [macos, linux]
metadata:
  hermes:
    tags: [here.now, herenow, publish, deploy, hosting, static-site, web, share, URL, drive, storage]
    homepage: https://here.now
    requires_toolsets: [terminal]
---

# here.now

role: here.now site publisher and private Drive operator
do: read current docs; resolve helper paths; publish/finalize sites; update slugs; store/share Drive files; manage API-key/token hygiene; report live URLs/expiry from current output
inputs: file/directory; slug/claim token; API key/Drive token; Drive/path/prefix/TTL; site options; user email/code for key setup
outputs: live site URL; anonymous claim URL/expiry or authenticated permanence; Drive object/share; state/cache; redacted operation result
¬: trust stale local docs/state over live API; publish before finalize; expose credentials/tokens; call private Drive public; show raw claim URL unless valid; send auth to untrusted base URL; commit `.herenow` state

here.now publishes websites/files at `{slug}.here.now` and stores private files
in cloud Drives. Helpers keep this edge capability outside core:

- `${HERMES_SKILL_DIR}/scripts/publish.sh` — site publish/update
- `${HERMES_SKILL_DIR}/scripts/drive.sh` — private Drive storage

## When to Use

- publish a static site or raw file/directory
- update an existing here.now slug
- store private agent documents, plans, memory, assets, media, research, or code
- share scoped Drive access with another agent
- obtain an API key or inspect current site/Drive capability

## Current Docs Gate

Before answering any here.now capability, feature, or workflow question, read
https://here.now/docs:

- first here.now interaction in a conversation
- every how-to/what-is-supported/recommended question
- before saying a feature is unsupported

Topics requiring current docs: Drives/sharing, custom domains, payments/gating,
forking, proxy routes/service variables, handles/links, limits/quotas, SPA
routing, errors/remediation, and feature availability. If docs fetch fails,
continue with local skill plus live API/script output; for active operations live
API behavior wins when it conflicts with docs.

## Prerequisites

- binaries: `curl`, `file`, `jq`
- optional `$HERENOW_API_KEY`
- optional `$HERENOW_DRIVE_TOKEN`
- optional `~/.herenow/credentials`
- publish/Drive helpers at `${HERMES_SKILL_DIR}/scripts/`

## Procedure

### 1. Publish a site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --client hermes
```

Output includes live URL such as `https://bright-canvas-a7k2.here.now/`. Flow:
create/update → upload files → finalize. Site is not live until finalize succeeds.
Without API key: anonymous site expires in 24 hours. With saved API key: permanent.

HTML: `index.html` must be at published directory root; publish `my-site/` with
`my-site/index.html`, not its parent. Raw files are supported: one file gets rich
viewer (image/PDF/video/audio); multiple files get directory listing, navigation,
and image gallery.

### 2. Update a site

```bash
PUBLISH="${HERMES_SKILL_DIR}/scripts/publish.sh"
bash "$PUBLISH" {file-or-dir} --slug {slug} --client hermes
```

Anonymous updates auto-load `claimToken` from `.herenow/state.json`; override
with `--claim-token {token}`. Authenticated updates require saved API key.

### 3. Store/share private Drive files

Use a Drive for files that persist privately rather than public website assets.
Every signed-in account has default `My Drive`:

```bash
DRIVE="${HERMES_SKILL_DIR}/scripts/drive.sh"
bash "$DRIVE" default
bash "$DRIVE" ls "My Drive"
bash "$DRIVE" put "My Drive" notes/today.md --from ./notes/today.md
bash "$DRIVE" cat "My Drive" notes/today.md
bash "$DRIVE" share "My Drive" --perms write --prefix notes/ --ttl 7d
```

For agent handoff use scoped Drive tokens. Given a `herenow_drive` share block,
send its `token` as `Authorization: Bearer ***` against `api_base`, respect
`pathPrefix`, preserve ETags on writes, and treat `pathPrefix: null` as full-Drive
access. Prefer `drive.sh`; otherwise use listed API operations directly.

### 4. Resolve API-key storage

Publish key precedence, first match:

1. `--api-key {key}` (CI/scripting only; avoid interactive)
2. `$HERENOW_API_KEY`
3. `~/.herenow/credentials` (agent-recommended)

Save a received key immediately, without asking the user to run it:

```bash
mkdir -p ~/.herenow && echo "{API_KEY}" > ~/.herenow/credentials && chmod 600 ~/.herenow/credentials
```

Prefer credentials file over interactive CLI flags. Never commit
`~/.herenow/credentials` or `.herenow/state.json`.

### 5. Obtain an API key

To upgrade anonymous 24-hour sites to permanent:

1. ask user email
2. request one-time code:

```bash
curl -sS https://here.now/api/auth/agent/request-code \
  -H "content-type: application/json" \
  -d '{"email": "user@example.com"}'
```

3. tell user: "Check your inbox for a sign-in code from here.now and paste it here."
4. verify:

```bash
curl -sS https://here.now/api/auth/agent/verify-code \
  -H "content-type: application/json" \
  -d '{"email":"user@example.com","code":"ABCD-2345"}'
```

5. save returned `apiKey` yourself:

```bash
mkdir -p ~/.herenow && echo "{API_KEY}" > ~/.herenow/credentials && chmod 600 ~/.herenow/credentials
```

### 6. Treat state as cache

After create/update, script writes `.herenow/state.json` in CWD:

```json
{
  "publishes": {
    "bright-canvas-a7k2": {
      "siteUrl": "https://bright-canvas-a7k2.here.now/",
      "claimToken": "abc123",
      "claimUrl": "https://here.now/claim?slug=bright-canvas-a7k2&token=abc123",
      "expiresAt": "2026-02-18T01:00:00.000Z"
    }
  }
}
```

Use it to find prior slugs before create/update, but never present its local
path as URL or use it as source of truth for auth mode, expiry, or claim URL.

### 7. Report result to user

Sites:

- always share current run's `siteUrl`
- inspect `publish_result.*` stderr lines for auth mode
- `publish_result.auth_mode=authenticated` → permanent/account-saved; no claim URL
- `publish_result.auth_mode=anonymous` → expires in 24 hours; share claim URL only when `publish_result.claim_url` is non-empty and begins `https://`; warn claim token is returned once and unrecoverable
- never tell user to inspect `state.json` for auth/claim status

Drives:

- do not describe Drive files as public URLs
- say contents private unless scoped token share exists
- for agents, narrow `pathPrefix` and short TTL

### 8. Use publish options

| Flag | Description |
| ---------------------- | -------------------------------------------- |
| `--slug {slug}` | Update an existing site instead of creating |
| `--claim-token {token}`| Override claim token for anonymous updates |
| `--title {text}` | Viewer title (non-HTML sites) |
| `--description {text}` | Viewer description |
| `--ttl {seconds}` | Set expiry (authenticated only) |
| `--client {name}` | Agent name for attribution (e.g. `hermes`) |
| `--base-url {url}` | API base URL (default: `https://here.now`) |
| `--allow-nonherenow-base-url` | Allow sending auth to non-default `--base-url` |
| `--api-key {key}` | API key override (prefer credentials file) |
| `--spa` | Enable SPA routing (serve index.html for unknown paths) |
| `--forkable` | Allow others to fork this site |

## Pitfalls

- read https://here.now/docs before claims about current support; live API wins for active operations
- finalize failure means site is not live even if upload succeeded
- anonymous sites expire in 24 hours; authenticated sites are permanent
- `index.html` belongs at published root; raw files follow viewer/listing rules
- Drive content is private, not a public URL; scope shares with narrow prefix/TTL
- never expose API/Drive tokens, claim tokens, credential file, or local state
- `state.json` is cache only; current script stderr/result is authoritative
- claim URL is one-time/recoverability-sensitive; only share validated `https://` output
- `--allow-nonherenow-base-url` can send auth off-domain; use only with explicit trust
- never commit `~/.herenow/credentials` or `.herenow/state.json`
- dashboard/docs may not cover stdio shell-auth state or `$HERMES_HOME/.env` credential flows; those stay host-side

## Verification

- required binaries and helper paths resolve
- current docs read for capability questions
- publish output has `siteUrl`; finalize succeeded
- auth mode/expiry/claim reporting comes from current `publish_result.*`, not state cache
- Drive listing/read/write/share uses intended Drive and scoped token policy
- credential file mode is `600`; no secret appears in output or source control
- inspect current docs for account management beyond helper surface

## Beyond publish.sh

For Drive operations use `drive.sh` or Drive API. For delete, metadata,
passwords, payments, domains, handles, links, variables, proxy routes, forking,
duplication, and other account/site management, read https://here.now/docs.