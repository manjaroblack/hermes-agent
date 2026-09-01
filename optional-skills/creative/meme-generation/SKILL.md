---
name: meme-generation
description: Create meme PNGs from templates with Pillow text overlay.
version: 2.0.0
author: adanaleycio
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, memes, humor, images]
    related_skills: [ascii-art]
    category: creative
---

# Meme Generation

role: meme image production operator
do: identify joke dynamic; choose template; write short captions; render PNG; optionally generate source scene; overlay text; inspect legibility; deliver artifact
inputs: topic/situation, template name or ID, captions, optional image scene, output path
outputs: non-empty meme PNG with readable text; optional vision review and MEDIA path
¬: long captions; wrong field count; generate hateful/abusive/personally targeted content; claim output before file/vision check; include text in AI scene prompt

Generate an actual meme image from a topic: select a template, write captions, and render text with Pillow.

## When to Use

- make/generate a meme about a topic, situation, or frustration
- user says `meme this` or equivalent
- classic template or original AI-generated scene with text overlay

## Prerequisites

- skill script `scripts/generate_meme.py`
- Pillow and network access for first-time dynamic template download
- optional `image_generate` and `vision_analyze`

## Templates

Supports ~100 popular imgflip templates by name/ID plus 10 curated templates with hand-tuned placement.

| ID | Name | Fields | Best for |
|----|------|--------|----------|
| `this-is-fine` | This is Fine | top, bottom | chaos, denial |
| `drake` | Drake Hotline Bling | reject, approve | rejecting/preferring |
| `distracted-boyfriend` | Distracted Boyfriend | distraction, current, person | temptation, shifting priorities |
| `two-buttons` | Two Buttons | left, right, person | impossible choice |
| `expanding-brain` | Expanding Brain | 4 levels | escalating irony |
| `change-my-mind` | Change My Mind | statement | hot takes |
| `woman-yelling-at-cat` | Woman Yelling at Cat | woman, cat | arguments |
| `one-does-not-simply` | One Does Not Simply | top, bottom | deceptively hard things |
| `grus-plan` | Gru's Plan | step1-3, realization | plans that backfire |
| `batman-slapping-robin` | Batman Slapping Robin | robin, batman | shutting down bad ideas |

Dynamic templates use smart defaults: top/bottom for 2 fields; evenly spaced for 3+.

```bash
python "$SKILL_DIR/scripts/generate_meme.py" --search "disaster"
```

## Procedure

### 1. Classic template (default)

1. Extract the core dynamic: chaos, dilemma, preference, irony, etc.
2. Pick by `Best for` or search with `--search`.
3. Write captions, 8-12 words max per field; shorter is better.
4. Locate the script:

   ```bash
   SKILL_DIR=$(dirname "$(find ~/.hermes/skills -path '*/meme-generation/SKILL.md' 2>/dev/null | head -1)")
   ```

5. Render:

   ```bash
   python "$SKILL_DIR/scripts/generate_meme.py" <template_id> /tmp/meme.png "caption 1" "caption 2" ...
   ```

6. Verify file and deliver `MEDIA:/tmp/meme.png`.

### 2. Custom AI scene

Use when no classic template fits or the user wants original art.

1. Write captions first.
2. Call `image_generate` with only the visual scene; **do not include text** because the script adds it.
3. Read the returned URL and download the scene locally.
4. Overlay text:

   ```bash
   python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png /tmp/meme.png "top text" "bottom text"
   python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png --bars /tmp/meme.png "top text" "bottom text"
   ```

   `--bars` uses black top/bottom bars and white text; prefer it for busy images.
5. If `vision_analyze` exists, inspect:

   ```python
   vision_analyze(image_url="/tmp/meme.png", question="Is the text legible and well-positioned? Does the meme work visually?")
   ```

   If placement/legibility fails, switch overlay↔bars or regenerate the scene.
6. Deliver `MEDIA:/tmp/meme.png`.

## Examples

```bash
# debugging production at 2 AM
python generate_meme.py this-is-fine /tmp/meme.png "SERVERS ARE ON FIRE" "This is fine"

# choosing sleep vs one more episode
python generate_meme.py drake /tmp/meme.png "Getting 8 hours of sleep" "One more episode at 3 AM"

# stages of a Monday morning
python generate_meme.py expanding-brain /tmp/meme.png "Setting an alarm" "Setting 5 alarms" "Sleeping through all alarms" "Working from bed"
```

List templates:

```bash
python generate_meme.py --list
```

## Pitfalls

- Keep captions short and match template field count.
- Match joke structure, not merely topic.
- Do not generate hateful, abusive, or personally targeted content.
- `scripts/.cache/` stores template images after first download.
- AI scene prompts must omit text; overlay text in the script.

## Verification

- `.png` exists at output path and is non-empty
- text is legible with white/black-outline or bars mode
- caption dynamic matches the template structure
- vision review passes when available
- artifact is deliverable as `MEDIA:` path

## Preserved Source Examples

### Original example 1

```bash
python generate_meme.py this-is-fine /tmp/meme.png "SERVERS ARE ON FIRE" "This is fine"
```

### Original example 2

```bash
python generate_meme.py drake /tmp/meme.png "Getting 8 hours of sleep" "One more episode at 3 AM"
```

### Original example 3

```bash
python generate_meme.py expanding-brain /tmp/meme.png "Setting an alarm" "Setting 5 alarms" "Sleeping through all alarms" "Working from bed"
```
