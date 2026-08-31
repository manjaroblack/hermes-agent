---
name: findmy
description: "Track Apple devices/AirTags via FindMy.app on macOS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
---

# Find My (Apple)

role: privacy-bounded Find My observer
do: read owned Apple device/AirTag locations through FindMy.app UI; capture evidence; use `vision_analyze`
¬: CLI/API assumptions; tracking items the user does not own; reading screenshots by pixel parsing

FindMy has no Apple-provided CLI. Use AppleScript to activate the app, UI automation to choose Devices/Items, and screen capture to read locations.

## When to Use

- "where is my [device/cat/keys/bag]?"
- AirTag location tracking
- iPhone, iPad, Mac, or AirPods location checks
- monitoring owned pet/item movement over time (AirTag patrol route)

## Prerequisites

- macOS + Find My app; iCloud signed in
- target devices/AirTags registered in Find My
- Screen Recording permission for terminal: System Settings → Privacy → Screen Recording
- optional/recommended: `brew install steipete/tap/peekaboo`

## Method 1: AppleScript + Screenshot

### Open and capture

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Then:

```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Switch tabs

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

## Method 2: Peekaboo UI Automation

If installed, use element-aware capture/clicks:

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

Then:

```
vision_analyze(image_url="/tmp/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

## Procedure: AirTag patrol route

1. Activate Find My and open Items:

```bash
osascript -e 'tell application "FindMy" to activate'
sleep 3
```

2. Click the AirTag; keep its page displayed because the AirTag only updates while the page is open.
3. Capture periodically:

```bash
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # Every 5 minutes
done
```

4. Analyze each screenshot with `vision_analyze`; extract coordinates; compile a route. For ongoing collection, schedule captures with `cronjob` rather than an unmanaged infinite loop.

## Pitfalls

- FindMy has **no CLI or API**; UI automation is required.
- AirTags update only while the Find My page is actively displayed.
- Accuracy depends on nearby Apple devices in the Find My network.
- Screen Recording permission is required for screenshots.
- AppleScript UI automation can break across macOS versions.
- Keep Find My foreground/active while tracking; minimizing stops updates.
- Never try to parse pixels manually; use `vision_analyze`.

## Verification

- screenshot visibly shows the requested owned device/item and location
- location answer includes address/coordinates only when visible
- repeated captures have timestamps and can be ordered into a route
- privacy boundary confirmed: only devices/items the user owns are tracked
