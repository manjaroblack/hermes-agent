---
sidebar_position: 6
title: "Plugin Hook Fork Contract"
description: "Host-owned model switches, exact tool policy, and skill roster snapshots for plugins"
---

# Plugin Hook Fork Contract

Hermes keeps the generic fork surfaces small and host-owned. Plugins receive data and return bounded directives; they never receive an agent, client, credential, filesystem loader, or model SDK handle.

## Capability markers

`PluginContext.capabilities` is an immutable `frozenset` of feature markers. The current markers are:

- `pre_llm_call.model_switch.v1`
- `pre_tool_call.decision.v1`
- `skills.snapshot.v1`

A plugin must treat an absent marker as unsupported. Markers are per feature, not a global plugin API version.

## Pre-LLM model switches

A `pre_llm_call` callback may return data such as:

```python
{"model_switch": {
    "model": "configured-model",
    "provider": "configured-provider",
    "allow_cache_break": False,
}}
```

The callback returns data only. Hermes validates the result, resolves the configured route through the existing model-switch pipeline, and applies it once on the owning turn thread before the next provider request. Conflicting destinations, stale or timed-out results, unsupported routes, and failed switches are ignored; the existing switch engine restores its complete prior runtime on failure.

On the first real conversation turn, `allow_cache_break` must be `False`. A later turn must explicitly set it to `True`. The plugin route preserves the frozen system prompt, tool schemas, and past message bytes; it does not rebuild prompt state or persist configuration. A `context` field remains the normal ephemeral user-context return and is not a model-switch command.

## Exact pre-tool policy

`register_hook("pre_tool_call", callback, phase="normal"|"decision")` adds an optional decision phase. Without a decision-phase callback, legacy first-directive behavior remains unchanged.

When the decision phase is present, request and execution middleware finish first. Normal callbacks run in registration order and may compose `{"action": "modify", "args": {...}}`; the first normal block or approve stops the normal chain. Decision callbacks then see a detached immutable view of the final JSON arguments and may return only `None`, `{"action": "block", "message": "..."}`, or `{"action": "approve"}`. The first decision directive wins. Exceptions, timeouts, malformed values, invalid arguments, and missing policy identity fail closed with static block messages.

An approval is resolved once through the native approval transport. Its local dispatch binding includes the tool name, registration generation, a fresh per-execution nonce, and a canonical argument digest. Native `once`/`session`/`always` choices remain governed by the normal approval owner policy and may retain their documented scope; the fresh nonce makes each resulting dispatch authorization a distinct host execution. Reused model call IDs do not establish identity. Hermes compares the binding again immediately before the exactly-once handler dispatch, after guardrails; a changed call is blocked rather than re-run unchecked.

## Skill roster snapshots

`ctx.skills_snapshot()` is an in-memory read of the published `SkillRosterSnapshot`, scoped to the invoking session and Hermes home. Calls without an invoking session identity fail closed with `None`. It contains only a generation and immutable `(name, description, excerpt)` descriptors. It contains no paths, manifests, secrets, linked support files, callables, or lazy loaders.

The host builds a bounded snapshot at session initialization and on supported skill/plugin changes or an explicit refresh. Invalidation removes the old generation immediately; rebuilding happens outside hook deadlines. Out-of-band edits are visible only after an explicit refresh. Calling `skills_snapshot()` from a hook performs no filesystem or network work and never changes the frozen conversation prompt. Publication is bounded to 512 descriptors, 128 UTF-8 bytes per name, 512 bytes per description, 700 characters/2800 UTF-8 bytes per excerpt, 32 KiB per `SKILL.md`, 2 MiB of raw skill reads, and 1 MiB of serialized metadata. Over-budget or ambiguous publications are unavailable rather than partial.
