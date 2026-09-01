---
name: pokemon-player
description: "Play Pokemon via headless emulator + RAM reads."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
tags: [gaming, pokemon, emulator, pyboy, gameplay, gameboy]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [gaming, pokemon, emulator, pyboy, gameplay, gameboy]
    related_skills: []
---

# Pokemon Player

role: Pokemon headless-emulation gameplay operator
do: set up pokemon-agent; obtain user ROM path; run server; expose dashboard; observe RAM+vision; act in short sequences; save; record PKM memory; report state
inputs: game/ROM supplied by user (`.gb`, `.gbc`, `.gba`); optional checkout/save; gameplay objective
outputs: running game server; optional dashboard URL; verified moves; named save; PKM progress note
¬: download/provide ROMs; act blindly; send long action lists; skip screenshots; lose risky progress; expose user files or tunnel secrets

Play Pokemon through the `pokemon-agent` package with headless emulation, RAM
reads, screenshots, and `vision_analyze`.

## When to Use

- user says "play pokemon", "start pokemon", or "pokemon game"
- user asks about Pokemon Red, Blue, Yellow, FireRed, etc.
- user wants to watch an AI play Pokemon
- user references a `.gb`, `.gbc`, or `.gba` ROM

## Prerequisites

- NousResearch/pokemon-agent checkout and Python 3.10+ environment
- `uv` preferred; fall back to `python -m venv` + `pip`
- user-provided ROM; ask for its path
- NEVER download or provide ROM files

## Procedure

### 1. First-time setup

Clone NousResearch/pokemon-agent when no checkout exists. Create/activate a
Python 3.10+ environment, install editable package with the `pyboy` extra, or
reuse an existing checkout such as `~/pokemon-agent` with its `.venv`.
Ask the user for a ROM; a prior setup may contain
`roms/pokemon_red.gb`, but do not obtain ROM content.

### 2. Start the game server

From the activated `pokemon-agent` directory run `pokemon-agent serve` with
`--rom <path>` and `--port 9876`; run in the background with `&`. Resume with
`--load-state <save-name>`. Wait 4 seconds, then verify `GET /health`.

### 3. Offer a live dashboard

Use an SSH reverse tunnel through the keyless localhost.run endpoint:

```text
ssh -R 80:localhost:9876 ssh://nokey@localhost.run
```

Redirect tunnel output to a log, wait 10 seconds, locate the `.lhr.life` URL,
and give the user that URL with `/dashboard/` appended. The URL changes after
each restart; report the new URL. Do not expose unrelated log content.

### 4. Save and load

- save every 15-20 turns
- save before gym battles, rival encounters, risky fights, new towns/dungeons, and uncertain actions
- `POST /save` with a descriptive name, e.g. `before_brock`, `route1_start`, `mt_moon_entrance`, `got_cut`
- `POST /load` with the save name
- `GET /saves` lists saves
- `--load-state` loads during server startup and is faster than post-start API loading

### 5. Gameplay loop

1. **OBSERVE** — call `GET /state` for position, HP, battle, dialog; call `GET /screenshot`, save `/tmp/pokemon.png`, then use `vision_analyze`; always do both.
2. **ORIENT** — dialog → advance; battle → fight/run; hurt party → Pokemon Center; near objective → navigate carefully.
3. **DECIDE** — priority: dialog > battle > heal > story objective > training > explore.
4. **ACT** — `POST /action` with only 2-4 actions.
5. **VERIFY** — screenshot after every move sequence; use `vision_analyze` to confirm the intended position.
6. **RECORD** — save progress to memory with `PKM:` prefix.
7. **SAVE** — save periodically and before risk.

### 6. Action reference

- `press_a` — confirm, talk, select
- `press_b` — cancel, close menu
- `press_start` — open game menu
- `walk_up/down/left/right` — move one tile
- `hold_b_N` — hold B for N frames to speed text
- `wait_60` — approximately one second / 60 frames
- `a_until_dialog_end` — press A until dialog clears

### 7. Navigation and dialog rules

- screenshot every 2-4 movement steps; RAM gives position/HP, not surroundings
- inspect ledges, fences, signs, doors, NPCs, and stuck states with vision; ask specific questions such as "what is one tile north of me?"
- after a door/stair warp, add 2-3 `wait_60` actions for the fade/map transition; otherwise RAM position may be stale
- after exiting a building, sidestep left or right 2 tiles before moving north; north immediately re-enters the door
- Gen 1 text: hold B for 120 frames, press A, repeat; `a_until_dialog_end` may miss text states, so use manual `hold_b` + `press_a` and verify by screenshot
- ledges jump down/south only; route around left/right when north is blocked, guided by vision
- move 2-4 steps, screenshot on new areas, ask vision for direction, and fully re-evaluate after 3+ failed attempts; never spam 10-15 movements

### 8. Battle rules

- wild battle not needed → RUN: default cursor FIGHT top-left; press down, right, A; use `hold_b` for text/animations
- FIGHT: FIGHT is top-left; press A into move selection, A to use first move; hold B during animation/text
- catch → weaken, then throw Poke Ball
- type advantage → super-effective move; no advantage → strongest STAB move
- low HP → switch or use Potion

Gen 1 matchups: Water beats Fire/Ground/Rock; Fire beats Grass/Bug/Ice;
Grass beats Water/Ground/Rock; Electric beats Water/Flying; Ground beats
Fire/Electric/Rock/Poison; Psychic beats Fighting/Poison and is dominant in
Gen 1. Quirks: Special is offense+defense for special moves; Ghost moves are
bugged; critical hits use Speed; Wrap/Bind prevent opponent action; Focus Energy
reduces crit rate instead of raising it.

### 9. Memory conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| PKM:OBJECTIVE | Current goal | Get Parcel from Viridian Mart |
| PKM:MAP | Navigation knowledge | Viridian: mart is northeast |
| PKM:STRATEGY | Battle/team plans | Need Grass type before Misty |
| PKM:PROGRESS | Milestone tracker | Beat rival, heading to Viridian |
| PKM:STUCK | Stuck situations | Ledge at y=28 go right to bypass |
| PKM:TEAM | Team notes | Squirtle Lv6, Tackle + Tail Whip |

### 10. Progression milestones

- Choose starter
- Deliver Parcel from Viridian Mart, receive Pokedex
- Boulder Badge — Brock (Rock) → Water/Grass
- Cascade Badge — Misty (Water) → Grass/Electric
- Thunder Badge — Lt. Surge (Electric) → Ground
- Rainbow Badge — Erika (Grass) → Fire/Ice/Flying
- Soul Badge — Koga (Poison) → Ground/Psychic
- Marsh Badge — Sabrina (Psychic), hardest gym
- Volcano Badge — Blaine (Fire) → Water/Ground
- Earth Badge — Giovanni (Ground) → Water/Grass/Ice
- Elite Four → Champion

### 11. Stop play

1. `POST /save` with a descriptive name.
2. Update memory with `PKM:PROGRESS`.
3. Tell the user: "Game saved as [name]! Say 'play pokemon' to resume."
4. Kill server and tunnel background processes.

## Pitfalls

- NEVER download or provide ROM files.
- Do not send more than 4-5 actions without a vision check.
- Sidestep after building exits before going north.
- Add `wait_60` x2-3 after door/stair warps.
- RAM dialog detection is unreliable; verify with screenshots.
- Save before risky encounters.
- Tunnel URL changes on every restart.

## Verification

- `/health` returns successfully after startup.
- Each move sequence has a screenshot/vision confirmation.
- `GET /state` and visual scene agree on position, battle, dialog, and HP.
- Save appears through `GET /saves`; stopping play updates `PKM:PROGRESS`.
- Dashboard URL, when offered, resolves with `/dashboard/` and the current tunnel.