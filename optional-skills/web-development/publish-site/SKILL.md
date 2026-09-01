---
name: publish-site
description: Versioned site deploys to GitHub/Cloudflare/Netlify Pages.
version: 1.0.0
author: Hermes Agent (Nous Research)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [publish, deploy, hosting, github-pages, cloudflare-pages, netlify, static-site, versioning, rollback, web-development]
    category: web-development
---

# Publish Site

role: versioned static-site deployment operator
do: build; preview for sign-off; commit/tag; deploy via provider ladder; curl-verify live URL; preserve rollback
inputs: site repo/output directory; authenticated provider CLI; deploy target/domain; rollback tag
outputs: signed-off deployment; version tag; verified URL; rollback command/tag
¬: deploy uncommitted files or source instead of build output; skip live HTTP verification; commit secrets; treat server-side runtime as static Pages work

Publish a user-built website, dashboard, or web app to user-owned infrastructure:
GitHub Pages by default; Cloudflare Pages or Netlify when needed. Preview,
version every deploy with a git tag, verify live HTTP, and keep rollback one command away.

Scope: static sites and SPA build output (plain HTML/CSS/JS or Vite/
Next-export/Astro `dist/`/`build/`). Server-side runtimes are out of scope;
use `cloudflare-temporary-deploy` for throwaway serverless deploys with zero account setup.

## When to Use

Load for:

- **put a site online** — "publish this", "host this somewhere", "give me a link I can share"
- **deploy generated output** — dashboard, report, portfolio, docs site, prototype
- **update** a published site (redeploy = new version)
- **roll back** a bad deploy to the previous version
- **pick a host** when the user only needs a URL

## Prerequisites

At least ONE authenticated provider CLI, checked in this order:

- **GitHub Pages (default):** `gh auth status` succeeds. Needs `git` too.
- **Cloudflare Pages:** `wrangler whoami` succeeds (or `CLOUDFLARE_API_TOKEN` is set). Install: `npm i -g wrangler` or use `npx wrangler@latest`.
- **Netlify (fallback):** `netlify status` succeeds. Install: `npm i -g netlify-cli`.

Plus: static output directory (site root or `dist/`/`build/`); build first when
needed and publish output, never source. For shared preview, optional
`cloudflared`; `python3 -m http.server` covers local-only preview.

## How to Run

Run commands with `terminal` from the site project directory. Five moves always apply:

1. Build → 2. Preview for sign-off → 3. Commit + tag (version-before-deploy) → 4. Deploy via the provider ladder → 5. Verify the live URL with `curl` and report it.

## Quick Reference

| Step | Command |
|---|---|
| Local preview | `python3 -m http.server 8080 --directory dist` |
| Shareable preview | `cloudflared tunnel --url http://localhost:8080` |
| Version a deploy | `git add -A && git commit -m "deploy: <what>" && git tag deploy-YYYYMMDD-HHMM` |
| GitHub Pages (branch mode) | `git subtree push --prefix dist origin gh-pages` |
| Enable Pages on repo | `gh api repos/{owner}/{repo}/pages -X POST -f 'source[branch]=gh-pages' -f 'source[path]=/'` |
| Cloudflare Pages | `npx wrangler@latest pages deploy dist --project-name <name>` |
| Netlify | `netlify deploy --prod --dir dist` |
| Rollback | `git checkout <previous-tag> -- . && redeploy` (or provider dashboard) |
| Verify live | `curl -sS -o /dev/null -w '%{http_code}' <url>` → expect `200` |

## Procedure

### 1. Build and preview locally

Build if needed (`npm run build`, etc.); identify output; serve it:

```bash
python3 -m http.server 8080 --directory dist
```

For another-machine sign-off, open a quick tunnel in a background `terminal` session:

```bash
cloudflared tunnel --url http://localhost:8080
```

Give the user the `https://*.trycloudflare.com` URL; get sign-off before deploy; kill the tunnel afterwards.

### 2. Version before deploy — no exceptions

Every deploy must come from a git commit: reproducible and rollback-ready.

```bash
git init 2>/dev/null; git add -A
git commit -m "deploy: <short description>"
git tag "deploy-$(date +%Y%m%d-%H%M)"
```

Existing repo → commit + tag. Never deploy uncommitted files.

### 3. Deploy — provider ladder

**Rung 1 — GitHub Pages** (default; free, no extra account if `gh` is authed):

```bash
gh repo create <name> --public --source . --push   # skip if repo exists
git subtree push --prefix dist origin gh-pages      # publish build output
gh api "repos/{owner}/<name>/pages" -X POST \
  -f 'source[branch]=gh-pages' -f 'source[path]=/'  # first time only
```

Site appears at `https://<owner>.github.io/<name>/`. If the site is the repo root (no build dir), push `main` and set Pages source to `main` instead of using subtree. For build-step projects that will redeploy often, prefer the official `actions/deploy-pages` workflow so pushes auto-publish.

**Rung 2 — Cloudflare Pages** (custom domain, redirects/headers, or Functions):

```bash
npx wrangler@latest pages deploy dist --project-name <name>
```

First run creates the project and prints `https://<name>.pages.dev`. Attach custom domains in the Cloudflare dashboard (Pages → project → Custom domains).

**Rung 3 — Netlify** (fallback or existing user host):

```bash
netlify deploy --prod --dir dist
```

`netlify deploy --dir dist` (without `--prod`) gives a draft URL for a second preview.

### 4. Rollback

Rollback = redeploy a previous tag; never hand-edit live output.

```bash
git checkout deploy-<previous> -- .   # or: git checkout deploy-<previous>; rebuild
# then rerun the same deploy command from step 3
```

Cloudflare Pages and Netlify retain deploy history with "Rollback to this deploy" when the CLI is unavailable.

### 5. Secrets and environment variables

- **NEVER commit secrets, API keys, or `.env` files** — they'd be public on Pages hosting. Check with `git status` before the first commit and keep `.env*` in `.gitignore`.
- Runtime env vars belong in the provider's dashboard: Cloudflare Pages → Settings → Environment variables; Netlify → Site settings → Environment variables. GitHub Pages is static-only — no server env; anything embedded in the bundle is public by definition. Warn the user if their build inlines a key.

## Pitfalls

- **SPA routes 404 on GitHub Pages.** Pages has no rewrite rules. Copy `index.html` to `404.html` in the output dir (`cp dist/index.html dist/404.html`) so client-side routing recovers. Cloudflare Pages and Netlify handle SPAs via `_redirects` (`/* /index.html 200`).
- **GitHub Pages build lag.** The site can take 1–10 minutes to appear after the first enable, and ~1 minute per subsequent push. Don't declare failure on the first 404 — poll `curl` a few times before investigating.
- **Case-sensitive paths.** Pages hosts are case-sensitive Linux; a site that worked on macOS/Windows can 404 on assets referenced as `Logo.PNG` but committed as `logo.png`. Grep the HTML for mismatched casing when an asset 404s.
- **Project-page base path.** `https://<owner>.github.io/<name>/` serves under `/<name>/` — absolute asset URLs like `/app.js` break. Use relative paths or set the build tool's base (`vite build --base=/<name>/`).
- **`wrangler` auth flow needs a browser.** `wrangler login` opens OAuth; in a headless session prefer `CLOUDFLARE_API_TOKEN` (user creates it at dash.cloudflare.com → API Tokens) and never echo the token into logs.
- **DNS propagation on custom domains.** New CNAMEs can take minutes to hours. Verify against the provider's default URL (`*.pages.dev`, `*.netlify.app`, `*.github.io`) first, then check the custom domain separately — don't conflate the two failures.
- **Deploying source instead of build output.** Publishing the repo root when the real site lives in `dist/` yields a directory listing or raw JSX. Always confirm the output dir contains an `index.html`.

## Verification

Do NOT report success from the deploy log alone. Before telling the user anything:

1. `curl -sS -o /dev/null -w '%{http_code}' <live-url>` returns `200` (retry over ~2 minutes for a first GitHub Pages deploy).
2. `curl -sS <live-url> | head -30` shows the expected `index.html` content — optionally confirm markup with `web_extract` on the live URL.
3. For SPAs, also curl one deep route (e.g. `/about`) and confirm it returns `200`, not `404`.
4. `git tag --list 'deploy-*'` shows the tag for this deploy.

Then report the live URL to the user, along with the deploy tag they can roll back to.
