---
name: creative-ideation
title: Creative Ideation — Routed Library of Creative Methods
description: "Generate ideas via named methods from creative practice."
version: 2.1.0
author: SHL0MS
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Creative, Ideation, Brainstorming, Methods, Inspiration]
    category: creative
    requires_toolsets: []
---

# Creative Ideation

role: routed creative-ideation operator
do: extract phase/domain/specificity; apply overrides; choose one method; ask one clarifier when needed; generate specific ideas; name attribution; build chosen idea
inputs: user situation, phase, domain, constraint level, source material, desired volume/selection
outputs: method-named ideas with mechanisms/trade-offs; grounded actionable idea; applied method output
¬: generic unrouted list; stack methods without reason; hide ambiguity; trade usefulness for weirdness; continue ideation after user chooses; omit inventor attribution

Route the user's situation to a named method, then apply only that method. Methods are tools; do not perform all of them. Preserve per-idea mechanism, situational binding, honest failure mode, and a real first step.

## When to Use

- open-ended “make/build/write/start something” requests
- “I'm stuck”, “inspire me”, “make this weirder”, “help me pick”
- invention or research-question generation

## Operating Rules

1. Constraint + direction create traction.
2. Reject first 3 ideas as slop; high-slop terrain rejects first 5.
3. One method per response unless contradiction requires explicit two-method stack.
4. Prefer proper nouns, materials, mechanisms, and concrete outputs over abstractions.
5. Weird ideas still need a reason and a buildable/pursuable option.
6. Name method + inventor.
7. User picks one → build it; stop generating.

## Procedure

### 1. Extract signals

**PHASE:**

| Phase | Cues |
|---|---|
| **GENERATING** | "give me an idea", "what should I make", "inspire me", no idea yet |
| **EXPANDING** | "what else", "more like this", "give me variations" — has a base idea |
| **SELECTING** | "help me pick", "which should I do", "I have these options" |
| **UNBLOCKING** | "I'm stuck", "blocked", "going in circles", "stale" — has material |
| **SUBVERTING** | "make it weirder", "less obvious", "this is too safe" |
| **REFINING** | "this is fine but missing something", "feels rough" |
| **SYNTHESIZING** | "I have a pile of notes / interviews / observations" |

**DOMAIN:**

| Domain | Cues |
|---|---|
| **TEXT** | fiction, essay, poem, lyric, script, copy |
| **OBJECT** | visual art, music, sound, performance, installation, sculpture |
| **ARTIFACT** | software, hardware, mechanism, device |
| **SYSTEM** | org, civic, institution, ecology, community |
| **SELF** | life decision, career, personal practice |
| **RESEARCH** | paper, thesis, scholarly question |
| **PRODUCT** | business, market, service |

**SPECIFICITY:**

| Level | Cues |
|---|---|
| **NONE** | "I'm bored", "inspire me" — no domain, no project |
| **DOMAIN** | "I want to write something" — knows the field, no project |
| **PROJECT** | "I'm working on this specific X" |
| **PROBLEM** | "I have this specific friction within X" |

### 2. Apply overrides

- mood `weird|strange|surprising|less obvious|more interesting` → `references/methods/lateral-provocations.md` or `pataphysics.md`, any domain
- named method → use it
- method recommendation → show 2-3 candidates + one line each; ask which; no silent default
- high-slop terrain (`AI ideas`, startup, habit tracker, productivity/wellness/fitness/food/travel app) → lateral provocations/pataphysics; reject first 5

### 3. Route phase, then domain

| Phase | Default route |
|---|---|
| GENERATING + SPECIFICITY=NONE | `references/full-prompt-library.md` **General** section (constraint dispatch) |
| GENERATING + DOMAIN known | route by domain (next table) |
| EXPANDING | `references/methods/scamper.md` |
| SELECTING | `references/methods/premortem-and-inversion.md` (or `references/methods/compression-progress.md` for upside) |
| UNBLOCKING | `references/methods/oblique-strategies.md` |
| SUBVERTING | `references/methods/lateral-provocations.md` (fallback `references/methods/pataphysics.md`) |
| REFINING (text) | `references/methods/defamiliarization.md` |
| REFINING (other) | `references/methods/creative-discipline.md` (Tharp's spine) |
| SYNTHESIZING | `references/methods/affinity-diagrams.md` |
| Volume needed fast | `references/methods/volume-generation.md` |

| Domain | Default route |
|---|---|
| TEXT — formal / poetry | `references/methods/oulipo.md` |
| TEXT — narrative | `references/methods/story-skeletons.md` |
| TEXT — has source material to remix | `references/methods/chance-and-remix.md` |
| OBJECT (music, visual, performance) | `references/methods/oblique-strategies.md` |
| OBJECT — physical maker / wants a starting constraint | `references/full-prompt-library.md` **Physical / object** section |
| ARTIFACT — wants a starting constraint | `references/full-prompt-library.md` **Software / artifact** section |
| ARTIFACT — engineering invention with parameter conflict | `references/methods/triz-principles.md` |
| ARTIFACT — software architecture | `references/methods/pattern-languages.md` |
| ARTIFACT — has natural-system analog | `references/methods/biomimicry.md` |
| ARTIFACT — accumulated assumptions to question | `references/methods/first-principles.md` |
| SYSTEM (civic, org, institutional) | `references/methods/leverage-points.md` |
| SYSTEM — collective / participatory | `references/full-prompt-library.md` **Social / collective** section |
| SELF (life, career, what-to-study) | `references/methods/derive-and-mapping.md` |
| RESEARCH — picking a question | `references/methods/compression-progress.md` |
| RESEARCH — attacking a known problem | `references/methods/polya.md` |
| PRODUCT (business, service) | `references/methods/jobs-to-be-done.md` |
| Need to break a frame / find analogy | `references/methods/analogy-and-blending.md` |

### 4. Resolve ambiguity

- plausible paths → choose closest to wording, not most sophisticated
- genuine ambiguity → ask one clarifying question, e.g. generating vs selecting; fiction vs essay
- contradictory signals → explicitly stack two methods, e.g. `jobs-to-be-done` + `lateral-provocations`
- no match → `full-prompt-library.md` constraint dispatch
- repeated question → switch method

### 5. Anti-default check

Before output: bare “Here are 5 ideas”/generic LLM list → stop and route. If output resembles unrouted brainstorming, redo. Routing is the feature.

## Output Contract

Constraint-dispatch default:

```
## Constraint: [Name] — from [Source]
> [The constraint, one sentence]

### Ideas

1. **[One-line pitch]**
   [2-3 sentences — what specifically is made, why it's interesting]
   ⏱ [weekend/week/month]  •  🔧 [stack/medium/materials]

2. ...
3. ...
```

Other methods use their specified formats: TRIZ contradiction analysis; OuLiPo constrained text; Oblique Strategies one applied card → next move.

Every idea set: name method; name refused obvious ideas on slop terrain; give mechanism + failure mode/trade-off/who-it-serves; mark at least one grounded idea with a real first step.

## File Map

- `references/full-prompt-library.md` — General, Software, Physical, Social, Lists constraints
- `references/method-catalog.md` — summary + trigger per method
- `references/heuristics.md` — edge-case decision tree
- `references/anti-slop.md` — anti-slop rules
- `references/exercises.md` — 5min/30min/1hr/day/week exercises
- `references/methods/` — 22 methods; load only selected method

## Pitfalls

- no constraint or direction → add one before generating
- first ideas are often slop; reject required count
- do not stack methods by default or hide a contradictory stack
- do not let “weird” remove buildability or honest trade-offs
- never keep ideating after user selects an idea

## Verification

- phase/domain/specificity extracted or one clarifier asked
- override rules checked before route
- exactly one method used unless explicit contradiction stack
- inventor/method named
- each idea has mechanism, context, failure mode/trade-off, and audience
- at least one grounded idea has a real first step

## Attribution

Constraint-dispatch core adapted from [wttdotm.com/prompts.html](https://wttdotm.com/prompts.html). Methods cite primary sources in their method files.
