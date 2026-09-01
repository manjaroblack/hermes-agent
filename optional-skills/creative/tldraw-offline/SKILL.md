---
name: tldraw-offline
description: Drive and script tldraw offline canvases with an agent.
version: 1.0.0
author: Teknium + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tldraw, canvas, whiteboard, document-script, diagramming]
    category: creative
    related_skills: []
---

# tldraw offline

role: tldraw offline canvas scripting operator
do: confirm app/document/API; reread port/token each call; use `/exec` for live edits; edit script workspace for durable behavior; validate shapes/listeners; verify state and screenshots
inputs: open tldraw document, canvas goal, optional durable script/interactive behavior, local `server.json`
outputs: edited canvas, idempotent `script/main.js`, self-running `.tldraw`, shape/binding/screenshot evidence
¬: GUI/computer-use drawing; direct `.tldraw` hand-edit; reuse exported token; log token; hardcode port; pass PNG reference to script; leak listeners/intervals; claim script applied without status

Work with the tldraw offline desktop app (`offline.tldraw.com`). It exposes a local HTTP API (default `localhost:7236`) driven through the terminal. Use document scripts—JavaScript embedded in a `.tldraw` file—for durable behavior. Keep the app open. The agent does not use GUI clicking or hand-edit the archive directly.

## When to Use

- build/modify an open offline tldraw canvas: diagram, wireframe, layout
- add reactive shapes, buttons, animation, or connection logic that survives reload

Do not hand-place shapes to imitate a drawing; script the canvas instead.

## Prerequisites

- tldraw offline installed/running with a document open: https://github.com/tldraw/tldraw-offline/releases/latest
- app Agent Skills installed via `Develop → Install Agent Skills` if using its companion guidance
- local API `server.json`: Linux `~/.config/tldraw/`, macOS `~/Library/Application Support/tldraw/`, Windows `%APPDATA%\tldraw\`; fields `port` (default `7236`), bearer `token`, `pid`, `startedAt`
- every request except `GET /` needs `Authorization: Bearer ***` (redacted in this document)
- clean quit removes `server.json`; present + dead port means unclean/not running
- reread port and token at the top of **every** shell call; shell exports do not persist
- no account/network needed for local editing

## How to Run

Choose by persistence: use `/exec` for one-off live edits; use the document's `/script-workspace` for behavior that must survive reload. Keep the app and target document open, then reread `server.json`, resolve the document, execute one path, and verify live state.

## Quick Reference

| Goal | Path | Completion evidence |
|---|---|---|
| One-off layout/edit | `POST /api/doc/:id/exec` | queried shapes/bindings + screenshot |
| Durable behavior | `POST /api/doc/:id/script-workspace` | `script-status` applied + matching digests |
| Discover document | `/api/search` with `api.getFocusedDoc()`/`api.getDocs()` | explicit target document ID |
| Validate snapshot props | `node scripts/validate_shapes.mjs` | `3/3` |

## Procedure

### 1. Resolve API and document

At each terminal call read `server.json` inline:

```bash
PORT=$(jq -r .port <server.json)
TOKEN=$(jq -r .token <server.json>)
```

Use `api.getFocusedDoc()` or `api.getDocs()`; name the target explicitly if several docs are open.

### 2. One-off edits via `/exec`

Use for layout, generation, or cleanup; live edit, not durable script:

```bash
BASE=http://localhost:7236
TOKEN=$(python -c "import json;print(json.load(open('$HOME/.config/tldraw/server.json'))['token'])")
# find the focused document id
DOC=$(curl -s "$BASE/api/search" -X POST -H 'content-type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"code":"return (await api.getFocusedDoc()).id"}' | python -c "import sys,json;print(json.load(sys.stdin)['result'])")
# run code with the live `editor` + `helpers` in scope
curl -s "$BASE/api/doc/$DOC/exec" -X POST -H 'content-type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"code":"const {createShapeId,toRichText}=await import(\"tldraw\"); editor.createShape({id:createShapeId(),type:\"geo\",x:0,y:0,props:{geo:\"rectangle\",w:200,h:100,color:\"blue\",fill:\"solid\",richText:toRichText(\"hello\")}}); return editor.getCurrentPageShapes().length"}'
```

### 3. Durable behavior via script workspace

Use for reload-surviving logic:

```bash
# get the live script file path for the doc
curl -s "$BASE/api/doc/$DOC/script-workspace" -X POST \
  -H "Authorization: Bearer $TOKEN"          # -> result.mainJsPath, result.isDefaultScript
# edit result.mainJsPath with read_file / patch / write_file (see scripts/main.js)
# then confirm the watcher applied it:
curl -s "$BASE/api/doc/$DOC/script-status" -H "Authorization: Bearer $TOKEN"
```

Template: `scripts/main.js`.

### 4. Script contract

```js
import { createShapeId, toRichText } from 'tldraw'   // primitives: import, not globals

export default function ({ editor, helpers, signal }) {
  editor.run(() => {                                 // batch = one undo step
    helpers.createShapeIfMissing({                   // idempotent furniture
      id: createShapeId('node-1'), type: 'geo', x: 0, y: 0,
      props: { geo: 'rectangle', w: 200, h: 100, richText: toRichText('hi') },
    })
  })

  const stop = editor.store.listen(() => { /* react */ })  // fires the tick AFTER a commit
  signal.addEventListener('abort', () => stop())           // REQUIRED cleanup on rerun/close
}
```

- `ctx.editor`: `createShape`, `updateShape`, `deleteShapes`, `getCurrentPageShapes`, `getShape`, `getBindingsFromShape`, `zoomToFit`, `on('tick'|'event', fn)`, `run(fn, { history: 'ignore' })`
- `ctx.helpers`: `createShapeIfMissing`, `createShapesIfMissing`, `createArrowBetweenShapes(from, to, { arrowheadEnd })`, `translateShapes`, `onShapeTranslate(id, fn, { signal })`, `richTextToPlainText`, `boxShapes`, `getLints`
- `ctx.signal`: `AbortSignal`; teardown every listener/interval
- `config.js` runs before mount for custom shape/tool/component utils; `main.js` runs mounted and reruns on save

### 5. Interactive buttons

Full sample: `scripts/counter.js` (MINUS/RESET/PLUS, state `0 → 1 → 2 → 1 → 0`). Verify with one `/exec` simulated click + state read, not a real mouse.

```js
export default function ({ editor, helpers, signal }) {
  // 1. Build buttons idempotently; tag each with meta so the handler finds them.
  //    Give buttons a visible label AND a meta.action.
  // 2. Hit-test pointer_down in PAGE coordinates against the button bounds:
  const inside = (b, p) => p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h
  function onEvent(info) {
    if (!info || info.name !== 'pointer_down') return
    let p = null
    try { if (info.point && editor.screenToPage) p = editor.screenToPage(info.point) } catch {}
    p = p ?? editor.inputs?.currentPagePoint
    if (!p) return
    const hit = editor.getCurrentPageShapes().find(
      (s) => s.meta?.ui === 'button' &&
        inside({ x: s.x, y: s.y, w: s.props.w, h: s.props.h }, p)
    )
    if (hit) runAction(hit.meta.action)   // mutate state; store it in a shape's meta
  }
  editor.on('event', onEvent)
  signal.addEventListener('abort', () => editor.off('event', onEvent))  // REQUIRED
}
```

Build buttons idempotently in the same script that handles them; give visible labels + `meta.action`; hit-test pointer-down in page coordinates; store state in shape `meta` and render it via `richText`; find by `meta`/label, not coordinates. Broad store listeners can feedback-loop; use `helpers.onShapeTranslate` for one anchor + attached shapes. Continuous motion uses `editor.on('tick', fn)`.

The file watcher must apply the script first. Linux inotify exhaustion (`inotify_add_watch ... No space left on device`) yields `script-status` `state: "not-watching"`/`hasEntry: false`; host limit, not script bug.

Computer-use testing is separate from the product path: background CUA may return `background_unavailable` for an occluded Electron renderer; if needed follow `escalation: "foreground"`, set `delivery_mode: "foreground"`, pair `bring_to_front`, and use X11 XTest (`x11_xtest_fg`) to dismiss consent/click. Do not conclude synthetic clicks are rejected; `/exec` remains the real product path.

### 6. Self-running `.tldraw`

A `.tldraw` archive contains `metadata.json`, `session.json`, `db.sqlite`, `assets/`, and `script/`.

- `metadata.json` `script` manifest: `{ "sha256": "<digest>" }`; digest is SHA-256 over sorted script paths as `` `${path}\0${sha256hex(bytes)}\n` ``. Mismatch is rejected as tampered.
- Trust digest in `~/.tldraw/script-trust.json`: `{ "trusted": ["<digest>"] }`, or use `$TLDRAW_SCRIPT_TRUST`; consent is skipped when `isScriptTrusted(digest)` is true.

### 7. End-to-end edit loop

1. Read current port/token every call; resolve focused doc.
2. `/exec` for one-off layout; `/script-workspace` for durable behavior.
3. Stable IDs + `helpers.createShapeIfMissing`; reruns must be idempotent.
4. Keep script writes out of undo: `editor.run(fn, { history: 'ignore' })` or `helpers.translateShapes`.
5. Use store/event/tick listeners with `signal` cleanup; pointer hit-test uses page coordinates.
6. Prefer `helpers.onShapeTranslate(anchorId, fn, { signal })` for moving anchors.

## Shape Props (tldraw SDK v5)

`createShape`/`createShapeIfMissing` accept partial props; raw snapshot records require all fields below, validated by `scripts/validate_shapes.mjs`:

| Shape | Required props |
|-------|----------------|
| `note`  | `richText`, `color`, `labelColor`, `size`, `font`, `align`, `verticalAlign`, `growY`, `fontSizeAdjustment`, `url`, `scale`, `textLastEditedBy` |
| `text`  | `richText`, `color`, `size`, `font`, `textAlign`, `w`, `scale`, `autoSize` |
| `frame` | `w`, `h`, `name`, `color` |
| `geo`   | `geo`, `w`, `h`, `color`, `fill`, `richText` (+ dash/size/etc. defaulted) |

`richText` must be `toRichText('...')`, not a bare string. `color`: `black grey light-violet violet blue light-blue yellow orange green light-green light-red red white`. `font`: `draw sans serif mono`.

## Pitfalls

- `store.listen` fires on the tick after commit, not synchronously; await a tick before reading state. `editor.dispatch` is also async.
- Entry receives `{ editor, helpers, signal }`; no global `editor`; import `createShapeId`/`toRichText`/`Vec` from `tldraw`.
- Use `richText`, not `text`; raw records need full props while `createShape` can be partial.
- Scripts rerun each load; stable IDs + `createShapeIfMissing` prevent duplicates/clobbering.
- Abort every `store.listen`, `editor.on`, and `setInterval`; otherwise reruns double actions.
- Use `editor.run(..., { history: 'ignore' })` for script-owned writes.
- `editor.on('tick')` pauses when hidden (RAF); `setInterval` is Electron-throttled to ~1/s.
- API requires bearer token; port can be non-default (`server.listen(0)`); never hardcode `7236`.
- Only `tldraw`, `react`, `react-dom` imports; this is not a Node project.

## Verification

- offline schema: `node scripts/validate_shapes.mjs`; expected `3/3`
- live edits: `/api/search` → `api.getShapes(docId)` returns `{ page, viewport, shapes }`; `api.getBindings(docId)` returns array; inspect `api.getScreenshot(docId)` PNG/JPEG with `vision_analyze`
- durable script: `GET /api/doc/:id/script-status`; success=`state: "applied"`, `currentDiskDigest === lastAppliedDigest === manifestSha256`, `pendingApply === false`, `lastApplyError === null`
- pending after retry → report pending; error → read `errorLogPath`; never claim applied
