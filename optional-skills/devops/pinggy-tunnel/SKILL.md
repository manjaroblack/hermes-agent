---
name: pinggy-tunnel
description: Zero-install localhost tunnels over SSH via Pinggy.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Pinggy, Tunnel, Networking, SSH, Webhook, Localhost]
    related_skills: []
---

# Pinggy Tunnel Skill

role: Pinggy tunnel operator
do: verify loopback origin; select HTTP/TCP/TLS/auth mode; launch background SSH reverse tunnel; parse URL; verify reachability; tear down process
inputs: local port/service, tunnel mode, optional access-control keywords, optional `PINGGY_TOKEN`
outputs: public URL/endpoint, access-control details, origin/tunnel verification, teardown handle
¬: expose sensitive origins without `b:`, `k:`, or `w:`; foreground-block on long tunnel; leak tokens/passwords; assume TCP/TLS returns HTTPS; trust URL before origin check; use tunnel as durable storage/config

Expose a local dev server, webhook receiver, MCP HTTP endpoint, demo, or local LLM through the stock SSH client to `a.pinggy.io:443`; no daemon install. Free tier: 60-minute random-subdomain tunnel, no signup. Pro is opt-in via token ($3/mo; persistent/custom domain, multiple tunnels, no cap).

## When to Use

- expose localhost, share a dev server, make a URL public, tunnel a port, or receive webhooks
- one-off HTTP demo for MCP, Ollama/vLLM, or dashboard
- host has SSH but no configured `cloudflared`/`ngrok`
- use `cloudflared-quick-tunnel` instead when already configured; its quick tunnels do not expire after 60 minutes

## Prerequisites

- `ssh` on PATH (`ssh -V`); stock Linux/macOS/Windows 10+ client
- origin listening on `127.0.0.1:<port>`; Pinggy URL returns 502 until origin exists
- optional `PINGGY_TOKEN` for Pro; free tier needs no credential

## Quick Reference

```bash
# Plain HTTP/HTTPS tunnel for port 8000 (free tier)
ssh -p 443 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -R0:localhost:8000 free@a.pinggy.io

# TCP tunnel (databases, raw SSH, etc.)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:5432 tcp@a.pinggy.io

# TLS tunnel (Pinggy can't decrypt — bring your own certs at origin)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:443 tls@a.pinggy.io

# Basic auth gate (b:user:pass)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "b:admin:secret+free@a.pinggy.io"

# Bearer token gate (k:token)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "k:mysecrettoken+free@a.pinggy.io"

# IP whitelist (w:CIDR)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "w:203.0.113.0/24+free@a.pinggy.io"

# Enable CORS + force HTTPS redirect
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 \
    "co+x:https+free@a.pinggy.io"

# Pro tier (persistent URL, no 60-min cap)
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:8000 "$PINGGY_TOKEN+a.pinggy.io"
```

## Procedure — Start a Tunnel and Get the URL

Use `terminal` for the tunnel; keep it in a background process, capture stdout/stderr, parse the URL, verify the origin through the tunnel, and retain a kill/process handle.

### 1. Confirm a local origin is up

```bash
curl -sI http://127.0.0.1:8000/ | head -1
# expect HTTP/1.x 200 (or any non-connection-refused response)
```

If absent, start the origin first, e.g. `python -m http.server 8000 --bind 127.0.0.1`. Pinggy returns a URL even when the origin is absent; users see 502 until it starts.

### 2. Launch the tunnel as a background process

Use `terminal(background=True)` and redirect the banner to a logfile:

```bash
LOG=/tmp/pinggy-8000.log
nohup ssh -p 443 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -R0:localhost:8000 free@a.pinggy.io \
    > "$LOG" 2>&1 &
echo $! > /tmp/pinggy-8000.pid
```

`StrictHostKeyChecking=no` + `UserKnownHostsFile=/dev/null` skips the first-run prompt. `ServerAliveInterval=30` avoids idle-NAT teardown.

### 3. Parse the URL out of the log

```bash
sleep 4
grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/pinggy-8000.log | head -1
```

Expected output looks like:

```
You are not authenticated.
Your tunnel will expire in 60 minutes.
http://yqycl-98-162-69-48.a.free.pinggy.link
https://yqycl-98-162-69-48.a.free.pinggy.link
```

Return the `https://...pinggy.link` URL, not the banner text.

### 4. Verify

```bash
curl -sI https://<the-url>/ | head -3
# expect 200/302/whatever the local origin actually returns
```

502 means SSH is up but the local origin is not listening; repair step 1.

### 5. Teardown

```bash
kill "$(cat /tmp/pinggy-8000.pid)"
# or, if the pid file got lost:
pkill -f 'ssh -p 443 .* free@a\.pinggy\.io'
```

If `terminal(background=True)` returned a session, prefer `process(action='kill', session_id=...)`.

## Access Control via Username Keywords

Flags stack in the SSH username with `+`; quote the whole `user@host` value whenever it contains `+`.

| Keyword | Effect |
|---------|--------|
| `b:user:pass` | HTTP Basic auth gate |
| `k:token` | Bearer-token header gate (`Authorization: Bearer <token>`) |
| `w:CIDR` | IP whitelist (single IP or CIDR, repeatable) |
| `co` | Add `Access-Control-Allow-Origin: *` (CORS) |
| `x:https` | Force HTTPS — auto-redirect HTTP to HTTPS |
| `a:Name:Value` | Add request header |
| `u:Name:Value` | Update request header |
| `r:Name` | Remove request header |
| `qr` | Print a QR code of the URL to stdout (handy for mobile sharing) |

Combine flags: `"b:admin:secret+co+x:https+free@a.pinggy.io"`.

## Web Debugger (Optional)

Mirror inbound traffic to `localhost:4300` with a local forward, then open the debugger:

```bash
ssh -p 443 -L4300:localhost:4300 -R0:localhost:8000 free@a.pinggy.io
```

Open `http://localhost:4300` to inspect live request/response pairs.

## Pitfalls

- free tier hard-stops at 60 minutes; Pro or an auto-restart loop is required for longer shares; free restarts change URL
- free URL is random and changes on restart; never bookmark or put it in config; re-parse logs
- one concurrent free tunnel per source IP is typical; Pro lifts it
- quote usernames containing `+`
- bare HTTP is public; protect non-public services with `b:`, `k:`, or `w:`
- `process(action='log')` may miss the interactive SSH banner; redirect and grep the logfile
- disable host-key prompt for unattended runs with both `StrictHostKeyChecking=no` and `UserKnownHostsFile=/dev/null`
- TCP/TLS returns `<subdomain>.a.pinggy.online:<port>`, not HTTPS; parse with the mode-specific form
- Pro token is the username (`"$PINGGY_TOKEN+a.pinggy.io"`), not a flag; `:persistent` can request a stable subdomain

## Recipes

Each recipe: start loopback origin, start protected tunnel, parse URL, hand it to the caller, then tear down both processes.

### Recipe 1 — Receive a webhook callback

Use for Stripe, GitHub, Discord, AgentMail, or another external POST callback.

```bash
# 1. Tiny capturing server: every request gets appended to /tmp/webhook-hits.log
cat >/tmp/webhook-server.py <<'PY'
import http.server, json, datetime, pathlib
LOG = pathlib.Path("/tmp/webhook-hits.log")
class H(http.server.BaseHTTPRequestHandler):
    def _capture(self):
        n = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
        rec = {"t": datetime.datetime.utcnow().isoformat(), "path": self.path,
               "method": self.command, "headers": dict(self.headers), "body": body}
        with LOG.open("a") as f: f.write(json.dumps(rec) + "\n")
        self.send_response(200); self.send_header("content-type","application/json")
        self.end_headers(); self.wfile.write(b'{"ok":true}\n')
    def do_GET(self): self._capture()
    def do_POST(self): self._capture()
    def log_message(self,*a,**k): pass
http.server.HTTPServer(("127.0.0.1", 18080), H).serve_forever()
PY
nohup python /tmp/webhook-server.py >/tmp/webhook-server.log 2>&1 &
echo $! >/tmp/webhook-server.pid

# 2. Tunnel — bearer-token-gate so randos can't pollute the capture log
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:18080 "k:$(openssl rand -hex 12)+free@a.pinggy.io" \
    >/tmp/webhook-pinggy.log 2>&1 &
echo $! >/tmp/webhook-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/webhook-pinggy.log | head -1)
echo "Webhook URL: $URL"

# 3. While the agent works, watch hits land
tail -f /tmp/webhook-hits.log
```

Hand `$URL` to the caller. Teardown: `kill $(cat /tmp/webhook-server.pid) $(cat /tmp/webhook-pinggy.pid)`.

### Recipe 2 — Expose an MCP server over HTTP/SSE

Only HTTP-transport MCP servers can be tunneled; stdio servers cannot.

```bash
# 1. Start the MCP server in HTTP mode (example: a FastMCP server on port 8765)
nohup python my_mcp_server.py --transport http --port 8765 \
    >/tmp/mcp-server.log 2>&1 &
echo $! >/tmp/mcp-server.pid

# 2. Tunnel with a bearer token — MCP traffic should not be open to the internet
TOKEN=$(openssl rand -hex 16)
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:8765 "k:$TOKEN+free@a.pinggy.io" \
    >/tmp/mcp-pinggy.log 2>&1 &
echo $! >/tmp/mcp-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/mcp-pinggy.log | head -1)
echo "MCP URL: $URL"
echo "Bearer token: $TOKEN"
```

Connect the remote client with `Authorization: Bearer ***`; Hermes native MCP config shape: `{"transport": "http", "url": "<URL>", "headers": {"Authorization": "Bearer <TOKEN>"}}`.

### Recipe 3 — Expose a local LLM endpoint

Ollama defaults to `:11434`; vLLM/llama.cpp typically use `:8000`.

```bash
# Pre-req: the model server is already running on 127.0.0.1:11434 (Ollama default)
TOKEN=$(openssl rand -hex 16)
nohup ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:11434 "k:$TOKEN+co+free@a.pinggy.io" \
    >/tmp/llm-pinggy.log 2>&1 &
echo $! >/tmp/llm-pinggy.pid
sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/llm-pinggy.log | head -1)
echo "Endpoint: $URL"
echo "Token:    $TOKEN"

# Verify
curl -s "$URL/api/tags" -H "Authorization: Bearer $TOKEN" | head
```

`co` enables browser CORS; drop it for backend-only callers. OpenAI-compatible callers use `$URL/v1` with `Authorization: Bearer ***`; Pinggy does not rewrite the body, so local server auth should be ignored on loopback while Pinggy gates access.

### Recipe 4 — Share a dev server with a one-shot password

Generate a one-time password; share URL + password; Ctrl-C tears down.

```bash
PASS=$(openssl rand -base64 12 | tr -d '+/=' | head -c 12)
echo "Dev server password: $PASS"
ssh -p 443 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ServerAliveInterval=30 \
    -R0:localhost:3000 "b:dev:$PASS+co+x:https+free@a.pinggy.io"
# URL prints to the terminal. Share URL + password. Ctrl-C to tear down.
```

`b:dev:$PASS` gates Basic auth; `x:https` forces TLS; `co` enables CORS.

## Verification

```bash
# End-to-end: spin up a trivial origin, tunnel it, hit it, tear down
python -m http.server 18000 --bind 127.0.0.1 >/tmp/origin.log 2>&1 &
ORIGIN_PID=$!

nohup ssh -p 443 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -R0:localhost:18000 free@a.pinggy.io >/tmp/pinggy-verify.log 2>&1 &
SSH_PID=$!

sleep 5
URL=$(grep -oE 'https://[a-z0-9-]+\.[a-z]+\.pinggy\.link' /tmp/pinggy-verify.log | head -1)
echo "URL: $URL"
curl -sI "$URL/" | head -1

kill "$SSH_PID" "$ORIGIN_PID"
```

Expected: a `pinggy.link` URL and `HTTP/2 200` on the curl head.
