# Jev closed-pool reasoning effort — security design audit

role: independent security auditor
scope: design-only; immutable source inspection; no implementation|merge|install|live config|gateway restart|paid inference
verdict: SECURITY_GO
implementation_authorized: false
approved_command_set: []
revision_required: false

## Bound evidence

design: `/root/apps/hermes-agent/docs/jev/t_66770f64/DESIGN.md`; bytes=16586; sha256=`60a155494f393f577ac76655745b4fbe8e9ba7e9ba45a3258cbe32df0b1596c9`
prd: `/root/apps/hermes-agent/docs/jev/t_66770f64/PRD.md`; sha256=`2b55ea5bbf85fb37de3b3c8c025e8ed4096f08f3810e5a6dc5115a43587b0265`
analysis: `/root/apps/hermes-agent/docs/jev/t_66770f64/ANALYSIS.md`; sha256=`0ee4c60db29822cd52e91c27b89b7e049fb9fd6764096463a556c74f60e31f32`
fork pin: `manjaroblack/hermes-agent local/runtime@c5e435a8998090dd2cf4823283bff4aa8c2f47a0`
plugin pin: `manjaroblack/hermes-typesafe main@b3fe987015793feb9496ee2e16631646afa7348a`
source method: targeted `git ls-remote`; depth-1 immutable SHA fetches into `/tmp/hermes-jev-security-t_dda404b6/{fork,plugin}`; detached exact heads; clean porcelain status; no product checkout mutation
branch policy receipt: fork tip exact+unprotected+rulesets=[]; plugin tip exact+protected; strict required checks=`Python 3.10 offline plugin tests`,`Python 3.12 offline plugin tests`
toolchain: git 2.43.0; gh 2.45.0; Python 3.12.3; Linux 6.18.38-Unraid

## Severity / blocking rule

BLOCKER: public exposure|auth bypass|secret leak|firewall widening; any unresolved instance blocks.
HIGH: untrusted answer can escape closed effort pool, widen tolerant parsing, bypass cache permission, add uncontrolled paid calls, or mutate outside owner thread; blocks.
MEDIUM: rollback/config/override/cross-provider isolation can silently select wrong effort; blocks implementation/review if required evidence absent, not this hash-bound design when explicit control+test gate exists.
LOW: bounded operational/test weakness; non-blocking with named closure evidence.
INFO: provenance/coverage fact.

threshold: BLOCKER|HIGH design defect => SECURITY_NO_GO. Missing immutable evidence => block, never inferred GO.

## Findings

finding_count: 0 blocking; 4 residual implementation gates

R-01; severity=MEDIUM; class=scoped tolerant-answer boundary; status=controlled-by-design
impact: broad optional-answer tolerance could fail open guards/system_one or accept arbitrary extras.
evidence: plugin `client.py:268-328` currently requires exact answer set/type/Choice criteria; `runtime.py:296-352` preflights then submits; DESIGN.md:25-30 restricts tolerance to routing-local `optional_choice_questions=("reasoning_effort",)`, validates tuple before broker admission, preserves envelope/model/usage/size/core/extras strictness, and forbids retry/fourth RPC.
remediation_gate: implement exact requested-Choice allowlist through execute_sync->_submit->AsyncTypeSafeClient.system_one->_normalize_response; default empty everywhere else; never return raw response after normalization failure.

R-02; severity=MEDIUM; class=transport override/cost ceiling; status=controlled-by-design
impact: existing request override ordering can replace a validated effort, reintroduce `max|xhigh`, or leak stale reasoning across providers.
evidence: fork `agent/transports/codex.py:578-623` builds canonical reasoning then applies `request_overrides`; fork `agent/agent_runtime_helpers.py:2209-2243` merges overrides, re-resolves config, snapshots runtime; DESIGN.md:39-48 requires exact canonical/family validation, unsupported skip, host-owned reasoning_config inside transaction, no blind nested override, no bypass/leak, and no stale Jev effort on Flash.
remediation_gate: selected valid Jev effort must govern actual outgoing request; conflicting reasoning overrides sanitized/reconciled without disturbing unrelated overrides; rollback restores pre-switch nested state; cross-provider Grok->Luna->Flash capture proves no stale effort.

R-03; severity=MEDIUM; class=owner-thread transaction/same-identity; status=controlled-by-design
impact: current same-identity early return prevents effort-only update; careless bypass could mutate off owner thread, skip generation/cache permission, perform unnecessary destination lookup, or publish partial runtime state.
evidence: fork `agent/plugin_model_switch.py:63-130` validates generation/cache permission on owner path but rejects same identity at :103-107; `agent/turn_context.py:659-697` dispatches hooks then applies on owning turn path; `agent/agent_runtime_helpers.py:1818-1877,2177-2251` supplies rollback snapshot and transaction; DESIGN.md:32-48 requires first/later permission before effects, actual-delta no-op, stale/conflicting fail closed, same-identity current-runtime path, config resolution before effort, primary snapshot after effort, and rollback/frozen-prefix preservation.
remediation_gate: do not delete identity guard without replacing it with atomic actual-delta handling; fail-on-call probes must prove effort-only path performs no credential/network/cold capability lookup.

R-04; severity=LOW; class=delivery evidence; status=controlled-by-design
impact: formatter/helper mocks or stale host fixture can pass while installed plugin/runtime/host/request wire is broken; unprotected fork branch cannot supply required-check enforcement.
evidence: plugin `tests/test_reviewed_harness_integration.py:14,424-468` and `.github/workflows/ci.yml:36-66` pin old reviewed host `b38c2858107e9d63f98c1d3a86bd00933fbd0661`; current fork branch is unprotected with no rulesets; plugin main requires strict Python 3.10/3.12 contexts. DESIGN.md:50-62 requires new exact reviewed host head in test+CI fixture, installed wheel/two-home actual loader+turn/request composition, feature PR, applicable CI, and independent exact-head review.
remediation_gate: old fixture pin cannot remain; fork local-only completion contract still requires PR+exact-head independent review+applicable CI evidence; plugin requires both named checks green.

## Control assessment

D1 closed pool: PASS. Required identity remains fail-closed; unknown extra keys alone cannot poison routing; optional effort malformed per-label only disables that label; exact ceiling=`low|medium|high`; defaults exact members; lists detached; shared normalizer required. Evidence: plugin `__init__.py:89-114` and `route.py:97-114` are current duplicate exact-key blockers; DESIGN.md:13-23 resolves both.

D2 untrusted Choice: PASS. One deterministic union Choice in existing routing batch; empty union omits question; selected-label intersection/default/omit bounds remote output. Missing/wrong/outside optional answer alone tolerates omission; core route, extras, envelope, model, usage, size, depth remain strict. No SDK/tool schema or broker ABI expansion. Evidence: plugin `route.py:169-262`; `client.py:268-382`; `limits.py:315-356`; DESIGN.md:25-30.

D3 cost/cache eligibility: PASS. RPC count stays one for routing; combined route+rank+rerank remains <=`MAX_PRE_LLM_RPC=3`; no retry/fourth call. Both modes permit first turn under existing mismatch/confidence gates with `allow_cache_break=false`; only later cache-break mode also requires worth and emits true. Same-target valid effort reaches host; host decides actual delta. Both registered combined and standalone directive paths are in scope. Evidence: plugin `questions.py:43,91-105`; `route.py:302-385`; `harness.py:143-287`; DESIGN.md:32-37,50-55.

D4 host trust/transaction: PASS. Optional effort cannot invalidate a valid model switch; exact canonical+family checks are local/cached; unknown/unsupported skips instead of clamping into authority. First same-destination directive owns effort+permission; conflicts/stale generations fail closed. Host, not plugin, mutates reasoning_config inside existing snapshot/rollback transaction; prompt/history/tools frozen. Evidence: fork `agent/plugin_model_switch.py:8-41,63-130`; `agent/reasoning_effort.py:25,92-96,110-140`; `providers/base.py:216-241`; `agent/agent_runtime_helpers.py:1818-1877,2101-2128,2177-2251`; DESIGN.md:39-48.

public exposure/auth/session/secrets/firewall: no changed surface in design. No network listener, auth/session policy, credential payload, firewall rule, live config write, or plugin direct mutation authorized. Secret remains local scoped read; report contains no value. Therefore no mandatory BLOCKER class observed.

## Mandatory implementation test matrix

T01; D1; both validators consume one shared normalizer: old identity-only entries; unrelated extra key; valid effort; empty/missing/wrong-type/duplicate/unknown/nonmember-default per-label; valid siblings survive; input mutation after normalization cannot alter pool.
T02; D2; real synthetic SDK->client->_normalize_response->runtime->route: optional effort missing|wrong type|outside union|outside selected label => selected default or omission; no raw unvalidated response.
T03; D2 strict-negative: malformed/missing target,mismatch,worth,difficulty; arbitrary extra answer; wrong model; invalid usage; non-JSON/oversize/deep envelope => whole route failure. Ordinary system_one, guards, suggestions, execute_async remain strict with default-empty optional tuple.
T04; budget: exactly one routing RPC; all-empty effort union emits no question; registered combined total <=3; shared monotonic deadline never resets across route/rank/rerank; no retry/fourth RPC; late hook result cannot mutate host.
T05; projection: routing wire state exactly current `{user_message,current_label}`; no history/system prompt/agent object; both registered combined and standalone directive paths.
T06; modes: first_turn mode first=true/false; cache_break mode first=true/false; first turn false permission and no worth threshold; later true permission+worth; low mismatch|worth|confidence deny; nonboolean first-turn deny.
T07; host parser: absent|non-string|mixed-case|whitespace|unknown|family-unsupported effort; invalid effort retains valid identity switch; supported exact token reaches reasoning_config; no clamp-driven escalation or pool widening.
T08; composition: duplicate same destination first owns omission|effort|permission; later cannot fill/replace/widen; differing destinations reject all; stale generation and partial agent no mutation.
T09; atomicity: same-identity changed effort applies; equal effort no-op; first/later permission checked before effect; config re-resolution then selected effort then primary snapshot; injected failures at each rebuild/snapshot edge restore identity, reasoning_config, request_overrides, primary runtime, prompt, history, tools.
T10; override/leak: preexisting `request_overrides.reasoning`, top-level reasoning-effort variants, and provider `extra_body` cannot override selected allowed effort; unrelated overrides preserved; Grok high->medium, Luna medium->high, Grok->Luna->Flash actual next request capture has no stale Jev override.
T11; cold capability: family support lookup uses static/cached predicates only; fail-on-network/credential-resolution probes on same-identity effort path; unknown/cold capability skips effort and preserves model switch.
T12; end-to-end delivery: candidate installed wheel, two private homes, actual plugin loader, real client normalization/runtime broker path, registered combined hook, owner-thread host apply, actual next synthetic SDK request; only external SDK/network endpoint replaced; test+workflow fixture pinned to independently approved new host head.
T13; isolation: fresh subprocess unsets all HERMES_KANBAN_* overrides before imports; private HOME/HERMES_HOME/kanban DB/workspace assertions; no live credential/config reads; source-text assertions forbidden.
T14; delivery gates: host `scripts/run_tests.sh` focused+affected regressions; plugin Python 3.10+3.12 offline suite/build; exact base/head/PR/CI receipts; secret scan; no live/paid actions.

## Residual risk / limits

residual: feature not implemented; tests intentionally not runnable against absent change. SECURITY_GO approves only design sufficiency for independent design review; it does not prove implementation, wire behavior, live model capability, deployment safety, or merge readiness.
coverage: immutable code/source, branch policy, and static transaction/data-flow reviewed; no live config, credentials, plugin install, gateway, paid inference, provider call, firewall, or host mutation inspected.
rollback: report-only; source/live state unchanged. If implementation violates any D1-D4 invariant or T01-T14 evidence is missing, hold same card/PR; no waiver inferred.

## Verdict

SECURITY_GO bound only to DESIGN.md sha256=`60a155494f393f577ac76655745b4fbe8e9ba7e9ba45a3258cbe32df0b1596c9`, bytes=16586, fork pin=`c5e435a8998090dd2cf4823283bff4aa8c2f47a0`, plugin pin=`b3fe987015793feb9496ee2e16631646afa7348a`.
reason: design closes untrusted-Choice, tolerant-answer, cost/cache, duplicate/stale directive, atomic rollback, cold capability, projection, RPC budget, and installed-wire proof boundaries without adding public/auth/secret/firewall surface.
¬: implementation authorization; command authorization; merge; install; live config; restart; paid inference.
