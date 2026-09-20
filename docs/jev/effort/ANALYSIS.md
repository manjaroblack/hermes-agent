# Jev effort routing — source-grounded analysis
role: orchestrator; mode: read-only research + design; product implementation: none
source: PRD.md = authoritative root body; source text unmodified.
board: hermes-jev; project: p_7211c32b; canonical board.json binding verified.

## Source identity
fork: manjaroblack/hermes-agent; base local/runtime; SHA c5e435a8998090dd2cf4823283bff4aa8c2f47a0.
plugin: manjaroblack/hermes-typesafe; base main; SHA b3fe987015793feb9496ee2e16631646afa7348a.
method: git ls-remote + GitHub branches API + installed clean checkout HEAD; pivotal file bytes compared independently via GitHub contents API at immutable refs, all matched.
planning clones stale: /root/apps/hermes-agent@bc1dd90c477d5c6e67b891221d8f293d057c5266; /root/apps/hermes-typesafe@5940cd784b8979834fa652a85689427dbf212ccf on fix/ignore-host-dispatch-kwargs. Existing untracked docs preserved. Neither local HEAD is implementation base.
source paths below: relative to respective installed checkout, used READ-ONLY; workers fetch immutable refs into isolated staging clones.

## Findings affecting design
F1 host agent/plugin_model_switch.py:8-25 strips optional data; :103-107 rejects same model/provider before resolving. Both must change; formatter-only patch cannot deliver effort-only behavior.
F2 plugin __init__.py:89-114 AND route.py:97-114 enforce exact model/provider keys. Both validators must share compatible normalization; extra unknown keys discarded, not pool-killing.
F3 route.py:192-194 requires exact four answers; client.py:268-328 independently requires every requested answer, exact type, and choice in union criteria. Missing/malformed effort dies before evaluator. Scoped local optional-Choice response policy required through real runtime/client path; broad fail-open normalization forbidden.
F4 route.py:241-251 vetoes same target; harness.py:192-229 AND route.py:343-381 exclude first turns in cache-break mode. Product semantics must be implemented on both paths, not mocked helper alone.
F5 host runtime field is reasoning_config; agent.reasoning_effort in PRD describes config setting, not current Python attribute. agent_runtime_helpers.py:2218-2228 re-resolves destination config; :2101-2127 records reasoning_config + request_overrides in primary snapshot. Apply reviewed runtime effort after config resolution, before primary snapshot; preserve rollback.
F6 agent/transports/codex.py:615-623 merges request_overrides AFTER reasoning fields. Blind nested reasoning override bypasses canonical clamp and can leak across destinations. Prefer host-owned reasoning_config application inside switch transaction; test override interactions and outgoing request.
F7 provider vocabulary already exists: agent/reasoning_effort.py EFFORT_LADDER, codex_supported_efforts, XAI_GROK46_EFFORTS; providers/base.py:216-243 declares None/empty/nonempty semantics. Never turn unknown/unsupported plugin token into a stronger valid token.
F8 reviewed integration fixture currently pins old fork SHA b38c2858107e9d63f98c1d3a86bd00933fbd0661 in plugin .github/workflows/ci.yml and tests/test_reviewed_harness_integration.py. New plugin PR must bind BOTH to new independently GO-reviewed host head; no moving fixture.
F9 core switch helper exceeds 2k lines. Put new behavior in narrow topical sibling, only integration glue in existing giant helper; no opportunistic full-file refactor.

## Admission/operations
roster: hermes-coding=gpt-5.6-luna/openai-codex; hermes-review=grok-4.6/xai-oauth; hermes-security-audit=gpt-5.6-sol/openai-codex. hermes-coding-sol currently Sol, NOT Astra: quality escalation requires explicit same-card gpt-6-astra/openai-codex override and clearing it before Grok review.
dispatch: gateway active; dispatch_in_gateway=true; review_dispatch=true; auto_decompose=false.
notify: root actual row Discord chat 1487950227108397056; thread 1550785566923038752; chat_type=thread; notifier_profile=default; delivery_mode=notify+wake. Child inheritance must be reread.
CI: fork local/runtime unprotected; no active repository rulesets; required contexts empty. PR completion kernel rejects zero-required-check policy: fork card local-only contract intentionally, but full PR + independent exact-head review/local and applicable CI evidence still mandatory. No standing waiver inherited from PR17.
CI plugin main: required Python 3.10 offline plugin tests AND Python 3.12 offline plugin tests; use repository completion_contract manjaroblack/hermes-typesafe.
existing graph: prior Jev cards done; no open feature PR for effort; root has no children at intake. No duplicate implementation discovered.

## Risk/assumptions
risk: moderate-to-high control boundary (untrusted remote Choice → provider request; prompt cache; paid routing). Fresh security audit + fresh Grok design GO before code.
clarifications settled as product-derived defaults in DESIGN.md; no unresolved human choice required for design dispatch.
limits: source inspection != feature tests; no tests, inference calls, live config writes, install, merge, gateway restart, or product code edits performed.
