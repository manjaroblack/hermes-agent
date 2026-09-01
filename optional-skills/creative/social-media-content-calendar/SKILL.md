---
name: social-media-content-calendar
description: "Plan multi-platform social campaigns: briefs to posting."
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Social-Media, Content-Calendar, Campaigns, Publishing]
    related_skills: [xurl, humanizer]
---

# Social Media Content Calendar

role: multi-platform campaign operator
do: define constraints; inventory verified claims/assets; schedule themes; adapt briefs; draft; review; publish approved posts or hand off; read back provider evidence
inputs: objective, audience, offer/message, platforms, date range, cadence, voice, claims, links, assets, approval authority
outputs: calendar, platform-specific briefs/copy/assets, review state, provider IDs or explicit handoff package
¬: copy-paste across platforms; publish draft/needs-review; claim publication without connector/provider ID; use unverified metrics/testimonials; skip rights/accessibility/disclosure checks

Own campaign structure, post briefs, channel adaptation, approvals, and publishing verification. Platform skills such as `xurl` own API commands. Without a connector, the verified endpoint is approved drafts for the user's scheduler: handed-off, not published.

## When to Use

- build a monthly/multi-platform calendar
- turn a launch into X, LinkedIn, Instagram, TikTok, or other channel posts
- draft/schedule a campaign
- repurpose articles/videos into social content

Do not use for a single one-off post; use the platform skill directly.

## Procedure

### 1. Define constraints

Record objective, audience, offer/message, platforms, dates, cadence, voice, mandatory/prohibited claims, links, tracking, localization, approval/publishing authority. Every proposed post needs a business purpose.

Done when every campaign constraint and publishing authority is explicit.

### 2. Inventory sources

Use `read_file` and `web_extract` for verified product facts, launches, articles, media, permitted testimonials, brand assets, and key dates. Mark claim owner + expiry; expose unsupported claims/missing assets.

Done when each usable claim/asset has provenance and unresolved gaps are listed.

### 3. Build themes and slots

Balance education, proof, product, community, event, behind-the-scenes, and conversation; align platform cadence + milestones; avoid duplicate cross-posts.

Done when every dated slot maps to a campaign theme, platform, and milestone.

### 4. Write briefs

For every post specify hook, core message, format, length, CTA, link, asset dimensions/content, accessibility text, tags/mentions, and success metric. Adapt per platform.

Done when every slot has a platform-specific, execution-ready brief.

### 5. Draft

Load `humanizer` for voice; use `image_generate` for needed visuals; preserve facts/shared identity and platform norms. Every slot gets copy + asset status.

Done when every slot has copy, asset status, and no unsupported claim.

### 6. Editorial and risk review

Check facts, tone, repetition, rights/permissions, accessibility, disclosures, link destination, dates, and crisis sensitivity. Mark `draft`, `needs review`, or `approved`; never publish draft.

Done when every slot has an explicit review state and only approved slots can advance.

### 7. Schedule or hand off

Present the approval batch. Publish/schedule approved slots via available skills (`xurl` for X). For unsupported platforms deliver copy, media, and timing to the user's scheduler and mark `handed-off`, not `published`. Read back scheduled time, account, preview, and provider post/job ID for actual publication.

Done when connected-platform slots have provider evidence and unsupported slots are handed-off, not published.

## Pitfalls

- identical copy on every platform
- low-value filler used to meet cadence
- unverified metrics, testimonials, or future claims
- confusing generated asset completion with publication
- calling a draft handoff “scheduled”

## Verification

- every post maps to a campaign objective + verified claim inventory
- no `draft`/`needs review` post was published
- published slots have provider-confirmed IDs
- unsupported slots are explicitly marked `handed-off`
- rights, permissions, accessibility, and disclosures checked before publishing
