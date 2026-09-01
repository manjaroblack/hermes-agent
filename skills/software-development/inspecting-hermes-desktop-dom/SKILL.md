---
name: inspecting-hermes-desktop-dom
description: "Read the live Hermes desktop DOM/CSS over CDP."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, electron, cdp, dom, ui-verification, self-inspection]
    related_skills: [node-inspect-debugger, systematic-debugging, dogfood]
---

# Inspecting the Live Hermes Desktop DOM

role: live Hermes desktop DOM/CSS fact checker
do: probe CDP; select main renderer; inspect DOM/styles/geometry/rules/console; verify running UI changes; use isolated instance when needed
inputs: running `hgui`/`npm run dev`, CDP port/env, selector/design-token question
outputs: computed values, matching selectors, geometry, console errors, rendered-state evidence
¬: infer live state from `.tsx`; attach to wrong target; dump whole DOM; kill/relaunch user's app; judge aesthetics from CDP facts

When developing `apps/desktop` against a running app, inspect the rendered DOM,
computed styles, winning CSS rules, geometry, and console instead of guessing from
source. CDP answers factual questions; screenshots/user eyes answer visual quality.

## When to Use

- verify a UI change took effect in the running app
- find the winning rule for “why is this element still X?”
- locate stable selectors before editing
- read real design-token values
- inspect renderer console errors

Don't use for perf/heap work (`node-inspect-debugger`, `debugging-hermes-desktop`)
or “does this look right?” aesthetics.

## Prerequisites

- dev-server run exposing CDP on `127.0.0.1:9222`
- `curl`, Node.js, and `apps/desktop/scripts/eval.mjs` for probes
- optional `HERMES_DESKTOP_CDP_PORT`, isolated `HERMES_HOME`, user-data dir

## Procedure

### 1. Check the port

Dev-server runs open CDP automatically. It is closed by
`apps/desktop/electron/dev-cdp.ts` for packaged builds and for unpackaged
`electron .` without `HERMES_DESKTOP_DEV_SERVER` (dist smoke test). Move port with
`HERMES_DESKTOP_CDP_PORT=9333`; disable with `=off`.

```bash
curl -s --max-time 3 http://127.0.0.1:${HERMES_DESKTOP_CDP_PORT:-9222}/json/version
```

Empty → no port; do not silently guess another. Never relaunch user's app to get
one; use an isolated instance.

### 2. Read DOM with the one-liner

```bash
cd apps/desktop
node scripts/eval.mjs "document.querySelectorAll('[data-slot]').length"
```

For multi-step/promise-aware work:

```js
import { CDP, SELECTORS } from './scripts/perf/lib/cdp.mjs'

const cdp = await CDP.connect({ port: 9222, match: '5174' })
const out = await cdp.eval(`JSON.stringify({
  radius: getComputedStyle(document.documentElement).getPropertyValue('--radius-scalar').trim(),
  composer: !!document.querySelector('[data-slot="composer-rich-input"]')
})`)
cdp.close()
```

Prefer stable `SELECTORS`/`data-slot` hooks (composer, thread viewport, assistant
message, turn pair, profile rail); they move with components.

### 3. Diagnose the winning rule

```js
const el = document.querySelector('[data-slot="aui_assistant-message-root"] a')
JSON.stringify({
  ownClasses: el.className,
  weight: getComputedStyle(el).fontWeight,
  parents: (() => {
    const out = []
    let n = el
    while ((n = n.parentElement) && out.length < 6) out.push(n.className)
    return out
  })()
})
```

No own class + unexpected value → inherited ancestor rule. Plugin typography such
as `@tailwindcss/typography` `prose a { font-weight: 500 }` may beat a utility;
override shared class, not every call site.

### 4. Launch an isolated instance when needed

```bash
cd apps/desktop
HERMES_HOME=/tmp/cdp-probe-home \
HERMES_DESKTOP_DEV_SERVER=http://127.0.0.1:5174 \
HERMES_DESKTOP_CDP_PORT=9333 \
  npx electron . --user-data-dir=/tmp/cdp-probe-userdata
```

Separate `--user-data-dir` avoids Electron's single-instance lock; separate
`HERMES_HOME` avoids real sessions; non-default port avoids collision. Background
it and kill it when done. `npm run perf:serve` provides a temp-HERMES_HOME perf
variant. A throwaway backend may exit with `ECONNREFUSED`; renderer DOM remains
readable briefly. `DevTools listening on ws://127.0.0.1:<port>/…` proves binding.

## Pitfalls

- never kill user's dev server/app; Chromium socket loss can create misleading
  `ERR_NETWORK_CHANGED`
- poll a just-launched app; one probe can race startup
- never dump `outerHTML`/whole DOM; project to small JSON inside eval
- always pass `match` to `CDP.connect` or attach to pet/quick-entry/devtools target
- `cdp.eval` returns value; raw `Runtime.evaluate` double-nests `.result.result.value`
- `import.meta.env.DEV` is true under Vite dev; stale contrary note is in
  `apps/desktop/scripts/profile-typing-lag.md`

## Verification

- CDP `/json/version` responds on expected port or isolated port
- `CDP.connect` match selects main renderer
- selectors resolve expected nodes; computed style/geometry/rule is reported
- console output checked when investigating errors
- isolated probe uses separate `HERMES_HOME` + user-data dir and is terminated
- aesthetic judgment deferred to screenshot/user
