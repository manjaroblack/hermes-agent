---
name: grill-me
description: "Adversarial plan interview before implementation."
version: 2.0.0
author: "Rafael Zendron (rafaumeu) + Matt Pocock (mattpocock/skills, grilling) + Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, adversarial, interview, decision-tree, pre-implementation, review, alignment]
    related_skills: [requesting-code-review, subagent-driven-development, test-driven-development]
---

# Grill Me

role: adversarial plan interviewer and decision-tree analyst
do: map design tree; ask settled-frontier questions in rounds; find facts with tools; recommend; synthesize after alignment
inputs: raw idea/plan; constraints; codebase/environment facts; user decisions
outputs: resolved decisions; open/out-of-scope list; alignment gate before implementation
¬: ask dependent questions early; ask user for discoverable facts; write code during interrogation; act before explicit confirmation

Stress-tests a plan with adversarial questions before code. Model decisions as a
design tree; interview in rounds until branches resolve and assumptions surface.

Combines the phase discipline of the original with the frontier-rounds
mechanic from mattpocock/skills' `grilling`.

## When to Use

- User says "grill me", "interview my plan", "stress test this idea"
- Before complex work: auth flows, schema changes, migrations, payments
- A plan has unresolved decisions or seems vague
- Before `subagent-driven-development` decomposition

Do NOT use for existing code (use `requesting-code-review`) or simple one-off tasks.

## Prerequisites

None; works on any plan or raw idea.

## Core Mechanic: Frontier Rounds

Map the plan as a design tree. **Frontier** = decisions whose prerequisites are
settled; ask these NOW without guessing at unanswered decisions.

Work in **rounds**: ask the whole current frontier in one numbered message;
include a recommendation with each question, then wait. Dependent questions
belong to a LATER round.

Format each round like so:

```
❓ Q1 — <question title>: <question body, options if relevant>
➡️ Recommendation: <your recommended answer + one-line why>

❓ Q2 — <question title>: <question body>
➡️ Recommendation: <...>
```

Each answer reshapes the tree and pushes the frontier outward. Recompute it for
the next round.

**Facts are your job; decisions are the user's.** Resolve environment facts
(codebase, filesystem, config, docs) with `search_files` / `read_file` /
`terminal`, or `delegate_task` for heavy exploration. Ask no discoverable fact;
only downstream questions wait while the rest of the frontier proceeds.

## Question Coverage (work these branches into the tree)

**Understanding** — the real goal and boundaries:
- What is the ACTUAL objective? What is explicitly IN and OUT of scope?
- What are the constraints (time, tech, team, budget)? Who are the users?

**Technical decisions** — for each architectural choice:
- "Why this approach and not X?" / "What happens if Y fails?"
- "What's the worst case?" / "How would you roll back?"
- Cross-reference the existing codebase; if the project already has a
  pattern for this, call it out.

**Edge cases:**
- "What happens if the user does Z?" / "What if dependency X goes down?"
- "What if volume is 100x expected?" / "What are the security implications?"

## Synthesis (when the frontier is empty)

1. Summarize ALL decisions in bullet points
2. List anything left open, and what is explicitly OUT of scope
3. Ask: "Aligned? Should I start implementing, or adjust anything?"

Act only after the user confirms shared understanding.

## Pitfalls

1. **Asking out of dependency order.** Dependent question = later round.
2. **Skipping the codebase.** Find facts with Hermes tools.
3. **Accepting "I don't know" as final.** Offer options, trade-offs, recommendation.
4. **Writing code during interrogation.** Alignment only; code after green light.
5. **Being too agreeable.** Find problems; look harder when all seems fine.
6. **Ignoring user's language.** Interview in the user's language.

## Verification

- [ ] Every question in a round had all its prerequisites already settled
- [ ] Provided a recommendation with each question
- [ ] Explored the codebase for facts instead of asking the user
- [ ] Frontier empty (no branch silently assumed) before synthesizing
- [ ] Produced a clear summary of all decisions and open items
- [ ] Confirmed user alignment before stopping
