---
name: actual-setup
description: Set up Actual Computer (actual.inc) inference in Hermes.
version: 2.0.0
author: shl0ms + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [actual, actual-inc, provider, local-inference, relay, gguf, setup]
    category: devops
---

# Actual Computer Setup

role: Actual Computer provider setup/operator
do: choose relay/local; authenticate safely; discover/load model; set Hermes provider; verify response; diagnose transport/context failures
inputs: Actual account/key or authorized daemon, model ID, relay/local endpoint, context size/toolset
outputs: configured `actual` provider, selected model, verified relay/local inference
¬: put secrets in config.yaml; authorize for user; invent OAuth/email; create `custom_providers` named actual; use undersized context/full schema; claim empty stream is success

Set up [actual.inc](https://actual.inc) as Hermes' `actual` provider. Actual exposes an OpenAI-compatible API through an end-to-end-encrypted relay at `https://api.actual.inc` (`ac_` key) or local daemon `http://127.0.0.1:8080` (loopback no auth). This skill does not install/authorize the daemon for the user; device authorization requires a human browser action.

## When to Use

- add actual.inc relay or local inference provider
- route Hermes through an Actual cluster
- fully local on-device inference
- diagnose cryptic 400s, empty streams, or model loading issues

## Prerequisites

- current Hermes first-class provider `actual`; aliases `actual-computer`, `actualcomputer`, `aci`
- do not configure `providers.actual.*`/`custom_providers`; built-in provider handles base URL normalization, Responses transport, and local no-auth
- relay: Actual account + `ac_` key from https://actual.inc/user/keys
- local: user installs daemon `curl -fsSL "https://actual.inc/install" | bash`, runs `actual`, opens printed `https://actual.inc/device?code=...` in browser; codes expire in 5 minutes

## Procedure

### Relay/API

1. Store secret only in `~/.hermes/.env`: `ACTUAL_API_KEY=ac_...`.
2. Discover models:

   ```bash
   curl -s https://api.actual.inc/v1/models -H "Authorization: Bearer ***"
   ```

3. Configure:

   ```bash
   hermes config set model.provider actual
   hermes config set model.default "MODEL_ID_FROM_DISCOVERY"
   ```

4. Verify:

   ```bash
   hermes chat -Q -q "Reply with exactly: ACTUAL_OK" --provider actual -m MODEL_ID
   ```

### Local daemon

1. Human installs/authorizes daemon as above; relay URL and wait, never authorize on their behalf.
2. Search/download/load model:

   ```bash
   actual models search "qwen2.5 0.5b instruct gguf" --limit 8 --no-prompt
   actual models download "Qwen/Qwen2.5-0.5B-Instruct-GGUF/Q4_K_M"
   actual models list
   actual models load "qwen2.5-0.5b-instruct-q4_k_m"
   ```

   Download requires explicit quantization; use installed name from `models list` for `load`.
3. Add `ACTUAL_BASE_URL=http://127.0.0.1:8080` to `~/.hermes/.env`; loopback selects built-in local no-auth, no key needed:

   ```bash
   hermes config set model.provider actual
   hermes config set model.default "INSTALLED_MODEL_NAME"
   hermes chat -Q -q "Reply with exactly: LOCAL_OK" --provider actual -m INSTALLED_NAME -t file,web
   ```

## Quick Reference

| Thing | Value |
|---|---|
| Hosted relay | `https://api.actual.inc/v1` (normalized from bare host automatically) |
| Local daemon | `http://127.0.0.1:8080/v1` (no auth on loopback) |
| Key env var | `ACTUAL_API_KEY` (`ac_...`) |
| Base URL env var | `ACTUAL_BASE_URL` (loopback host ⇒ local no-auth mode) |
| Provider id / aliases | `actual` / `actual-computer`, `actualcomputer`, `aci` |
| Transport | Responses API (`codex_responses`) — built-in, do not override |
| Cluster pinning | `X-Cluster-ID` header via `providers.actual.extra_headers` in config.yaml |
| Model size guide | 0.5B Q4_K_M ~470MB (toy), 7-8B Q4_K_M ~4.5GB (daily driver), 32B ~20GB |

## Pitfalls

- Actual accepts reasoning `none/low/medium/high/max`; built-in clamps `xhigh→high`, `ultra→max`; old Hermes fallback: `agent.reasoning_overrides.<model>: high`.
- Default Hermes schemas ~26k tokens + system prompt ~9k; 32k context can overflow before turn and yield bare `data: [DONE]` / `Provider returned an empty stream with no finish_reason`. Use `-t file,web`, larger `n_ctx`, or >=64k context. Tracking #51448; related #65631 and #56516.
- download ID (`repo/QUANT`) differs from installed `models list` name; missing quantization yields 409 `ambiguous_model_download`.
- reasoning variants can put all output in `reasoning`; use generous `max_tokens`.
- never create custom provider named `actual`; remove stale `providers.actual.*` blocks.

## Verification

```bash
# Relay:
hermes chat -Q -q "Reply with exactly: ACTUAL_OK" --provider actual -m MODEL
# Local (small model — reduced toolset):
hermes chat -Q -q "Reply with exactly: LOCAL_OK" --provider actual -m MODEL -t file,web
# Provider status (local no-auth shows key_source=local-offline):
hermes status
```

Relay/local response contains exact marker; local status shows `key_source=local-offline`. For OpenCode integration see `references/opencode.md`.
