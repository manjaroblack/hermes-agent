---
name: openhue
description: "Control Philips Hue lights, scenes, rooms via OpenHue CLI."
version: 1.0.1
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Smart-Home, Hue, Lights, IoT, Automation]
    homepage: https://www.openhue.io/cli
prerequisites:
  commands: [openhue]
---

# OpenHue CLI

role: Philips Hue terminal operator
do: install/pair OpenHue; list lights/rooms/scenes; set power/brightness/temperature/color; apply scenes/presets
inputs: Hue Bridge/network, exact case-sensitive resource name, on/off/brightness/color/temperature/scene
outputs: updated Hue light/room/scene state
¬: act before pairing; assume a different network; use wrong case-sensitive name; set color on white-only bulb

Control Philips Hue lights/scenes through a Hue Bridge. Bridge and Hermes host
must share the local network; first run requires pressing the Bridge button.

## When to Use

- turn lights on/off or set brightness
- set color/color temperature
- control a room, zone, or individual bulb
- apply scenes such as Relax, Concentrate, or movie mode
- schedule lighting through cron

## Prerequisites

Install one supported CLI build:

```bash
# Linux (pre-built binary — releases ship tarballs, not bare binaries)
curl -sL "https://github.com/openhue/openhue-cli/releases/latest/download/openhue_Linux_x86_64.tar.gz" \
  | tar -xz -C /tmp openhue \
  && install -m 0755 /tmp/openhue ~/.local/bin/openhue
# (use openhue_Linux_arm64.tar.gz on ARM64)

# macOS
brew install openhue/cli/openhue-cli
```

Pair on first run by physically pressing the Hue Bridge button.

## Quick Reference

| Action | Command |
|---|---|
| List lights/rooms/scenes | `openhue get light`; `openhue get room`; `openhue get scene` |
| Toggle bulb | `openhue set light "Bedroom Lamp" --on`; `openhue set light "Bedroom Lamp" --off` |
| Brightness | `openhue set light "Bedroom Lamp" --on --brightness 50` |
| Temperature | `openhue set light "Bedroom Lamp" --on --temperature 300` |
| Named/hex color | `openhue set light "Bedroom Lamp" --on --color red`; `openhue set light "Bedroom Lamp" --on --rgb "#FF5500"` |
| Room power/brightness | `openhue set room "Bedroom" --off`; `openhue set room "Bedroom" --on --brightness 30` |
| Scene | `openhue set scene "Relax" --room "Bedroom"` |

## Procedure

1. Verify Bridge/network, install, and complete button pairing.
2. Discover exact resource names:

```bash
openhue get light       # List all lights
openhue get room        # List all rooms
openhue get scene       # List all scenes
```

3. Apply the requested light/room/scene command; brightness = 0-100,
   temperature = 153-500 mirek (warm → cool).
4. Use color only on color-capable bulbs; re-list to verify resulting state.
5. For schedules, invoke the verified command from cron.

### Control Lights

```bash
# Turn on/off
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off

# Brightness (0-100)
openhue set light "Bedroom Lamp" --on --brightness 50

# Color temperature (warm to cool: 153-500 mirek)
openhue set light "Bedroom Lamp" --on --temperature 300

# Color (by name or hex)
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### Control Rooms

```bash
# Turn off entire room
openhue set room "Bedroom" --off

# Set room brightness
openhue set room "Bedroom" --on --brightness 30
```

### Scenes

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

### Quick Presets

```bash
# Bedtime (dim warm)
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode (bright cool)
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode (dim)
openhue set room "Living Room" --on --brightness 10

# Everything off
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## Pitfalls

- Bridge must share the local network with Hermes; first pairing is physical
- names are case-sensitive; use `openhue get light|room|scene` first
- color fails/has no effect on white-only bulbs
- Linux releases are tarballs; use ARM64 asset on ARM64

## Verification

- `openhue` installed and pairing completed
- requested exact resource exists in `get` output
- command exits successfully and resulting state matches request
- color/temperature capability matches the selected bulb
