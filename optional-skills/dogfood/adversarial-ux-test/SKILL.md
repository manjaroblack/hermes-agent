---
name: adversarial-ux-test
description: Roleplay a hostile user to find and triage UX pain points.
version: 1.0.0
author: Omni @ Comelse
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, ux, testing, adversarial, dogfood, personas, user-testing]
    related_skills: [dogfood]
---

# Adversarial UX Test

role: hostile-persona UX dogfood operator
do: define hardest persona; browse actual task; capture screenshots/console errors; write in-character rant; pragmatically filter; create bounded tickets; report evidence
inputs: staging/deployed URL, product docs, target audience, optional persona, core task, ticket destination
outputs: persona profile, in-character review, RED/YELLOW/WHITE/GREEN assessment, max 10 tickets, screenshots and links
¬: feature-tour instead of core task; mix personas; skip pragmatism filter; file raw persona noise; test local dev; exceed 10 tickets; claim UX issue without screenshot; use pre-seeded admin account when cold start is testable

Roleplay the worst-case user—technology-averse, impatient, and ready to return to their old method—then separate real friction from “I hate computers” noise. This is an angry automated mom test: most QA finds correctness bugs; this finds terminology, steps, onboarding, accessibility, cold-start, and paywall friction.

## When to Use

- `Run an adversarial UX test on [URL]`
- “Be a grumpy [persona] and test [app]”
- hostile user test on staging/deployed product

## Prerequisites

- staging/deployed app, not local dev
- browser tools, screenshot capture, console inspection
- project docs/known issues and ticket destination
- one persona + one core task per session

## Procedure

### 1. Define one specific persona

If absent, answer:

1. hardest user for the product (age, role, old method)
2. tech comfort (lower is better: WhatsApp-only/paper/email set up by spouse)
3. one job they need done, not feature list
4. abandonment trigger (clicks, jargon, slowness, confusion)
5. frustrated voice (blunt, sweary, dismissive, sighing)

Example: **“Big Mick” McAllister**, 58-year-old S&C coach, WhatsApp only, paper notebook, must log 25 players, hates small text/jargon/passwords, quits after 10 seconds. A vague “user who dislikes the app” is invalid; persona must hold for ~20 minutes.

### 2. Browse in character

1. Read docs for context/URLs.
2. Fully inhabit limitations, goals, and frustrations.
3. Navigate with browser tools.
4. Attempt only the actual core task first:
   - steps/clicks/screens
   - confusion/lost points/anger
   - what causes abandonment
5. Test first impression, core workflow, error recovery, readability/contrast/density, speed, terminology, navigation.
6. Register a new user when possible; test cold start/empty states and expired/paywall accounts where relevant.
7. Capture a screenshot for every complaint and check browser console JS errors on every page.
8. Count clicks; >5 for the one task is almost always RED.

### 3. Write the rant (still in character)

```
[PERSONA NAME]'s Review of [PRODUCT]

Overall: [Would they keep using it? Yes/No/Maybe with conditions]

THE GOOD (grudging admission):
- [things even they have to admit work]

THE BAD (legitimate UX issues):
- [real problems that would stop them from using the product]

THE UGLY (showstoppers):
- [things that would make them uninstall/cancel immediately]

SPECIFIC COMPLAINTS:
1. [Page/feature]: "[quote in persona voice]" — [what happened, expected]
2. ...

VERDICT: "[one-line persona quote summarizing their experience]"
```

### 4. Apply mandatory pragmatism filter

Break character. Classify every complaint:

| Class | Meaning | Action |
|---|---|---|
| **RED** | any competent user has it; accessibility; genuine workflow blocker | fix/ticket |
| **YELLOW** | valid, mainly extreme user/low priority | one catch-all ticket |
| **WHITE** | “I hate computers”/paper-only resistance; complexity would hurt 80% | report only |
| **GREEN** | feature/onboarding opportunity hidden in complaint | consider/ticket |

Criteria: same for a busy competent 35-year-old? RED; font/contrast/click target? RED; “work like paper”? WHITE; real inefficiency? YELLOW/RED; added complexity for satisfied 80%? WHITE; missing aha/onboarding? GREEN. Never ship raw persona complaints.

### 5. Create tickets

Only RED/GREEN: actionable title, verbatim quote, objective UX issue, suggested fix, `ux-review` label. YELLOW: one catch-all. WHITE: report only. Max 10 tickets; include links.

### 6. Report

1. persona rant
2. filtered assessment
3. created tickets + links
4. screenshots of key issues
5. console errors and known-issue cross-check

## Persona Starters

| Product Type | Persona | Age | Key Trait |
|-------------|---------|-----|-----------|
| CRM | Retirement home director | 68 | Filing cabinet is the current CRM |
| Photography SaaS | Rural wedding photographer | 62 | Books clients by phone, invoices on paper |
| AI/ML Tool | Department store buyer | 55 | Burned by 3 failed tech startups |
| Fitness App | Old-school gym coach | 58 | Paper notebook, thick fingers, bad eyes |
| Accounting | Family bakery owner | 64 | Shoebox of receipts, hates subscriptions |
| E-commerce | Market stall vendor | 60 | Cash only, smartphone is for calls |
| Healthcare | Senior GP | 63 | Dictates notes, nurse handles the computer |
| Education | Veteran teacher | 57 | Chalk and talk, worksheets in ring binders |

## Pitfalls

- stay in character only through Steps 2-3; step out for filter
- one persona/session/report; do not mix perspectives
- test core workflow before settings
- zero WHITE items can be a useful signal: real UX problems may dominate
- check known issues after testing; known-but-unfelt bugs are damning
- test expired subscription/paywall flows; users must not lose data
- persona with zero complaints is too tech-savvy; make constraints concrete

## Verification

- staging/deployed target and one persona/core task recorded
- every complaint has screenshot; every page console checked
- rant is in persona voice; assessment is out of character
- all complaints classified; mandatory filter completed
- ticket count <=10; only RED/GREEN individually ticketed, YELLOW grouped, WHITE report-only
- report includes links/evidence and known-issue comparison

## Preserved Source Examples

### Original example 1

```
"Run an adversarial UX test on [URL]"
"Be a grumpy [persona type] and test [app name]"
"Do an asshole user test on my staging site"
```
