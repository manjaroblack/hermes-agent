---
name: mcporter
description: List, auth, and call MCP servers/tools from the terminal.
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, API, Integrations, Interop]
    homepage: https://mcporter.dev
prerequisites:
  commands: [npx]
---

# mcporter

role: terminal MCP server/tool discovery, auth, call, and config operator
do: list servers; inspect schemas; call tools; connect ad hoc HTTP/stdio; authenticate; manage config/daemon; generate wrappers/types; parse JSON
inputs: server/tool spec; `key=value` or JSON args; HTTP URL/stdio command; config key/path; auth target
outputs: structured MCP result; server/schema inventory; auth/config state; daemon status; generated CLI/TypeScript client
¬: trust unknown server; omit required args; expose OAuth/token output; edit unrelated config; use unstructured output when JSON is available

Use `mcporter` to discover, call, and manage [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) servers/tools directly from the terminal.

## When to Use

- inspect MCP servers configured by Claude Desktop, Cursor, or another client
- call a known MCP tool from the terminal
- connect to a one-off HTTP URL or stdio server without config
- authenticate/configure a server, run a persistent daemon
- generate a CLI wrapper or TypeScript client/types

## Prerequisites

Requires Node.js. `npx` needs no install:

```bash
# No install needed (runs via npx)
npx mcporter list

# Or install globally
npm install -g mcporter
```

## Procedure

### 1. Discover servers and schemas

```bash
# List MCP servers already configured on this machine
mcporter list

# List tools for a specific server with schema details
mcporter list <server> --schema

# Call a tool
mcporter call <server.tool> key=value
```

`mcporter` auto-discovers servers configured by other MCP clients. Browse
[mcpfinder.dev](https://mcpfinder.dev) or [mcp.so](https://mcp.so) for new
servers, then connect ad hoc:

```bash
# Connect to any MCP server by URL (no config needed)
mcporter list --http-url https://some-mcp-server.com --name my_server

# Or run a stdio server on the fly
mcporter list --stdio "npx -y @modelcontextprotocol/server-filesystem" --name fs
```

### 2. Call tools

```bash
# Key=value syntax
mcporter call linear.list_issues team=ENG limit:5

# Function syntax
mcporter call "linear.create_issue(title: \"Bug fix needed\")"

# Ad-hoc HTTP server (no config needed)
mcporter call https://api.example.com/mcp.fetch url=https://example.com

# Ad-hoc stdio server
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com

# JSON payload
mcporter call <server.tool> --args '{"limit": 5}'

# Machine-readable output (recommended for Hermes)
mcporter call <server.tool> key=value --output json
```

Prefer `--output json` for parsing. Confirm server/tool schema before sending
arguments; preserve required types and names.

### 3. Authenticate and manage config

```bash
# OAuth login for a server
mcporter auth <server | url> [--reset]

# Manage config
mcporter config list
mcporter config get <key>
mcporter config add <server>
mcporter config remove <server>
mcporter config import <path>
```

Config lives at `./config/mcporter.json`; override with `--config`. OAuth may
open an interactive browser: use `terminal(command="mcporter auth <server>", pty=true)`.

### 4. Maintain a daemon

```bash
mcporter daemon start
mcporter daemon status
mcporter daemon stop
mcporter daemon restart
```

Use the daemon for persistent server connections; check status after start or
restart before issuing dependent calls.

### 5. Generate clients

```bash
# Generate a CLI wrapper for an MCP server
mcporter generate-cli --server <name>
mcporter generate-cli --command <url>

# Inspect a generated CLI
mcporter inspect-cli <path> [--json]

# Generate TypeScript types/client
mcporter emit-ts <server> --mode client
mcporter emit-ts <server> --mode types
```

## Pitfalls

- Ad-hoc HTTP/stdio servers work without config; do not add persistent config for a one-off call unless requested.
- OAuth may require interactive browser flow; pass `pty=true` to the terminal invocation.
- Use `--output json` for machine-readable results and error handling.
- Treat untrusted server URLs/stdio commands as external code; require user intent and inspect schema before calls.
- Keep auth material out of output, logs, and durable notes.

## Verification

- `npx mcporter list` returns or clearly reports the configured-server inventory.
- `mcporter list <server> --schema` confirms tool names/arguments before calls.
- a representative `mcporter call ... --output json` returns parseable structured output.
- auth/config changes are scoped to the intended target and config path.
- daemon operations are followed by `mcporter daemon status`.
- generated CLI/client passes `inspect-cli` or emits the requested mode.