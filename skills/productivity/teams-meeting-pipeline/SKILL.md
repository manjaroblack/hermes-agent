---
name: teams-meeting-pipeline
description: Teams meeting summaries, job replay, Graph subscriptions.
version: 1.1.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET]
  commands: [hermes]
metadata:
  hermes:
    tags: [Teams, Microsoft Graph, Meetings, Productivity, Operations]
    related_docs:
      - /docs/guides/microsoft-graph-app-registration
      - /docs/user-guide/messaging/teams-meetings
      - /docs/guides/operate-teams-meeting-pipeline
---

# Teams Meeting Pipeline

role: Teams meeting-pipeline operator
do: validate Graph config/token; inspect/replay/fetch jobs; manage subscriptions; diagnose delivery; schedule renewal
inputs: meeting/job ID or join URL, Graph env, subscription resource/URL/client state, delivery target
outputs: summaries/action items/transcripts, job/token/subscription status, replay/fetch results
¬: add per-meeting subscription by default; assume Graph subscriptions auto-renew; expose client secret/client state; declare pipeline healthy from one check; deliver without matching target config

All operator actions are `hermes teams-pipeline` through `terminal`; no model
tools are added. Works in any language. Triggers include meeting summary,
transcript/recording/action items, Graph subscriptions, status, replay, and
“meeting summary never arrived”.

## When to Use

- summarize Teams meeting, extract action items, pull notes/transcript
- inspect recent meetings, stored jobs, failures, or pipeline status
- replay failed/stale job; dry-run meeting/transcript resolution
- validate changed Microsoft Graph env/config
- create/renew/delete/inspect Graph webhooks
- automate subscription renewal

Multilingual examples: “summarize the Teams meeting”, “pipeline status”,
“replay job X”; Turkish: “Teams meeting özetle”, “action item çıkar”,
“toplantı notu”, “pipeline durumu”, “replay job”.

## Procedure

1. Verify Graph prerequisites; run `validate` + `token-health` before diagnosis.
2. Resolve job/meeting/subscription + requested delivery target.
3. Choose inspect, replay/fetch, subscribe/renew/delete command below.
4. Follow Decision Tree; when subscriptions exist, enforce scheduled renewal.
5. Verify job/subscription/delivery state without exposing secrets/client state.

## Prerequisites

Verify in `${HERMES_HOME:-~/.hermes}/.env`:

```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

Missing values → `/docs/guides/microsoft-graph-app-registration`: Azure AD app
registration + admin-consented Graph application permissions required.

## Command Reference

### Status/inspection (start here)

```bash
hermes teams-pipeline validate              # config snapshot — run first after any change
hermes teams-pipeline token-health          # Graph token status
hermes teams-pipeline token-health --force-refresh   # force a fresh token acquisition
hermes teams-pipeline list                  # recent meeting jobs
hermes teams-pipeline list --status failed  # only failed jobs
hermes teams-pipeline show <job-id>         # full detail of one job
hermes teams-pipeline subscriptions         # current Graph webhook subscriptions
```

### Replay/debug

```bash
hermes teams-pipeline run <job-id>          # replay a stored job (re-summarize, re-deliver)
hermes teams-pipeline fetch --meeting-id <id>   # dry-run: resolve meeting + transcript without persisting
hermes teams-pipeline fetch --join-web-url "<url>"   # dry-run by join URL
```

### Subscription management

```bash
hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllTranscripts \
  --notification-url https://<your-public-host>/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"

hermes teams-pipeline renew-subscription <sub-id> --expiration <iso-8601>
hermes teams-pipeline delete-subscription <sub-id>
hermes teams-pipeline maintain-subscriptions            # renew near-expiry ones
hermes teams-pipeline maintain-subscriptions --dry-run  # show what would be renewed
```

## Decision Tree

- summary absent today → `list --status failed`; `show <job-id>`; if no job,
  inspect `subscriptions` for expired webhook
- setup → `validate` → `token-health` → `subscriptions`; all pass → request
  test meeting and confirm fresh `list` row
- replay X → `list` → `run <job-id>`; repeat failure → `show`; dry-run artifact
  resolution with `fetch --meeting-id`
- add past meeting → normally no: pipeline is subscription-driven; use `fetch`
  for transcript then `run` after a job exists

## Pitfalls

### Critical Pitfall: 72-Hour Subscription Expiry

Microsoft Graph caps webhook subscriptions at 72 hours and does **not** renew
them. Without scheduled `maintain-subscriptions`, notifications silently stop
3 days after manual creation.

When ingestion stopped:

1. `hermes teams-pipeline subscriptions`; empty or every
   `expirationDateTime` past → cause confirmed.
2. Recreate with `subscribe` above.
3. Schedule renewal immediately via `hermes cron add`, systemd timer, or plain
   crontab. Runbook:
   `/docs/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production`.
   A 12-hour interval gives 6× headroom.

### Other Pitfalls

- transcript generation lags meeting end; `fetch --meeting-id` may be empty;
  wait 2–5 minutes or let webhook ingest
- summary succeeds but delivery absent → inspect
  `platforms.teams.extra.delivery_mode` and matching `incoming_webhook_url`,
  `chat_id`, or `team_id` + `channel_id`; writer reads config.yaml or `TEAMS_*`
- token health pass + Graph 401/403 → permissions changed without admin
  consent; Azure portal → “Grant admin consent” again

## Related Docs

- Azure registration: `/docs/guides/microsoft-graph-app-registration`
- setup: `/docs/user-guide/messaging/teams-meetings`
- operator renewal/troubleshooting/go-live:
  `/docs/guides/operate-teams-meeting-pipeline`
- listener: `/docs/user-guide/messaging/msgraph-webhook`

## Verification

- [ ] env present/private; `validate`, `token-health`, `subscriptions` all checked
- [ ] job ID exists before replay; `show`/`fetch` output inspected
- [ ] delivery mode and target config match
- [ ] subscription expiry captured; renewal automation scheduled at ≤12-hour cadence
- [ ] transient transcript delay distinguished from ingestion/delivery failure