---
name: fastmcp
description: Build, test, and deploy Python MCP servers.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, FastMCP, Python, Tools, Resources, Prompts, Deployment]
    homepage: https://gofastmcp.com
    related_skills: [hermes-agent, mcporter]
prerequisites:
  commands: [python]
---

# FastMCP

role: Python FastMCP server builder/tester/deployer
do: choose smallest server; scaffold; implement typed tools; add resources/prompts only when useful; inspect/list/call locally; install client; validate HTTP/deploy contract
inputs: API/database/CLI/file workflow; server name; template; environment-variable contract; client/deployment target
outputs: importable MCP server; tools/resources/prompts; validated CLI/HTTP endpoint; client registration or deployment handoff
¬: expose an entire API by default; vague/untyped tools; unsafe writes; hardcode auth; deploy before real calls; use `native-mcp`/`mcporter` scope interchangeably

Build MCP servers in Python with FastMCP, validate locally, install into MCP
clients, and prepare HTTP deployment.

## When to Use

- create a Python MCP server
- wrap an API, database, CLI, or file workflow as MCP tools
- expose resources or prompts in addition to tools
- smoke-test with FastMCP CLI before Hermes/client integration
- install into Claude Code, Claude Desktop, Cursor, or another MCP client
- prepare a FastMCP repo for HTTP deployment

Use `native-mcp` when an existing server only needs Hermes connection. Use
`mcporter` for ad-hoc CLI access to an existing server rather than building one.

## Prerequisites

```bash
pip install fastmcp
fastmcp version
```

API template dependency:

```bash
pip install httpx
```

Included assets:

- `templates/api_wrapper.py` — REST wrapper with auth-header support
- `templates/database_server.py` — read-only SQLite query server
- `templates/file_processor.py` — text-file inspection/search server
- `scripts/scaffold_fastmcp.py` — template copier/name substitution
- `references/fastmcp-cli.md` — CLI, install targets, deployment checks

## Procedure

### 1. Choose the smallest viable shape

- API wrapper: 1-3 high-value endpoints, not the whole API
- database: read-only introspection plus constrained query
- file processor: deterministic operations with explicit path arguments
- resources/prompts: only when reusable prompts or discoverable documents help

Prefer a thin server with concrete names, user-facing docstrings, and schemas.

### 2. Scaffold

```bash
python ~/.hermes/skills/mcp/fastmcp/scripts/scaffold_fastmcp.py \
  --template api_wrapper \
  --name "Acme API" \
  --output ./acme_server.py
```

List templates:

```bash
python ~/.hermes/skills/mcp/fastmcp/scripts/scaffold_fastmcp.py --list
```

Manual copies must replace `__SERVER_NAME__`.

### 3. Implement tools first

Start with `@mcp.tool` functions. Every tool: concrete verb name; user-facing
docstring; explicit typed parameters; JSON-safe structured result where possible;
early unsafe-input validation; read-only default for first versions.

Good names: `get_customer`, `search_tickets`, `describe_table`,
`summarize_text_file`. Weak names: `run`, `process`, `do_thing`.

### 4. Add resources/prompts selectively

- `@mcp.resource`: stable read-only schemas, policy docs, generated reports
- `@mcp.prompt`: reusable template for a known workflow
- tools = actions; resources = data/document retrieval; prompts = reusable LLM instructions

Do not turn every document into a prompt.

### 5. Validate before integration

```bash
fastmcp inspect acme_server.py:mcp
fastmcp list acme_server.py --json
fastmcp call acme_server.py search_resources query=router limit=5 --json
```

Fast iteration:

```bash
fastmcp run acme_server.py:mcp
```

HTTP transport:

```bash
fastmcp run acme_server.py:mcp --transport http --host 127.0.0.1 --port 8000
fastmcp list http://127.0.0.1:8000/mcp --json
fastmcp call http://127.0.0.1:8000/mcp search_resources query=router --json
```

Run at least one real `fastmcp call` against each new tool.

### 6. Install into a client

```bash
fastmcp install claude-code acme_server.py
fastmcp install claude-desktop acme_server.py
fastmcp install cursor acme_server.py -e .
```

Use `fastmcp discover` to inspect named MCP servers already configured.
For Hermes, configure `mcp_servers.<name>` in `~/.hermes/config.yaml` using
`native-mcp`, or continue FastMCP CLI development until the interface stabilizes.

### 7. Deploy after the contract is stable

FastMCP documents Prefect Horizon most directly for managed hosting. Before
deployment:

```bash
fastmcp inspect acme_server.py:mcp
```

Repository must contain a Python file with the FastMCP server object,
`requirements.txt` or `pyproject.toml`, and deployment environment-variable
documentation. For generic HTTP hosting, validate locally, then use any
Python-compatible platform that exposes the server port.

## Patterns

### API wrapper

Start with one read path, one list/search path, and optional health check. Keep
auth in environment variables, centralize request logic, surface concise API
errors, and normalize inconsistent upstream payloads. Start from
`templates/api_wrapper.py`.

### Database

Start with `list_tables`, `describe_table`, and one constrained read query.
Default read-only; reject non-`SELECT` SQL in early versions; cap row counts;
return rows plus column names. Start from `templates/database_server.py`.

### File processor

Start with content summary, in-file search, and deterministic metadata. Accept
explicit paths; handle missing files/encoding failures; cap previews/results;
avoid shelling out unless a required external tool demands it. Start from
`templates/file_processor.py`.

## Pitfalls

- `fastmcp inspect` needs an importable file and correctly named `<file.py:object>` instance.
- Install optional template dependencies before blaming the CLI.
- CLI/Python mismatches usually mean wrong tool name, missing required args, or non-serializable return.
- Keep secrets in environment variables, never source or hardcode them.
- A server can be correct while Hermes config is wrong; use `native-mcp` and `~/.hermes/config.yaml` for that boundary.
- Do not call a server deployed until every new tool has a real local call.

## Verification

- `fastmcp version` succeeds in the active environment.
- server imports cleanly; `fastmcp inspect <file.py:mcp>` succeeds.
- `fastmcp list <server spec> --json` succeeds.
- every new tool has a real `fastmcp call`.
- env vars are documented; surface is small and understandable.
- HTTP transport is tested locally before deployment.

## Troubleshooting

### FastMCP command missing

```bash
pip install fastmcp
fastmcp version
```

### `fastmcp inspect` fails

Check import side effects, FastMCP instance name in `<file.py:object>`, and
optional template dependencies.

### Tool works in Python but not through CLI

```bash
fastmcp list server.py --json
fastmcp call server.py your_tool_name --json
```

Use this to expose naming mismatches, missing args, or non-serializable returns.

### Hermes cannot see the deployed server

Load `native-mcp`, configure `~/.hermes/config.yaml`, and restart Hermes after
confirming the server's own build/inspection path works.