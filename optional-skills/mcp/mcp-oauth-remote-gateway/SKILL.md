---
name: mcp-oauth-remote-gateway
description: Manual OAuth for remote MCP servers on headless gateways.
version: 1.0.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [MCP, OAuth, PKCE, Remote-Deployment]
    related_skills: [hermes-agent, mcporter, fastmcp]
---

# MCP OAuth on a Remote Hermes Gateway

role: remote-gateway MCP OAuth operator
do: identify topology; prefer dashboard/TTY escape hatch; discover RFC metadata; register PKCE client; authorize; verify state; exchange code; atomically write Hermes token files; configure/reload; smoke-test and classify recovery
inputs: remote HTTP MCP URL/name; gateway `HERMES_HOME`; OAuth metadata; user browser callback URL; client credentials when provider is pre-registered
outputs: cached Hermes OAuth/client JSON; `mcp_servers` config; token smoke-test result; reload/re-auth/API-key decision
¬: use manual flow on local CLI; skip state/PKCE/resource; print secrets; write only access token; fabricate scopes; call remote OAuth support impossible; use `mcp-remote` as workaround; diagnose/treat provider revocation as a local bug

Hermes' built-in MCP OAuth client listens on `127.0.0.1:<port>` inside the
Hermes process and registers that loopback as `redirect_uri`. This works for a
local CLI, but a remote gateway's browser resolves `127.0.0.1` to the user's
laptop, not the gateway. The callback therefore misses Hermes.

This procedure performs OAuth manually and writes the exact token files expected
by `HermesTokenStorage`; a later `/reload-mcp` finds cached tokens and skips the
browser flow.

## When to Use

Use only when all are true:

1. user wants a remote HTTP MCP server requiring OAuth, not a static Bearer token
2. Hermes runs as a remote gateway (container, VPS, Docker, managed service), not a local laptop CLI
3. server supports OAuth 2.1 with PKCE and RFC 7591 Dynamic Client Registration (DCR)

Modern servers such as Better Stack, Linear, Cloudflare, and Datadog commonly
support DCR. GitHub is the notable exception: use a pre-registered OAuth App or
Personal Access Token instead.

Do not use this for:

- local CLI Hermes: set `auth: oauth` in `mcp_servers.<name>` and `/reload-mcp`; built-in browser/localhost callback works
- static Bearer/API-key servers: prefer `headers.Authorization: "Bearer <token>"` when user agrees
- GitHub Copilot MCP (`api.githubcopilot.com/mcp/`): use PAT or pre-registered OAuth App; see pitfall 17

## Why remote built-in OAuth fails

`tools/mcp_oauth.py` picks free port `P`, registers
`http://127.0.0.1:P/callback`, starts the listener inside Hermes, and waits for
the code. A remote browser follows the redirect to its own laptop; the callback
never arrives. After authorization, the browser returns to
`http://127.0.0.1:P/callback?code=...`, which resolves on the user's laptop,
not the gateway. The flow times out, and `/reload-mcp` may say "No MCP tools
available" without detail. Recognize `[xdg-open] <defunct>`, empty/missing
`$HERMES_HOME/mcp-tokens/`, and reload output without an "Added/Reconnected: X"
line in `change_detail`.

## Cheap fallbacks first

When Hermes detects a remote session, its built-in flow offers:

1. paste-back: authorize in browser, let callback fail, paste full address-bar URL (`?code=...&state=...`) at an interactive TTY prompt; works over SSH
2. SSH port-forward: `ssh -N -L <port>:127.0.0.1:<port> <user>@<host>`; callback reaches the remote listener

Both require an interactive terminal. Use the manual no-TTY flow below for a
messaging-only gateway/bot.

## Preferred front door: dashboard

Try the Hermes dashboard before token surgery. A remote gateway may run the
dashboard separately, e.g. `hermes dashboard --host 0.0.0.0 --port <port>`.
Its authenticated connector/MCP console may expose `/api/mcp/servers`,
`/api/mcp/status`, and `/connectors`; a cookieless request returning 401/302
confirms routes exist. In the user's browser, dashboard OAuth captures the
redirect in the correct context.

Escalation order:

1. dashboard in the user's browser: add server, authorize, reload; no callback copy/paste or hand-written files
2. manual token surgery: no dashboard browser session / pure-chat headless context

Find the public dashboard URL and redact secrets:

```bash
env | grep -iE "HERMES_DASHBOARD_PUBLIC_URL|RAILWAY_PUBLIC_DOMAIN|RAILWAY_STATIC_URL|RAILWAY_SERVICE_.*_URL|PUBLIC_URL|BASE_URL|DOMAIN" \
  | sed -E 's/(TOKEN|SECRET|KEY|PASSWORD)=.*/\1=***REDACTED***/I'
```

`HERMES_DASHBOARD_PUBLIC_URL` wins. On Railway inspect
`RAILWAY_PUBLIC_DOMAIN`, `RAILWAY_STATIC_URL` (`*.up.railway.app`), and
`RAILWAY_SERVICE_*_URL`; provide the full `https://` URL and Connectors/MCP
section. Always retain the redaction pipe: these variables sit beside
`*_TOKEN`/`*_SECRET`.

Dashboard does not fix stdio servers needing shell login state or credentials
from `$HERMES_HOME/.env`; those remain host-side.

## Procedure

Run shell commands through `terminal` on the gateway host. Run PKCE, token
exchange, and file writes through `execute_code` or a terminal Python process.
Token exchange and final file writes MUST be in the same code block (pitfall 16).

### 1. Confirm remote/headless topology

```bash
env | grep -iE "HERMES|RAILWAY|CONTAINER"
echo "$DISPLAY $WAYLAND_DISPLAY $SSH_CLIENT"
```

No display plus a remote indicator means remote gateway. This matches
`tools/mcp_oauth.py::_can_open_browser()`; if Hermes calls itself headless, the
built-in interactive flow cannot complete.

### 2. Resolve profile-aware Hermes paths

```bash
HERMES_HOME=$(python3 -c 'from hermes_constants import get_hermes_home; print(get_hermes_home())')
echo "config: $HERMES_HOME/config.yaml"
echo "tokens: $HERMES_HOME/mcp-tokens/"
```

### 3. Discover OAuth metadata

RFC 9728 Protected Resource Metadata is advertised by `WWW-Authenticate` on
401 responses:

```bash
curl -sI https://mcp.example.com | grep -i www-authenticate
# → Bearer realm="mcp", resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource"
```

If the response is a bare `{"errors":["Unauthorized"]}` 401, probe all
well-known paths:

```bash
for p in \
  /.well-known/oauth-protected-resource \
  /.well-known/oauth-authorization-server \
  /.well-known/openid-configuration ; do
  echo "=== $p ==="
  curl -s -A "python-httpx/0.27" "https://mcp.example.com$p" | head -c 400; echo
done
```

Fetch resource metadata for `authorization_servers`, then that AS's
`/.well-known/oauth-authorization-server` for `authorization_endpoint`,
`token_endpoint`, and `registration_endpoint`. Many providers behind Cloudflare
403 default `urllib`; use `User-Agent: python-httpx/0.27` (or similar) on every
request.

### 4. Register a dynamic public client (RFC 7591)

POST to `registration_endpoint`:

```json
{
  "client_name": "Hermes Agent (manual OAuth)",
  "redirect_uris": ["http://127.0.0.1:8765/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "<scopes_from_resource_metadata>"
}
```

Omit `scope` when AS `scopes_supported` is empty. Port `8765` (or any unused
port) is only a registered redirect; nothing listens there. `none` declares a
public PKCE client. Save returned `client_id`.

### 5. Build authorize URL with PKCE

Generate `code_verifier = secrets.token_urlsafe(64)[:128]`,
`code_challenge = base64url(sha256(code_verifier))` without padding, and
`state = secrets.token_urlsafe(24)`. Query parameters:

- `response_type=code`, `client_id`, `redirect_uri`
- `code_challenge`, `code_challenge_method=S256`, `state`
- `resource=<mcp_server_url>` (RFC 8707; many servers require it)
- `scope=<space-separated>` only when AS `scopes_supported` is non-empty and/or resource metadata declares scopes

With `scopes_supported: []`, omit `scope`; the AS grants its default set.
Fabricated scopes can cause `invalid_scope`. Stash `code_verifier` and `state`
in `/tmp/.mcp-oauth-work/<server>.json` with `0600` permissions; they may be
needed across turns.

### 6. Send authorize URL to user

Generate it with `urllib.parse.urlencode()`, never by hand:

```
Open this URL in your browser:
<authorize_url>

After approving, your browser will try to load http://127.0.0.1:8765/callback
and fail to connect — THAT'S EXPECTED. Just copy the entire URL from the
address bar (it will contain ?code=...&state=...) and paste it back here.
```

### 7. Exchange callback code

1. Parse `code` and `state` from callback query.
2. Verify `state` equals stashed state; this CSRF check is mandatory.
3. POST `application/x-www-form-urlencoded` to `token_endpoint`:
   `grant_type=authorization_code`, `code`, same `redirect_uri`, `client_id`, stashed `code_verifier`, and `resource` when required in step 5.
4. Expect `access_token`, `refresh_token`, `token_type`, `expires_in`, `scope`.

### 8. Write exact Hermes token schema

`tools/mcp_oauth.py::HermesTokenStorage.get_tokens()` expects
`$HERMES_HOME/mcp-tokens/`; create directory `0o700`, files `0o600`.

`<server_name>.json` (`OAuthToken`):

```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "refresh_token": "...",
  "scope": "read write"
}
```

`<server_name>.client.json` (`OAuthClientInformationFull`):

```json
{
  "client_id": "...",
  "redirect_uris": ["http://127.0.0.1:8765/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "scope": "read write",
  "client_name": "..."
}
```

Use `json.dumps(..., indent=2)`. Sanitize filename with
`re.sub(r'[^\w\-]', '_', server_name)[:128]`, matching `_safe_filename()`.
Delete `/tmp/.mcp-oauth-work/<server>.json` immediately after successful
exchange; it contains the consumed `code_verifier`.

### 9. Configure server

```yaml
mcp_servers:
  <name>:
    url: "https://mcp.example.com"
    auth: oauth
    timeout: 180
    connect_timeout: 60
```

### 10. Smoke-test token before reload

Manually POST MCP `initialize`; this catches scopes, `resource`, and Cloudflare
issues before another opaque reload failure:

```python
body = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "hermes-debug", "version": "1.0"},
    },
}).encode()
# POST to the MCP URL with:
#   Authorization: Bearer ***
#   Accept: application/json, text/event-stream
#   Content-Type: application/json
#   MCP-Protocol-Version: 2025-06-18
#   User-Agent: python-httpx/0.27
```

Expect HTTP 200, `Content-Type: text/event-stream`, and JSON-RPC result with
`serverInfo` and `capabilities`. Do not use default-User-Agent `urllib`; use
`scripts/diagnose-oauth-mcp.py` to automate this smoke test.

### 11. Reload MCP

Tell the user to run `/reload-mcp`. Hermes reads `auth: oauth`, loads both files,
skips browser flow, registers `mcp_<name>_*`, and refreshes before
`expires_in`.

## Pitfalls

1. **Headless is not OAuth-impossible.** Built-in OAuth works for local CLI;
   only remote browser/process topology breaks it. Inspect environment first.
2. **Read source/docs before capability claims.** `tools/mcp_oauth.py` and
   MCP config docs in `website/docs/` are authoritative.
3. **Cloudflare UA filter.** Send `User-Agent: python-httpx/0.27` (or browser-like)
   on every metadata request; Hermes uses httpx and succeeds on the real path.
4. **Send `resource` in authorize and token requests.** RFC 8707 binds token to
   MCP resource; omission can cause scope/audience failure.
5. **Trailing slash matters.** Copy `resource` verbatim from protected-resource
   metadata; `https://mcp.example.com/` may differ from no-slash URL.
6. **`/reload-mcp` is silent on failure.** "No MCP tools available" without
   `change_detail` means configured server failed to connect; inspect error log,
   manual `initialize`, then full process restart only if needed.
7. **Circuit breaker can survive reload.** `tools/mcp_tool.py` module-level
   error-count threshold may short-circuit calls. Try `/reload-mcp` first; if a
   live call still short-circuits, restart the gateway process. Do not lead with
   restart.
8. **Expired access token + tripped breaker deadlock.** Auto-refresh is inside
   the call path; pair manual refresh with full restart, not only reload.
9. **`invalid_grant` means refresh token dead.** HTTP 400 variants such as
   `Grant not found`, `Token expired`, or `refresh token is invalid` have no
   gateway-side recovery. Re-run steps 3-10 or switch to static personal API key;
   do not loop. Check `expires_at` against `time.time()` before create/update.
10. **Successful refresh can still expose session revocation.** If old token
    smoke-test returns `401 invalid_token`, refresh and smoke-test new token. If
    new token works, persist and restart for breaker. If it returns JSON-RPC
    `-32002`/"Session expired", provider revoked underlying MCP session; full
    authorization-code re-auth is required. `scripts/diagnose-oauth-mcp.py`
    classifies `TOKEN_OK`, `REFRESH_FIXED`, `SESSION_REVOKED`, or `REFRESH_DEAD`.
    For recurring revocation, prefer static Personal API key; see
    `references/stripe-mcp-oauth-revocation.md`.
11. **Client info file is mandatory.** Without `<server>.client.json`, refresh
    lacks `client_id`; write both files.
12. **Generate authorize URL programmatically.** `urllib.parse.urlencode()`
    preserves scopes and special `state` characters.
13. **Delete verifier stash after exchange.** It is a proof-of-identity secret.
14. **Persist granted scope, not requested scope.** Write token-response
    `scope`; with `scopes_supported: []`, explicit scope list is authoritative,
    but only token response proves what was granted.
15. **OAuth access token may also be REST Bearer token.** If MCP is read-only but
    a write is needed, test documented provider REST API with `Authorization:
    Bearer ***` before requesting another key, within granted resource scope.
16. **Redaction can hide tokens.** Never print exchange response across turns;
    access token may become `***` and one-use `code` is consumed. Write token to
    final file in the SAME exchange block. Debug only `len(access_token)`,
    `token_type`, `scope`, `expires_in`.
17. **GitHub MCP uses pre-registered confidential OAuth.**
    `api.githubcopilot.com/mcp/` uses a real `client_secret` and
    `token_endpoint_auth_method: client_secret_post`; POST it to
    `https://github.com/login/oauth/access_token` with `client_id`, `code`,
    `code_verifier`, and `redirect_uri`. Redirect URI is fixed in the app; the
    listener-port trick cannot change it. Use PAT or pre-registered app, not DCR
    public-client registration.

## What Not to Do

- do not use `mcp-remote`; its npx callback server has the same remote-localhost failure, and Hermes speaks remote HTTP natively
- do not push API-token headers when user explicitly chose OAuth; offer static token only after explaining topology and with consent
- do not claim Hermes lacks a feature without inspecting source/docs

## Verification

- remote topology and profile-aware `HERMES_HOME` confirmed
- protected-resource/AS metadata fetched with safe User-Agent; endpoint values recorded
- PKCE, state verification, `resource`, scope omission rules, and DCR/pre-registered branch correct
- both token files exist with `0o700` directory/`0o600` files, safe filename, and no token printed
- manual `initialize` returns HTTP 200, event-stream content type, `serverInfo`, and `capabilities`
- `/reload-mcp` registers `mcp_<name>_*`; if not, classify breaker/refresh/session revocation before escalation
- verifier stash deleted; stale/invalid refresh token is routed to re-auth or static API key, not repeated

## Quick Reference Files

- `scripts/diagnose-oauth-mcp.py` — read-only-by-default diagnostic: smoke-test access token, refresh, smoke-test new token, print `TOKEN_OK`/`REFRESH_FIXED`/`SESSION_REVOKED`/`REFRESH_DEAD`; `--write` atomically persists a working refresh; never prints secrets. Run first when OAuth MCP says "not connected".
- `references/stripe-mcp-oauth-revocation.md` — Stripe recurring session-revocation example and durable restricted-key fix.

## Related

- `native-mcp` — Hermes MCP configuration guide and authoritative config reference
- `mcporter` — external CLI bridge for ad-hoc MCP calls outside Hermes config