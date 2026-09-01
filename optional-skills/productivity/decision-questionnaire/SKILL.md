---
name: decision-questionnaire
description: "Turn an unanswerable decision into a questionnaire doc."
version: 1.0.0
author: "Matt Pocock (mattpocock/skills, to-questionnaire) + Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [questionnaire, decision, async, stakeholder, discovery, communication]
    related_skills: [meeting-action-items, document-to-action-items]
---

# Decision Questionnaire

role: decision-gap interviewer + questionnaire author
do: inspect discoverable facts; ask only recipient/outcome questions; draft prioritized questionnaire; write/verify file
inputs: decision topic; recipient role/expertise; needed decisions/facts
outputs: `decision-questionnaire-<slug>.md`; answer stubs; covered outcomes
¬: ask subject-matter questions the user cannot answer; use when answer is discoverable; write compound questions; invent recipient facts

Turns an unanswerable decision into a Markdown questionnaire for async response
or a meeting. Recipient knowledge fills the user's information gap.

Ported from mattpocock/skills' MIT-licensed `to-questionnaire` skill.

## When to Use

- A decision blocks on facts or judgment held by someone else (a domain
  expert, a stakeholder, a vendor contact, ops)
- The user says "I need to ask X about this" or keeps deferring a decision
  pending someone else's input
- Preparing for a meeting where specific answers must come back

Do NOT use when the answer is discoverable in the environment (codebase, docs,
web); find it first.

## Core Principle: Interview the Send, Not the Subject

The user cannot answer subject-matter questions; they can ALWAYS answer about
the send. Ask only two short exchanges:

1. **Who is it going to?** Role, expertise, relationship. This fixes tone and
   required context; done when recipient knowledge absent from the user is known.
2. **What do you need back?** Decisions/facts the user cannot resolve alone;
   done when the user's required outcomes are concrete.

Then **write the questionnaire**: target the recipient/user knowledge gap and
follow the structure below. Write `decision-questionnaire-<slug>.md` in the
current directory (slug from topic), report its absolute path, and ensure every
step-2 item has a question.

## Document Structure

Frame a **discovery questionnaire**: user lacks context; recipient holds it.
Order most-important-first (async may allow one pass). Group more than a handful
under `##` theme headings.

Template:

```markdown
# <Questionnaire title>

**Purpose:** why this questionnaire exists and the decision riding on it.

**From:** <the user> · **To:** <the recipient> ·
**How your answers will be used:** <where they go>

## Context

One paragraph orienting a recipient who wasn't in the user's head. Enough
to answer well, not a page.

## How to answer

Deadline and rough effort. Partial answers and "I don't know" are useful:
flag anything you're unsure of rather than skipping it.

## <Theme heading>

### <One question — a single idea, never compound>

_Why this matters: <one line, only where the question could be misread or
invite a throwaway answer>._

>

## Anything else?

A closing catch-all: anything we didn't ask that we should know?
```

Put an answer stub (`>`) directly beneath every question.

## Pitfalls

1. **Grilling the user about the subject.** User cannot answer; interview the send.
2. **Compound questions.** One idea each; split "and/or" questions.
3. **Burying the critical question.** Most-important-first; async recipients fade.
4. **Context dump.** One orienting paragraph, not the full history.
5. **Missing "why this matters" on ambiguity.** Add it to prevent throwaway
   answers; omit it when the question is unambiguous.

## Verification

- [ ] Recipient's role/knowledge and the needed outcomes captured in two
      exchanges before drafting
- [ ] Every step-2 item covered by at least one question
- [ ] Questions single-idea, most-important-first, answer stubs present
- [ ] File written and absolute path reported to the user
