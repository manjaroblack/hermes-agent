---
name: one-three-one-rule
description: "1-3-1 decision briefs: problem, three options, one pick."
platforms: [linux, macos, windows]
version: 1.0.0
author: Willard Moore
license: MIT
category: communication
metadata:
  hermes:
    tags: [communication, decision-making, proposals, trade-offs]
---

# 1-3-1 Communication Rule

role: decision-brief operator
do: frame one problem; compare exactly three viable options; recommend one; define done; plan execution; update if choice changes
inputs: decision, context/priorities, constraints, viable approaches, success criteria
outputs: one Problem sentence, Options A/B/C with pros/cons, one Recommendation, aligned DoD and Implementation Plan
¬: use for obvious one-answer questions; invent three fake options; hedge recommendation; mix two problems; leave DoD/plan tied to rejected choice

Use this format when a technical or organizational decision has multiple meaningful trade-offs and the user needs a forwardable recommendation.

## When to Use

- user explicitly asks for a `1-3-1`
- user asks for options/choices on architecture, tooling, or migration
- multiple viable approaches have meaningful trade-offs
- user needs a proposal for a team or stakeholder

Do not use for simple questions, debugging sessions, or decisions already made.

## Procedure

1. **Problem** — exactly one sentence; state desired outcome/core decision, not implementation details or tool names. If `and` is needed, split the decision.
2. **Options** — exactly A, B, C; each genuinely distinct and viable; include short description, pros, and cons.
3. **Recommendation** — select one option directly; justify from user context and priorities.
4. **Definition of Done** — concrete, verifiable success criteria for the recommendation.
5. **Implementation Plan** — executable steps, commands/tools where useful; revise DoD + plan if the user selects another option.

## Output Template

```markdown
**Problem:** [one sentence]

**Options:**
- **Option A:** [approach]
  Pros: [..]
  Cons: [..]
- **Option B:** [approach]
  Pros: [..]
  Cons: [..]
- **Option C:** [approach]
  Pros: [..]
  Cons: [..]

**Recommendation:** Option [A/B/C]. [contextual reason]

**Definition of Done:**
- [verifiable criterion]

**Implementation Plan:**
1. [step]
```

## Example

User: “Give me a 1-3-1 for adding retry logic to our API client.”

Agent:

**Problem:** API calls to external services fail intermittently under load and need graceful retry handling.

**Options:**

- **Option A: Exponential backoff with jitter in a shared utility.**
  Pros: Simple, understood, one implementation for all callers.
  Cons: No circuit breaking; callers block during retries.

- **Option B: Retry library (`tenacity`) as a decorator on each endpoint call.**
  Pros: Per-endpoint configuration; built-in circuit-breaker/rate-limit support.
  Cons: Adds a dependency; decorators can obscure control flow.

- **Option C: Queue-based async retry with dead-letter handling.**
  Pros: Non-blocking, replayable failures, scalable.
  Cons: Queue backend and significant complexity; overkill at low volume.

**Recommendation:** Option A. The volume does not justify queue infrastructure; shared exponential backoff + jitter covers the failure without a new dependency.

**Definition of Done:**
- `api_retry()` handles transient HTTP 429, 502, 503, 504.
- Up to 3 retries with exponential backoff and jitter.
- All external API calls use the utility.
- Each retry logs endpoint + attempt number.
- Tests cover exhaustion, immediate success, and transient-then-success.

**Implementation Plan:**
1. Create `utils/api_retry.py` with max retries, base delay, retryable statuses.
2. Add `random.uniform(0, base_delay)` jitter.
3. Wrap `api_client.py` calls.
4. Add HTTP-response tests for each retry case.
5. Run a stress test against a flaky endpoint mock.

## Pitfalls

- Exactly three options, not three cosmetic variants.
- One problem sentence; keep what separate from how.
- Recommendation is a decision, not a hedge.
- DoD and plan must follow the selected option.
- Revise Recommendation, DoD, and plan when the user chooses a different option.

## Verification

- one Problem sentence
- exactly Options A, B, C
- each option has pros + cons
- one Recommendation with rationale
- DoD and Implementation Plan align with it
- user-selected alternative updates all dependent sections
