---
name: xurl
description: "X/Twitter via xurl CLI: raw post search, posting, DM, media."
version: 1.1.3
author: xdevplatform + openclaw + Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [xurl]
metadata:
  hermes:
    tags: [twitter, x, social-media, xurl, official-api]
    homepage: https://github.com/xdevplatform/xurl
    upstream_skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
---

# xurl — X (Twitter) API via the Official CLI

role: X API terminal operator
do: verify auth; read/search posts/timelines/mentions; post/reply/quote/delete; engage; follow/block/mute; DM; upload media; call raw v2 endpoints; switch apps/accounts
inputs: `xurl` command, authenticated app/account, post/user IDs or URLs, query, JSON body, media path, explicit write intent
outputs: X API v2 JSON, post/user/media IDs, state-changing action results, auth status
¬: read/print `~/.xurl`; request secrets in chat; run inline-secret/verbose auth; claim writes from summaries; write without target+intent confirmation; retry ambiguous actions blindly

`xurl` is the X developer platform's official CLI. Shortcuts cover common
operations; raw curl-style mode reaches any v2 endpoint; all commands return
JSON. It replaces the older `xitter` third-party Python CLI, supports OAuth 2.0
PKCE auto-refresh, and supports multi-app/multi-account workflows.

## When to Use

- post, reply, quote, or delete
- search raw post objects, read timelines, or inspect mentions
- like, repost, bookmark
- follow, unfollow, block, mute
- direct messages
- image/video upload and media status
- any X API v2 endpoint or multi-app/account workflow

## Secret Safety (MANDATORY)

- **Never** read, print, parse, summarize, upload, or send `~/.xurl` to LLM context.
- **Never** ask user to paste credentials/tokens into chat.
- User fills `~/.xurl` manually; in Docker use the `~` seen by Hermes subprocesses.
- **Never** recommend/execute auth commands with inline secrets in an agent session.
- **Never** use `--verbose` / `-v`; it may expose auth headers/tokens.
- Credential existence check = `xurl auth status` only.

Forbidden flags (inline secrets):
`--bearer-token`, `--consumer-key`, `--consumer-secret`, `--access-token`,
`--token-secret`, `--client-id`, `--client-secret`.

App registration/rotation is user-only, outside the agent session. User runs
`xurl auth oauth2` outside the agent session after registration; OAuth 2.0 tokens
persist to `~/.xurl`, each app has isolated tokens, and tokens auto-refresh.

## Prerequisites + Installation

Pick one method (Linux shell/Go easiest):

```bash
# Shell script (installs to ~/.local/bin, no sudo, works on Linux + macOS)
curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh | bash

# Homebrew (macOS)
brew install --cask xdevplatform/tap/xurl

# npm
npm install -g @xdevplatform/xurl

# Go
go install github.com/xdevplatform/xurl@latest
```

Verify:

```bash
xurl --help
xurl auth status
```

No app/token → stop and direct user to One-Time User Setup; agent does not
register apps or pass secrets.

## One-Time User Setup (user runs outside the agent)

User performs these steps directly because they involve secrets; agent directs,
not executes:

1. Create/open app: https://developer.x.com/en/portal/dashboard
2. Redirect URI: `http://localhost:8080/callback`
3. Copy Client ID + Client Secret.
4. User registers app:

   ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```

5. User authenticates with app binding:

   ```bash
   xurl auth oauth2 --app my-app
   ```

   This opens OAuth 2.0 PKCE. If `UsernameNotFound`/403 occurs on post-OAuth
   `/2/users/me`, pass handle (xurl v1.1.0+):

   ```bash
   xurl auth oauth2 --app my-app YOUR_USERNAME
   ```

6. Set default:

   ```bash
   xurl auth default my-app
   ```

7. Verify:

   ```bash
   xurl auth status
   xurl whoami
   ```

After setup, agent may use commands; OAuth tokens auto-refresh.

Common pitfall: omit `--app my-app` → token saved to built-in `default` profile
without client ID/secret; re-run `xurl auth oauth2 --app my-app` then
`xurl auth default my-app`.

Docker HOME pitfall: official Hermes Docker uses `/opt/data` as `HERMES_HOME`,
but tool subprocesses use `HOME=/opt/data/home`; therefore `~/.xurl` is
`/opt/data/home/.xurl`, not `/opt/data/.xurl`. Run setup with same HOME:

```bash
HOME=/opt/data/home xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
HOME=/opt/data/home xurl auth oauth2 --app my-app YOUR_USERNAME
HOME=/opt/data/home xurl auth default my-app YOUR_USERNAME
HOME=/opt/data/home xurl auth status
```

If `HOME=/opt/data xurl auth status` works but `HOME=/opt/data/home xurl auth
status` has no app/token, Hermes calls cannot see credentials.

## Quick Reference

| Action | Command |
| --- | --- |
| Post | `xurl post "Hello world!"` |
| Reply | `xurl reply POST_ID "Nice post!"` |
| Quote | `xurl quote POST_ID "My take"` |
| Delete a post | `xurl delete POST_ID` |
| Read a post | `xurl read POST_ID` |
| Search posts | `xurl search "QUERY" -n 10` |
| Who am I | `xurl whoami` |
| Look up a user | `xurl user @handle` |
| Home timeline | `xurl timeline -n 20` |
| Mentions | `xurl mentions -n 10` |
| Like / Unlike | `xurl like POST_ID` / `xurl unlike POST_ID` |
| Repost / Undo | `xurl repost POST_ID` / `xurl unrepost POST_ID` |
| Bookmark / Remove | `xurl bookmark POST_ID` / `xurl unbookmark POST_ID` |
| List bookmarks / likes | `xurl bookmarks -n 10` / `xurl likes -n 10` |
| Follow / Unfollow | `xurl follow @handle` / `xurl unfollow @handle` |
| Following / Followers | `xurl following -n 20` / `xurl followers -n 20` |
| Block / Unblock | `xurl block @handle` / `xurl unblock @handle` |
| Mute / Unmute | `xurl mute @handle` / `xurl unmute @handle` |
| Send DM | `xurl dm @handle "message"` |
| List DMs | `xurl dms -n 10` |
| Upload media | `xurl media upload path/to/file.mp4` |
| Media status | `xurl media status MEDIA_ID` |
| List apps | `xurl auth apps list` |
| Remove app | `xurl auth apps remove NAME` |
| Set default app | `xurl auth default APP_NAME [USERNAME]` |
| Per-request app | `xurl --app NAME /2/users/me` |
| Auth status | `xurl auth status` |

`POST_ID` accepts full URLs (xurl extracts ID); usernames accept optional `@`.

## Procedure

1. Verify `xurl --help`, `xurl auth status`, and default-app marker `▸`.
2. If default app has `oauth2: (none)` but another app has a valid user, tell user
   `xurl auth default <that-app>`; if auth absent, use One-Time User Setup.
3. Confirm reachability with cheap read: `xurl whoami`, `xurl user @handle`, or
   `xurl search ... -n 3`.
4. For `search`, confirm task needs raw authenticated post objects, IDs,
   account context, or a following write; use another research surface for a
   mere topic summary, not a summarized answer or summary of a topic.
5. Confirm target post/user and explicit intent before every write (post, reply,
   like, repost, DM, follow, block, delete).
6. Execute; only xurl output/raw X response proves a state change. Search,
   summaries, and prior context do not.
7. Parse JSON directly; never return `~/.xurl` contents.

## Command Details

### Posting

```bash
xurl post "Hello world!"
xurl post "Check this out" --media-id MEDIA_ID
xurl post "Thread pics" --media-id 111 --media-id 222

xurl reply 1234567890 "Great point!"
xurl reply https://x.com/user/status/1234567890 "Agreed!"
xurl reply 1234567890 "Look at this" --media-id MEDIA_ID

xurl quote 1234567890 "Adding my thoughts"
xurl delete 1234567890
```

### Reading & Search

`xurl search` returns raw authenticated post objects (IDs, authors, full text) for
immediate engagement:

```bash
xurl read 1234567890
xurl read https://x.com/user/status/1234567890

xurl search "golang"
xurl search "from:elonmusk" -n 20
xurl search "#buildinpublic lang:en" -n 15
```

For X Articles, use raw API mode. Use `xurl read` for a post ID/URL; do not put `read` before a `/2/tweets/...` path. Request `article` and ingest
`data.article.plain_text`:

```bash
xurl --app APP_NAME '/2/tweets/2057909493250539891?expansions=author_id,attachments.media_keys,referenced_tweets.id&tweet.fields=created_at,lang,public_metrics,context_annotations,entities,possibly_sensitive,conversation_id,in_reply_to_user_id,referenced_tweets,article'
```

### Users, Timeline, Mentions

```bash
xurl whoami
xurl user elonmusk
xurl user @XDevelopers

xurl timeline -n 25
xurl mentions -n 20
```

### Engagement

```bash
xurl like 1234567890
xurl unlike 1234567890

xurl repost 1234567890
xurl unrepost 1234567890

xurl bookmark 1234567890
xurl unbookmark 1234567890

xurl bookmarks -n 20
xurl likes -n 20
```

### Social Graph

```bash
xurl follow @XDevelopers
xurl unfollow @XDevelopers

xurl following -n 50
xurl followers -n 50

# Another user's graph
xurl following --of elonmusk -n 20
xurl followers --of elonmusk -n 20

xurl block @spammer
xurl unblock @spammer
xurl mute @annoying
xurl unmute @annoying
```

### Direct Messages

```bash
xurl dm @someuser "Hey, saw your post!"
xurl dms -n 25
```

### Media Upload

```bash
# Auto-detect type
xurl media upload photo.jpg
xurl media upload video.mp4

# Explicit type/category
xurl media upload --media-type image/jpeg --category tweet_image photo.jpg

# Videos need server-side processing — check status (or poll)
xurl media status MEDIA_ID
xurl media status --wait MEDIA_ID

# Full workflow
xurl media upload meme.png                  # returns media id
xurl post "lol" --media-id MEDIA_ID
```

## Raw API Access

Shortcuts are not exhaustive; raw curl-style mode reaches any endpoint:

```bash
# GET
xurl /2/users/me

# POST with JSON body
xurl -X POST /2/tweets -d '{"text":"Hello world!"}'

# DELETE / PUT / PATCH
xurl -X DELETE /2/tweets/1234567890

# Custom headers
xurl -H "Content-Type: application/json" /2/some/endpoint

# Force streaming
xurl -s /2/tweets/search/stream

# Full URLs also work
xurl https://api.x.com/2/users/me
```

## Flags, Streaming, and Output

| Flag | Short | Description |
| --- | --- | --- |
| `--app` | | Use a specific registered app (overrides default) |
| `--auth` | | Force auth type: `oauth1`, `oauth2`, or `app` |
| `--username` | `-u` | Which OAuth2 account to use (if multiple exist) |
| `--verbose` | `-v` | **Forbidden in agent sessions** — leaks auth headers |
| `--trace` | `-t` | Add `X-B3-Flags: 1` trace header |

Streaming endpoints auto-detected: `/2/tweets/search/stream`,
`/2/tweets/sample/stream`, `/2/tweets/sample10/stream`; force any endpoint with
`-s`.

All commands return JSON mirroring X API v2:

```json
{ "data": { "id": "1234567890", "text": "Hello world!" } }
```

Errors are JSON too:

```json
{ "errors": [ { "message": "Not authorized", "code": 403 } ] }
```

## Common Workflows

### Post with an image

```bash
xurl media upload photo.jpg
xurl post "Check out this photo!" --media-id MEDIA_ID
```

### Reply to a conversation

```bash
xurl read https://x.com/user/status/1234567890
xurl reply 1234567890 "Here are my thoughts..."
```

### Search and engage

```bash
xurl search "topic of interest" -n 10
xurl like POST_ID_FROM_RESULTS
xurl reply POST_ID_FROM_RESULTS "Great point!"
```

### Check your activity

```bash
xurl whoami
xurl mentions -n 20
xurl timeline -n 20
```

### Multiple apps (credentials pre-configured manually)

```bash
xurl auth default prod alice               # prod app, alice user
xurl --app staging /2/users/me             # one-off against staging
```

## Error Handling

- any error → non-zero exit; API errors still JSON on stdout
- auth errors → user re-runs `xurl auth oauth2` outside agent session
- write commands needing caller ID auto-fetch `/2/users/me`; failure surfaces auth error

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Auth errors after successful OAuth flow | Token saved to `default` app (no client-id/secret) instead of your named app | `xurl auth oauth2 --app my-app` then `xurl auth default my-app` |
| `unauthorized_client` during OAuth | App type set to "Native App" in X dashboard | Change to "Web app, automated app or bot" in User Authentication Settings |
| `UsernameNotFound` or 403 on `/2/users/me` right after OAuth | X not returning username reliably from `/2/users/me` | Re-run `xurl auth oauth2 --app my-app YOUR_USERNAME` (xurl v1.1.0+) to pass the handle explicitly |
| 401 on every request | Token expired or wrong default app | Check `xurl auth status` — verify `▸` points to an app with oauth2 tokens |
| `client-forbidden` / `client-not-enrolled` | X platform enrollment issue | Dashboard → Apps → Manage → Move to "Pay-per-use" package → Production environment |
| `CreditsDepleted` | $0 balance on X API | Buy credits (min $5) in Developer Console → Billing |
| `media processing failed` on image upload | Default category is `amplify_video` | Add `--category tweet_image --media-type image/png` |
| Two "Client Secret" values in X dashboard | UI bug — first is actually Client ID | Confirm on the "Keys and tokens" page; ID ends in `MTpjaQ` |

## Pitfalls

- rate limits are per endpoint; 429 → wait/retry; writes tighter than reads
- 403 usually missing OAuth scope; user re-runs OAuth
- OAuth tokens auto-refresh; no manual refresh action
- each app has isolated credentials/tokens; switch `auth default`/`--app`
- multiple accounts use `-u/--username` or `xurl auth default APP USER`
- token storage is YAML at `~/.xurl`; Docker official HOME = `/opt/data/home`; never expose file
- meaningful X API use is typically paid; plan/permission failures are not code failures
- never claim state change without command/API response

## Verification

- `xurl --help` and `xurl auth status` succeed; no secrets entered/read by agent
- `▸` default app has valid OAuth2 user; cheap read confirms reachability
- each write had explicit target+intent and command JSON confirms resulting state
- raw Article request uses `article` and `data.article.plain_text` when applicable
- media processing status checked before posting videos
- 401/403/429/credits/plan errors handled per troubleshooting

## Attribution

- Upstream CLI: https://github.com/xdevplatform/xurl (X developer platform team, Chris Park et al.)
- Upstream agent skill: https://github.com/openclaw/openclaw/blob/main/skills/xurl/SKILL.md
- Hermes adaptation: reformatted for Hermes skill conventions; safety guardrails preserved verbatim.
