---
name: honcho
description: Configure and troubleshoot Honcho memory for Hermes.
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Honcho, Memory, Profiles, Observation, Dialectic, User-Modeling, Session-Summary]
    homepage: https://docs.honcho.dev
    related_skills: [hermes-agent]
prerequisites:
  pip: [honcho-ai]
---

# Honcho Memory for Hermes

role: Honcho memory configuration/operator
do: set up cloud/local; verify connection/peers; choose recall/session strategy; tune observation/cadence/depth/level/budget; use five tools deliberately; troubleshoot persistence
inputs: Honcho deployment, API key/base URL, profile/workspace identity, recall mode, observation/dialectic/budget settings
outputs: profile-local Honcho config, peer/context state, conclusions, status/diagnostics
¬: expose API keys; call dialectic every turn; duplicate auto-injected context; confuse user/AI peers; delete non-PII conclusions casually; claim memory persisted without status/peer evidence

Honcho provides cross-session user modeling. Each Hermes profile has its own AI peer while profiles share a unified user/workspace view.

## When to Use

- cloud or self-hosted Honcho setup/troubleshooting
- profiles need distinct Honcho AI peers
- memory persistence, observation, recall, dialectic, or write-frequency tuning
- understanding Honcho tools, context budgets, or session-summary injection

## Prerequisites

- `honcho-ai` (`pip` metadata above)
- cloud account/API key from https://app.honcho.dev, or self-hosted base URL
- Hermes config and an active profile

## Procedure: Setup

### Cloud

```bash
hermes memory setup honcho
# select "cloud", paste API key from https://app.honcho.dev
```

### Self-hosted

```bash
hermes memory setup honcho
# select "local", enter base URL (e.g. http://localhost:8000)
```

Integration guide: https://docs.honcho.dev/v3/guides/integrations/hermes#running-honcho-locally-with-hermes

### Verify

```bash
hermes honcho status    # shows resolved config, connection test, peer info
```

Status should show resolved config, connection test, and peer info.

## Architecture

### Base Context Injection

In `hybrid`/`context` recall, injection order is:

1. **Session summary** — short current-session digest; first for continuity
2. **User representation** — accumulated preferences, facts, patterns
3. **AI peer card** — this profile's identity card

Honcho generates the summary at turn start when a prior session exists; it warms the model without replaying full history.

### Cold/Warm Selection

| Condition | Strategy | What happens |
|-----------|----------|--------------|
| No prior session or empty representation | **Cold start** | Lightweight intro prompt; skips summary injection; encourages the model to learn about the user |
| Existing representation and/or session history | **Warm start** | Full base context injection (summary → representation → card); richer system prompt |

Automatic; no configuration required.

### Peers

- **User peer** (`peerName`) represents the human; Honcho builds its representation from observations.
- **AI peer** (`aiPeer`) represents this Hermes profile; each profile gets its own AI peer.

### Observation

| Toggle | What it does |
|--------|-------------|
| `observeMe` | Peer's own messages are observed (builds self-representation) |
| `observeOthers` | Other peers' messages are observed (builds cross-peer understanding) |

Default: all four user/AI toggles on.

```json
{
  "observation": {
    "user": { "observeMe": true, "observeOthers": true },
    "ai":   { "observeMe": true, "observeOthers": true }
  }
}
```

Presets:

| Preset | User | AI | Use case |
|--------|------|----|----------|
| `"directional"` (default) | me:on, others:on | me:on, others:on | Multi-agent, full memory |
| `"unified"` | me:on, others:off | me:off, others:on | Single agent, user-only modeling |

Dashboard changes sync on session init; server-side config wins over local defaults.

### Sessions

| Strategy | Behavior |
|----------|----------|
| `per-directory` (default) | One session per working directory |
| `per-repo` | One session per git repository root |
| `per-session` | New Honcho session each Hermes run |
| `global` | Single session across all directories |

Manual mapping: `hermes honcho map my-project-name`.

### Recall Modes

| Mode | Auto-inject context? | Tools available? | Use case |
|------|---------------------|-----------------|----------|
| `hybrid` (default) | Yes | Yes | Agent decides when to use tools vs auto context |
| `context` | Yes | No (hidden) | Minimal token cost, no tool calls |
| `tools` | No | Yes | Agent controls all memory access explicitly |

## Dialectic Controls: Three Orthogonal Knobs

### Cadence (when)

| Key | Default | Description |
|-----|---------|-------------|
| `contextCadence` | `1` | Min turns between context API calls |
| `dialecticCadence` | `2` | Min turns between dialectic API calls. Recommended 1–5 |
| `injectionFrequency` | `every-turn` | `every-turn` or `first-turn` for base context injection |

Higher cadence fires Honcho's dialectic LLM less often; `dialecticCadence: 2` means every other turn; `1` means every turn.

### Depth (how many)

| Key | Default | Range | Description |
|-----|---------|-------|-------------|
| `dialecticDepth` | `1` | 1-3 | Number of dialectic reasoning rounds per query |
| `dialecticDepthLevels` | -- | array | Optional per-depth-round level overrides (see below) |

Two rounds produce initial answer then refinement. Example:

```json
{
  "dialecticDepth": 3,
  "dialecticDepthLevels": ["low", "medium", "high"]
}
```

Without overrides, proportional levels from `dialecticReasoningLevel`:

| Depth | Pass levels |
|-------|-------------|
| 1 | [base] |
| 2 | [minimal, base] |
| 3 | [minimal, base, low] |

Session-start prewarm runs full configured depth in background before turn 1. Turn 1 consumes it; if late, a bounded synchronous call runs. Multi-pass avoids thin cold-peer output by completing audit/reconcile before user turn.

### Level (how hard)

| Key | Default | Description |
|-----|---------|-------------|
| `dialecticReasoningLevel` | `low` | `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | When `true`, the model can pass `reasoning_level` to `honcho_reasoning` to override the default per-call. `false` = always use `dialecticReasoningLevel`, model overrides ignored |

Higher level costs more Honcho-backend tokens and yields richer synthesis.

## Multi-Profile Setup

Profiles share user representation/workspace but have independent AI identities/observations; conclusions written by one are visible to others through shared workspace.

### Create

```bash
hermes profile create coder --clone
# creates host block hermes.coder, AI peer "coder", inherits config from default
```

`--clone`:

1. creates `hermes.coder` host block in `honcho.json`
2. sets `aiPeer: "coder"`
3. inherits `workspace`, `peerName`, `writeFrequency`, `recallMode`, etc.
4. eagerly creates peer before first message

Backfill:

```bash
hermes honcho sync    # creates host blocks for all profiles that don't have one yet
```

Example host override:

```json
{
  "hosts": {
    "hermes.coder": {
      "aiPeer": "coder",
      "recallMode": "tools",
      "dialecticDepth": 2,
      "observation": {
        "user": { "observeMe": true, "observeOthers": false },
        "ai": { "observeMe": true, "observeOthers": true }
      }
    }
  }
}
```

## Tools

Five bidirectional tools; hidden in `context` recall mode:

| Tool | LLM call? | Cost | Use when |
|------|-----------|------|----------|
| `honcho_profile` | No | minimal | Quick factual snapshot at conversation start or for fast name/role/pref lookups |
| `honcho_search` | No | low | Fetch specific past facts to reason over yourself — raw excerpts, no synthesis |
| `honcho_context` | No | low | Full session context snapshot: summary, representation, card, recent messages |
| `honcho_reasoning` | Yes | medium–high | Natural language question synthesized by Honcho's dialectic engine |
| `honcho_conclude` | No | minimal | Write or delete a persistent fact; pass `peer: "ai"` for AI self-knowledge |

### Tool contracts

- `honcho_profile`: read card; pass `card: [...]` to update; omit to read.
- `honcho_search`: semantic raw excerpts, ranked; default 800 tokens, max 2000; no synthesis.
- `honcho_context`: full current session summary, representation, card, recent messages; no LLM.
- `honcho_reasoning`: natural-language synthesis; `reasoning_level`=`minimal`→`low`→`medium`→`high`→`max`; omit for configured default (`low`).
- `honcho_conclude`: exactly one of `conclusion: "..."` or `delete_id: "..."`; delete only for PII removal, as Honcho self-heals incorrect conclusions.

All accept optional `peer`: `"user"` default, `"ai"`, or explicit workspace peer ID.

```
honcho_profile                        # read user's card
honcho_profile peer="ai"              # read AI peer's card
honcho_reasoning query="What does this user care about most?"
honcho_reasoning query="What are my interaction patterns?" peer="ai" reasoning_level="medium"
honcho_conclude conclusion="Prefers terse answers"
honcho_conclude conclusion="I tend to over-explain code" peer="ai"
honcho_conclude delete_id="abc123"    # PII removal
```

## Usage Patterns

### Conversation start

```
1. honcho_profile                  → fast warmup, no LLM cost
2. If context looks thin → honcho_context  (full snapshot, still no LLM)
3. If deep synthesis needed → honcho_reasoning  (LLM call, use sparingly)
```

Do not call `honcho_reasoning` every turn; auto-injection handles ongoing refresh. Use it only when injected context lacks synthesized insight.

### New memory

```
honcho_conclude conclusion="<specific, actionable fact>"
```

Good: `Prefers code examples over prose explanations`; `Working on a Rust async project through April 2026`. Bad: `User said something about Rust` (vague); `User seems technical` (already represented).

### Specific recall

```
honcho_search query="<topic>"       → fast, no LLM, good for specific facts
honcho_context                       → full snapshot with summary + messages
honcho_reasoning query="<question>"  → synthesized answer, use when search isn't enough
```

### AI self-knowledge

```text
honcho_conclude conclusion="I tend to be verbose when explaining architecture" peer="ai"
honcho_reasoning query="How do I typically handle ambiguous requests?" peer="ai"
honcho_profile peer="ai"
```

### Skip redundant calls

In `hybrid`/`context`, user representation + card + summary are injected before every turn. Call tools only when injected context lacks the answer, user explicitly asks recall, or a new conclusion is needed.

Explicit `honcho_reasoning` shares auto-injection cost; after it, auto cadence resets to avoid double charging the turn.

## Config Reference

Config: `$HERMES_HOME/honcho.json` (profile-local) or `~/.honcho/config.json` (global).

### General

| Key | Default | Description |
|-----|---------|-------------|
| `apiKey` | -- | API key ([get one](https://app.honcho.dev)) |
| `baseUrl` | -- | Base URL for self-hosted Honcho |
| `peerName` | -- | User peer identity |
| `aiPeer` | host key | AI peer identity |
| `workspace` | host key | Shared workspace ID |
| `recallMode` | `hybrid` | `hybrid`, `context`, or `tools` |
| `observation` | all on | Per-peer `observeMe`/`observeOthers` booleans |
| `writeFrequency` | `async` | `async`, `turn`, `session`, or integer N |
| `sessionStrategy` | `per-directory` | `per-directory`, `per-repo`, `per-session`, `global` |
| `messageMaxChars` | `25000` | Max chars per message (chunked if exceeded) |

### Dialectic

| Key | Default | Description |
|-----|---------|-------------|
| `dialecticReasoningLevel` | `low` | `minimal`, `low`, `medium`, `high`, `max` |
| `dialecticDynamic` | `true` | Auto-bump reasoning by query complexity. `false` = fixed level |
| `dialecticDepth` | `1` | Number of dialectic rounds per query (1-3) |
| `dialecticDepthLevels` | -- | Optional array of per-round levels, e.g. `["low", "high"]` |
| `dialecticMaxInputChars` | `10000` | Max chars for dialectic query input |

### Context budget/injection

| Key | Default | Description |
|-----|---------|-------------|
| `contextTokens` | uncapped | Max tokens for the combined base context injection (summary + representation + card). Opt-in cap — omit to leave uncapped, set to an integer to bound injection size. |
| `injectionFrequency` | `every-turn` | `every-turn` or `first-turn` |
| `contextCadence` | `1` | Min turns between context API calls |
| `dialecticCadence` | `2` | Min turns between dialectic LLM calls (recommended 1–5) |

At injection, if context exceeds `contextTokens`, trim summary first, then representation, preserve card.

### Sanitization

Honcho sanitizes injected `memory-context`:

- strips XML/HTML tags from user conclusions
- normalizes whitespace/control characters
- truncates conclusions over `messageMaxChars`
- escapes delimiters that could corrupt system-prompt structure

## Pitfalls

Use the troubleshooting matrix below when a verification check fails.

## Troubleshooting

| Symptom | Check/fix |
|---|---|
| “Honcho not configured” | `hermes honcho setup`; ensure `memory.provider: honcho` in `~/.hermes/config.yaml` |
| no cross-session memory | `hermes honcho status`; verify `saveMessages: true`; `writeFrequency`=`session` writes only on exit |
| profile lacks own peer | create with `hermes profile create <name> --clone`; existing→`hermes honcho sync` |
| dashboard observation not reflected | server syncs on session init; start a new session |
| messages truncated | >`messageMaxChars` (default 25k) chunk with `[continued]`; inspect tool/skill size |
| context budget exceeded | lower `contextTokens` or `dialecticDepth`; summary trims first |
| session summary missing | requires prior turn in current Honcho session; cold start intentionally omits it |

## CLI Commands

| Command | Description |
|---------|-------------|
| `hermes honcho setup` | Interactive setup wizard (cloud/local, identity, observation, recall, sessions) |
| `hermes honcho status` | Show resolved config, connection test, peer info for active profile |
| `hermes honcho enable` | Enable Honcho for the active profile (creates host block if needed) |
| `hermes honcho disable` | Disable Honcho for the active profile |
| `hermes honcho peer` | Show or update peer names (`--user <name>`, `--ai <name>`, `--reasoning <level>`) |
| `hermes honcho peers` | Show peer identities across all profiles |
| `hermes honcho mode` | Show or set recall mode (`hybrid`, `context`, `tools`) |
| `hermes honcho tokens` | Show or set token budgets (`--context <N>`, `--dialectic <N>`) |
| `hermes honcho sessions` | List known directory-to-session-name mappings |
| `hermes honcho map <name>` | Map current working directory to a Honcho session name |
| `hermes honcho identity` | Seed AI peer identity or show both peer representations |
| `hermes honcho sync` | Create host blocks for all Hermes profiles that don't have one yet |
| `hermes honcho migrate` | Step-by-step migration guide from OpenClaw native memory to Hermes + Honcho |
| `hermes memory setup` | Generic memory provider picker (selecting "honcho" runs the same wizard) |
| `hermes memory status` | Show active memory provider and config |
| `hermes memory off` | Disable external memory provider |

## Verification

- `hermes honcho status` shows resolved provider, reachable endpoint, workspace, and peer info
- cold session omits summary; warm session injects summary → representation → AI card
- profile clone has independent `aiPeer` and shared workspace
- recall mode exposes/omits tools as table specifies
- context budget trims summary before representation and preserves card
- `honcho_conclude` receives exactly one create/delete input; PII deletion is explicit
- cadence/depth/level settings match requested cost/quality trade-off
