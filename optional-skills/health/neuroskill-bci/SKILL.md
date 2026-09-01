---
name: neuroskill-bci
description: "Use live BCI cognitive and mood state from NeuroSkill."
platforms: [linux, macos, windows]
version: 1.0.0
author: Hermes Agent + Nous Research
license: MIT
metadata:
  hermes:
    tags: [BCI, neurofeedback, health, focus, EEG, cognitive-state, biometrics, neuroskill]
    category: health
    related_skills: []
---

# NeuroSkill BCI

role: NeuroSkill BCI state and neurofeedback operator
do: verify device/app; query live scores; analyze sessions/sleep/history; label moments; stream events; suggest protocols only with consent; explain uncertainty
inputs: connected Muse 2/Muse S/OpenBCI; user state question; UTC range; label/query; optional protocol/timer request
outputs: interpreted cognitive/mood/body metrics; session trends/comparisons; sleep analysis; labels; protocol suggestion; explicit research-use caveat
¬: diagnose/treat; call metrics medical evidence; interrupt flow; report raw numbers without meaning; suggest protocol without asking; expose biometric data

Connect Hermes to a running [NeuroSkill](https://neuroskill.com/) instance to
read real-time brain/body metrics from a BCI wearable, give cognitively-aware
responses, suggest interventions, and track mental performance.

> **Research Use Only** — NeuroSkill is an open-source research tool. It is
> NOT a medical device and has NOT been cleared by the FDA, CE, or any regulatory
> body. Never use these metrics for clinical diagnosis or treatment.

References: `references/metrics.md` (metric guide), `references/protocols.md`
(interventions), `references/api.md` (WebSocket/HTTP API).

## When to Use

- user asks about current focus, relaxation, mood, cognitive load, drowsiness, readiness, or recovery
- user asks to compare sessions, find similar historical states, inspect labels, sleep, or UMAP
- user asks to mark a moment, start a timer, calibrate, notify, or stream live state
- user reports concentration difficulty, stress, fatigue, or sleep concerns and a connected BCI can add context

## Prerequisites

- Node.js 20+: `node --version`
- NeuroSkill desktop app running with a connected BCI
- Muse 2, Muse S, or OpenBCI hardware: 4-channel EEG + PPG + IMU via BLE
- `npx neuroskill status` succeeds

Verify setup:

```bash
node --version
npx neuroskill status
npx neuroskill status --json
```

On error: open NeuroSkill; power/connect the BCI over Bluetooth; check green
electrode indicators (≥0.7 each); install Node.js 20+ if `command not found`.

## Procedure

### 1. Query current state

Always use `--json` for reliable parsing; default output is colorized human text.

### CLI Reference

All commands support `--json` (raw JSON, pipe-safe) and `--full` (human summary + JSON):

| Command | Description |
|---|---|
| `status` | Full snapshot: device, scores, bands, ratios, sleep, history |
| `session [N]` | Session breakdown with first/second-half trends (0=most recent) |
| `sessions` | All recorded sessions across days |
| `search` | ANN search for neurally similar historical moments |
| `compare` | A/B session deltas and trend analysis |
| `sleep [N]` | Sleep stages (Wake/N1/N2/N3/REM) with analysis |
| `label "text"` | Timestamped annotation at current moment |
| `search-labels "query"` | Semantic vector search over labels |
| `interactive "query"` | Cross-modal 4-layer graph search (text → EXG → labels) |
| `listen` | Real-time event stream; default 5s, set `--seconds N` |
| `umap` | 3D UMAP session-embedding projection |
| `calibrate` | Calibration window/profile |
| `timer` | Focus Timer: Pomodoro/Deep Work/Short Focus |
| `notify "title" "body"` | NeuroSkill OS notification |
| `raw '{json}'` | Raw JSON passthrough to server |

Global flags: `--json` (raw/no ANSI/pipe-safe); `--full` (summary + colorized
JSON); `--port <N>` (override server port; auto-discover, usually 8375);
`--ws`/`--http` (transport); `--k <N>` (nearest-neighbor count for search and
search-labels); `--seconds <N>` (listen duration, default 5); `--trends` (session
trends); `--dot` (Graphviz DOT for interactive).

```bash
npx neuroskill status --json
```

The `scores` object uses 0-1 unless noted:

```jsonc
{
  "scores": {
    "focus": 0.70,           // β / (α + θ) — sustained attention
    "relaxation": 0.40,      // α / (β + θ) — calm wakefulness
    "engagement": 0.60,      // active mental investment
    "meditation": 0.52,      // alpha + stillness + HRV coherence
    "mood": 0.55,            // composite from FAA, TAR, BAR
    "cognitive_load": 0.33,  // frontal θ / temporal α · f(FAA, TBR)
    "drowsiness": 0.10,      // TAR + TBR + falling spectral centroid
    "hr": 68.2,              // heart rate in bpm (from PPG)
    "snr": 14.3,             // signal-to-noise ratio in dB
    "stillness": 0.88,       // 0–1; 1 = perfectly still
    "faa": 0.042,            // Frontal Alpha Asymmetry (+ = approach)
    "tar": 0.56,             // Theta/Alpha Ratio
    "bar": 0.53,             // Beta/Alpha Ratio
    "tbr": 1.06,             // Theta/Beta Ratio (ADHD proxy)
    "apf": 10.1,             // Alpha Peak Frequency in Hz
    "coherence": 0.614,      // inter-hemispheric coherence
    "bands": {
      "rel_delta": 0.28, "rel_theta": 0.18,
      "rel_alpha": 0.32, "rel_beta": 0.17, "rel_gamma": 0.05
    }
  }
}
```

Also parse `device` (state, battery, firmware), `signal_quality` (per-electrode
0-1), `session` (duration, epochs), `embeddings`, `labels`, `sleep`, and
`history`. Translate metrics into meaning, never raw numbers alone. Reference
thresholds: focus >0.70 flow; focus <0.40 break/protocol; drowsiness >0.60
fatigue; relaxation <0.30 stress intervention; cognitive load >0.70 sustained
offload/break; TBR >1.5 theta dominance; FAA <0 negative affect; SNR <3 dB
unreliable signal/electrode repositioning.

### 2. Analyze sessions

```bash
npx neuroskill session --json
npx neuroskill session 1 --json
npx neuroskill session 0 --json | jq '{focus: .metrics.focus, trend: .trends.focus}'
npx neuroskill sessions --json
npx neuroskill sessions --trends
```

Session output includes first-half/second-half trends (`up`, `down`, `flat`).
Use this to describe evolution, e.g. focus 0.64 → 0.76 and cognitive load
0.38 → 0.28 can indicate the task became more automatic; describe context, not
just deltas.

### 3. Search historical states

Neural search uses HNSW approximate nearest neighbors over 128-D ZUNA
embeddings; returns distance statistics, hour distribution, and matching days.

```bash
npx neuroskill search --json
npx neuroskill search --k 10 --json
npx neuroskill search --start <UTC> --end <UTC> --json
npx neuroskill search-labels "deep focus" --k 10 --json
npx neuroskill search-labels "stress" --json | jq '[.results[].EXG_metrics.tbr]'
npx neuroskill interactive "deep focus" --json
npx neuroskill interactive "deep focus" --dot | dot -Tsvg > graph.svg
```

Use `--k-text`, `--k-EXG`, and `--reach <minutes>` for cross-modal graph search.
The graph is query → text labels → EXG points → nearby labels. Use searches for
"When was I last in a state like this?", best focus sessions, or afternoon crashes.
Label search uses Xenova/bge-small-en-v1.5 and returns labels plus EXG metrics.

### 4. Compare sessions

```bash
npx neuroskill compare --json
npx neuroskill compare --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
npx neuroskill compare --json | jq '.insights.deltas | to_entries | sort_by(.value.pct) | reverse'
```

Output has absolute/percentage/directional changes for ~50 metrics,
`insights.improved[]`, `insights.declined[]`, sleep staging, and a UMAP job ID.
Interpret trends and possible causes, not isolated deltas; mention improvements,
declines, and likely context (for example, higher engagement with more stress
spikes, a 15% stress-index increase, or more-negative FAA).

### 5. Inspect sleep

```bash
npx neuroskill sleep --json
npx neuroskill sleep 0 --json
npx neuroskill sleep --start <UTC> --end <UTC> --json
npx neuroskill sleep --json | jq '.summary | {n3: .n3_epochs, rem: .rem_epochs}'
npx neuroskill sleep --json | jq '.analysis.efficiency_pct'
```

Sleep epochs use 5-second windows: 0=Wake, 1=N1, 2=N2, 3=N3/deep,
4=REM. Analysis includes `efficiency_pct`, onset/REM latency, and bout counts.
Healthy targets: N3 15–25%, REM 20–25%, efficiency >85%, onset <20 min.

### 6. Label moments

```bash
npx neuroskill label "breakthrough"
npx neuroskill label "studying algorithms"
npx neuroskill label "post-meditation"
npx neuroskill label --json "focus block start"
```

Auto-label a breakthrough/insight, task-type switch, completed protocol, explicit
user request, or notable flow transition. Labels persist and feed
`search-labels`/`interactive`.

### 7. Stream events and visualize

```bash
npx neuroskill listen --seconds 30 --json
npx neuroskill listen --seconds 5 --json | jq '[.[] | select(.event == "scores")]'
npx neuroskill umap --json
npx neuroskill umap --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

`listen` streams EXG, PPG, IMU, scores, and labels over WebSocket for the
duration; `--http` cannot provide it. UMAP is GPU-accelerated 3D over ZUNA
embeddings: `separation_score > 1.5` means distinct sessions; `< 0.5` means
similar states.

### 8. Proactive awareness and protocols

Optionally query status at session start when the user says they wear the device
or asks about state. Mention state only when explicitly asked, concentration/
stress/fatigue is reported, a critical threshold crosses (drowsiness >0.70 or
focus <0.30 sustained), or demanding-work readiness is requested. If focus >0.75,
protect flow and stay silent. A brief permitted summary can say: “focus is
building at 0.62, relaxation is 0.55, and FAA is positive — approach motivation
is engaged.”

Before any intervention, ask. Use `references/protocols.md` and these triggers:

- focus <0.40 + TBR >1.5 → Theta-Beta Neurofeedback Anchor or Box Breathing
- relaxation <0.30 + high `stress_index` → Cardiac Coherence or 4-7-8 Breathing
- cognitive load >0.70 sustained → Cognitive Load Offload
- drowsiness >0.60 → Ultradian Reset or Wake Reset
- FAA <0 → FAA Rebalancing
- focus >0.75 + engagement >0.70 → do not interrupt
- high stillness + `headache_index` → Neck Release Sequence
- RMSSD <25ms → Vagal Toning

Protocol suggestion example: if focus has declined for 15 minutes and TBR exceeds
1.5, explain theta dominance/fatigue and ask whether the user wants the
90-second Theta-Beta Neurofeedback Anchor; never start it without consent.

### 9. Timer, calibration, notifications, raw commands

```bash
npx neuroskill timer --json
npx neuroskill calibrate
npx neuroskill calibrate --profile "Eyes Open"
npx neuroskill notify "Break Time" "Your focus has been declining for 20 minutes"
npx neuroskill raw '{"command":"status"}' --json
```

Timer presets: Pomodoro 25/5, Deep Work 50/10, Short Focus 15/5. Calibration
opens a window for poor signal or a personalized baseline. `raw` passes unmapped
server commands through.

## Pitfalls

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `npx neuroskill status` hangs | NeuroSkill app not running | Open NeuroSkill desktop app |
| `device.state: "disconnected"` | BCI device not connected | Check Bluetooth, device battery |
| All scores return 0 | Poor electrode contact | Reposition headband, moisten electrodes |
| `signal_quality` values < 0.7 | Loose electrodes | Adjust fit, clean electrode contacts |
| SNR < 3 dB | Noisy signal | Minimize head movement, check environment |
| `command not found: npx` | Node.js not installed | Install Node.js 20+ |

- NeuroSkill is research-only, not medical diagnosis/treatment.
- Do not report raw scores without interpretation; thresholds are heuristic.
- Never interrupt flow state; ask before protocols.
- Poor electrode contact can zero scores; inspect signal quality and SNR.
- WebSocket is required for `listen`; HTTP transport cannot stream it.

## Verification

- `node --version` is 20+ and `npx neuroskill status --json` returns data.
- State responses include device/signal/session context and scores are explained.
- Session comparison reports trends and deltas with context.
- Sleep reports stage codes, architecture, efficiency, and healthy-target comparison.
- Labels return a label ID when `--json` is used and are searchable later.
- Protocol suggestions respect thresholds, research-only limits, consent, and flow protection.

## Examples

```bash
npx neuroskill status --json
npx neuroskill compare --json
npx neuroskill search-labels "flow" --json
npx neuroskill search --json
npx neuroskill sleep --json
npx neuroskill label "breakthrough"
```

Interpret current state naturally; compare improvements/declines; report flow
timestamps, metrics, labels, sleep architecture, or saved-label confirmation as
requested.

Interaction rules:

- “How am I doing?” → `status`; interpret focus, relaxation, mood, FAA, TBR; suggest action only if indicated.
- “I can't concentrate” → `status`; check high theta/low beta/rising TBR/drowsiness; if metrics look fine, say motivation may be the cause rather than neurological evidence.
- “Compare today vs yesterday” → `compare`; explain improved/declined trends and possible causes.
- “When was I last in flow?” → `search-labels "flow"` + `search`; report timestamps, metrics, and labels.
- “How did I sleep?” → `sleep`; report N3/REM/efficiency against targets and note wake/REM issues.
- “Mark this breakthrough” → `label "breakthrough"`; confirm save and optionally record current metrics.

## References

- [NeuroSkill Paper — arXiv:2603.03212](https://arxiv.org/abs/2603.03212) (Kosmyna & Hauptmann, MIT Media Lab)
- [NeuroSkill Desktop App](https://github.com/NeuroSkill-com/skill) (GPLv3)
- [NeuroLoop CLI Companion](https://github.com/NeuroSkill-com/neuroloop) (GPLv3)
- [MIT Media Lab Project](https://www.media.mit.edu/projects/neuroskill/overview/)