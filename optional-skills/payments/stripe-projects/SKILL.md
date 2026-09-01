---
name: stripe-projects
description: Provision SaaS services + sync creds via Stripe Projects.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Payments, Stripe, Projects, Provisioning, Infrastructure]
    related_skills: [stripe-link-cli, mpp-agent]
---

# Stripe Projects

role: per-project SaaS provisioning and credential-sync operator
do: install Stripe CLI/plugin; initialize project; catalog providers; confirm tier/charge; add/link service; verify; upgrade/remove/rotate; protect `.env` and vault
inputs: project root; provider/service; existing-resource/link intent; account/tier choice; credential rotation/removal request
outputs: provisioned provider resource; `.env` keys; encrypted vault record; provider list/status; upgrade/remove/rotation result
¬: provision without project/account/charge confirmation; commit `.env`; assume existing-resource import; claim removal destroys provider resource; leak vault/plaintext credentials; ignore billing

Wraps [Stripe Projects](https://projects.dev) CLI plugin for SaaS providers
(Neon, Twilio, Vercel, etc.), credential sync, and provider billing.
Gated `[linux, macos]` while payments tooling matures on Windows; Stripe CLI
itself is cross-platform.

## When to Use

- set up/provision a provider or create a database
- request Postgres, Redis, Twilio number, or similar project resource
- manage stack credentials, rotate a key, upgrade a plan
- discover available providers
- link an existing provider account with `stripe projects link <provider>`

Existing-resource import is provider-specific; many providers provision new
resources but do not import an existing database/Vercel project. Check support.

## Prerequisites

- Stripe CLI: Homebrew, Linux package manager, or https://docs.stripe.com/stripe-cli/install
- Stripe Projects plugin
- Stripe account; browser sign-in/account creation may occur during setup

macOS:

```
brew install stripe/stripe-cli/stripe
stripe plugin install projects
```

Linux: follow https://docs.stripe.com/stripe-cli/install, then:

```
stripe plugin install projects
```

## Procedure

All commands run through `terminal` from project root. CLI writes `.env` and
`.projects/vault/vault.json` relative to current working directory.

### 1. Initialize

```
cd <project-root>
stripe projects init
```

Creates `.projects/vault/vault.json` encrypted credential store and prepares the
project for providers.

### 2. Discover catalog

```
stripe projects catalog
```

Review provider availability across databases, hosting, auth, AI, analytics,
messaging, and other categories before choosing a service.

### 3. Add/link service

```
stripe projects add <provider>/<service>
```

Examples:

- `stripe projects add neon/postgres`
- `stripe projects add twilio/sms`
- `stripe projects add runloop/sandbox`

The CLI provisions in user's provider account, generates credentials, syncs
`.env`, and records the resource in the vault. Surface tier/pricing prompt and
obtain confirmation before a charge.

For an existing provider account, use `stripe projects link <provider>` after
checking existing-resource support.

### 4. Verify

```
stripe projects list
```

Confirm provider and expected `.env` keys; never print secret values.

### 5. Manage lifecycle

```
stripe projects upgrade <provider>     # tier change
stripe projects remove <provider>      # deprovision
stripe projects rotate <provider>      # rotate credentials
```

Confirm impact and billing before upgrade/remove. After remove, inspect the
provider dashboard for high-cost services; removal may leave paused/dormant
resources.

## Pitfalls

- `.env` writes are real project-root writes; check `.gitignore` first. Never commit plaintext credentials.
- `.projects/vault/vault.json` is per-project; same service in two projects creates separate resources and bills.
- `add`/`upgrade` tier prompts can charge; surface them before confirmation.
- Provider catalog changes; check `stripe projects catalog | grep <name>` before failing an add.
- Vault is encrypted but `.env` is plaintext; apply standard `.env` hygiene.
- `remove` does not always destroy the underlying resource; verify provider dashboard, especially managed databases.
- Stripe account/browser setup may block first run; do not claim provisioning until CLI reports success.

## Verification

```
stripe projects --version && stripe projects list
```

Exit code 0 inside initialized project means plugin is healthy. Also verify
target provider/resource, vault record, expected keys without values, `.gitignore`,
and charge/removal outcome.