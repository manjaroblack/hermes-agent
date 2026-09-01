---
name: ascii-art
description: "ASCII art: pyfiglet, cowsay, boxes, image-to-ascii."
version: 4.0.0
author: 0xbyt4, Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ASCII, Art, Banners, Creative, Unicode, Text-Art, pyfiglet, figlet, cowsay, boxes]
    related_skills: [excalidraw]

---

# ASCII Art

role: local/HTTP ASCII-art producer
do: choose the smallest suitable banner, character-art, border, image-conversion, lookup, or custom-art path
inputs: text/image/subject/style/width/height; optional installed CLI
outputs: terminal-safe ASCII/Unicode text or saved text artifact
¬: API-key assumptions; width/height overflow; ANSI output where plain text is required

No API keys are required. Prefer local tools; fall back to the free remote API or next method when a binary is unavailable.

## When to Use

- generate banners, cowsay/boxes art, image-to-ASCII, QR/weather art, or custom Unicode art
- use when terminal-safe fixed-width output is the requested artifact

## Procedure

1. text banner → pyfiglet; if absent, asciified API
2. message in character speech/thought bubble → cowsay
3. decorative frame → boxes; combine with banner tool
4. specific subject → ascii.co.uk + `<pre>` extraction
5. image → ascii-image-converter or jp2a
6. QR → qrenco.de
7. weather/moon → wttr.in
8. custom art → Unicode generation
9. missing tool → install or next option

## Text Banners: pyfiglet

571 local fonts.

```bash
pip install pyfiglet --break-system-packages -q
python -m pyfiglet "YOUR TEXT" -f slant
python -m pyfiglet "TEXT" -f doom -w 80    # Set width
python -m pyfiglet --list_fonts             # List all 571 fonts
```

| Style | Font | Best for |
|-------|------|----------|
| Clean & modern | `slant` | Project names, headers |
| Bold & blocky | `doom` | Titles, logos |
| Big & readable | `big` | Banners |
| Classic banner | `banner3` | Wide displays |
| Compact | `small` | Subtitles |
| Cyberpunk | `cyberlarge` | Tech themes |
| 3D effect | `3-d` | Splash screens |
| Gothic | `gothic` | Dramatic text |

Preview 2–3 fonts; short text (1–8 chars) suits detailed `doom`/`block`; long text suits compact `small`/`mini`.

## Text Banners: asciified API

Free REST API, 250+ FIGlet fonts, plain-text response. Use when pyfiglet is absent or a quick remote alternative is wanted.

```bash
# Basic text banner (default font)
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello+World"

# With a specific font
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Slant"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Doom"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Star+Wars"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=3-D"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Banner3"

# List all available fonts (returns JSON array)
curl -s "https://asciified.thelicato.io/api/v2/fonts"
```

Encode spaces as `+`; response is display-ready plain ASCII; font names are case-sensitive, so query `/fonts`; works with curl alone.

## Cowsay

Speech bubble + ASCII character.

```bash
sudo apt install cowsay -y    # Debian/Ubuntu
# brew install cowsay         # macOS
cowsay "Hello World"
cowsay -f tux "Linux rules"       # Tux the penguin
cowsay -f dragon "Rawr!"          # Dragon
cowsay -f stegosaurus "Roar!"     # Stegosaurus
cowthink "Hmm..."                  # Thought bubble
cowsay -l                          # List all characters
```

Characters include:

`beavis.zen`, `bong`, `bunny`, `cheese`, `daemon`, `default`, `dragon`, `dragon-and-cow`, `elephant`, `eyes`, `flaming-skull`, `ghostbusters`, `hellokitty`, `kiss`, `kitty`, `koala`, `luke-koala`, `mech-and-cow`, `meow`, `moofasa`, `moose`, `ren`, `sheep`, `skeleton`, `small`, `stegosaurus`, `stimpy`, `supermilker`, `surgery`, `three-eyes`, `turkey`, `turtle`, `tux`, `udder`, `vader`, `vader-koala`, `www`.

```bash
cowsay -b "Borg"       # =_= eyes
cowsay -d "Dead"       # x_x eyes
cowsay -g "Greedy"     # $_$ eyes
cowsay -p "Paranoid"   # @_@ eyes
cowsay -s "Stoned"     # *_* eyes
cowsay -w "Wired"      # O_O eyes
cowsay -e "OO" "Msg"   # Custom eyes
cowsay -T "U " "Msg"   # Custom tongue
```

## Boxes

70+ decorative borders.

```bash
sudo apt install boxes -y    # Debian/Ubuntu
# brew install boxes         # macOS
echo "Hello World" | boxes                    # Default box
echo "Hello World" | boxes -d stone           # Stone border
echo "Hello World" | boxes -d parchment       # Parchment scroll
echo "Hello World" | boxes -d cat             # Cat border
echo "Hello World" | boxes -d dog             # Dog border
echo "Hello World" | boxes -d unicornsay      # Unicorn
echo "Hello World" | boxes -d diamonds        # Diamond pattern
echo "Hello World" | boxes -d c-cmt           # C-style comment
echo "Hello World" | boxes -d html-cmt        # HTML comment
echo "Hello World" | boxes -a c               # Center text
boxes -l                                       # List all 70+ designs
```

Combine:

```bash
python -m pyfiglet "HERMES" -f slant | boxes -d stone
# Or without pyfiglet installed:
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=HERMES&font=Slant" | boxes -d stone
```

## TOIlet

Colored/filter text art; ANSI may not render in plain files or some chat platforms.

```bash
sudo apt install toilet toilet-fonts -y    # Debian/Ubuntu
# brew install toilet                      # macOS
toilet "Hello World"                    # Basic text art
toilet -f bigmono12 "Hello"            # Specific font
toilet --gay "Rainbow!"                 # Rainbow coloring
toilet --metal "Metal!"                 # Metallic effect
toilet -F border "Bordered"             # Add border
toilet -F border --gay "Fancy!"         # Combined effects
toilet -f pagga "Block"                 # Block-style font (unique to toilet)
toilet -F list                          # List available filters
```

Filters: `crop`, `gay`, `metal`, `flip`, `flop`, `180`, `left`, `right`, `border`.

## Image → ASCII

Supports PNG, JPEG, GIF, WEBP.

### ascii-image-converter

```bash
# Install
sudo snap install ascii-image-converter
# OR: go install github.com/TheZoraiz/ascii-image-converter@latest

ascii-image-converter image.png                  # Basic
ascii-image-converter image.png -C               # Color output
ascii-image-converter image.png -d 60,30         # Set dimensions
ascii-image-converter image.png -b               # Braille characters
ascii-image-converter image.png -n               # Negative/inverted
ascii-image-converter https://url/image.jpg      # Direct URL
ascii-image-converter image.png --save-txt out   # Save as text
```

### jp2a

```bash
sudo apt install jp2a -y
jp2a --width=80 image.jpg
jp2a --colors image.jpg              # Colorized
```

## Search Pre-Made Art

`ascii.co.uk` stores classic art in HTML `<pre>` tags. URL: `https://ascii.co.uk/art/{subject}`.

```bash
curl -s 'https://ascii.co.uk/art/cat' -o /tmp/ascii_art.html
```

```python
import re, html
with open('/tmp/ascii_art.html') as f:
    text = f.read()
arts = re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
for art in arts:
    clean = re.sub(r'<[^>]+>', '', art)
    clean = html.unescape(clean).strip()
    if len(clean) > 30:
        print(clean)
        print('\n---\n')
```

Subjects:
- animals: `cat`, `dog`, `horse`, `bird`, `fish`, `dragon`, `snake`, `rabbit`, `elephant`, `dolphin`, `butterfly`, `owl`, `wolf`, `bear`, `penguin`, `turtle`
- objects: `car`, `ship`, `airplane`, `rocket`, `guitar`, `computer`, `coffee`, `beer`, `cake`, `house`, `castle`, `sword`, `crown`, `key`
- nature: `tree`, `flower`, `sun`, `moon`, `star`, `mountain`, `ocean`, `rainbow`
- characters: `skull`, `robot`, `angel`, `wizard`, `pirate`, `ninja`, `alien`
- holidays: `christmas`, `halloween`, `valentine`

Preserve artist signatures/initials; pages contain multiple pieces, select the best; curl works without JavaScript.

GitHub easter egg, no auth:

```bash
curl -s https://api.github.com/octocat
```

## Fun HTTP Utilities

```bash
curl -s "qrenco.de/Hello+World"
curl -s "qrenco.de/https://example.com"
curl -s "wttr.in/London"          # Full weather report with ASCII graphics
curl -s "wttr.in/Moon"            # Moon phase in ASCII art
curl -s "v2.wttr.in/London"       # Detailed version
```

## Custom Unicode Art

Use when tools cannot express the requested subject:

- box drawing: `╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯`
- block: `░ ▒ ▓ █ ▄ ▀ ▌ ▐ ▖ ▗ ▘ ▝ ▚ ▞`
- geometric/symbols: `◆ ◇ ◈ ● ○ ◉ ■ □ ▲ △ ▼ ▽ ★ ☆ ✦ ✧ ◀ ▶ ◁ ▷ ⬡ ⬢ ⌂`

Constraints: max 60 chars/line; max 15 lines banners, 25 scene; monospace-safe rendering.

## Pitfalls

- do not use a decorative tool when a requested subject needs a readable, recognizable result
- preserve fixed-width output; inspect remote/API responses before displaying them
- keep image conversion dimensions, color mode, negative mode, and Braille settings explicit

## Verification

- selected path matches the decision flow and user intent
- output stays within width/height limits and fixed-width rendering
- remote responses are checked before display; ANSI is labeled when relevant
- image conversion preserves requested dimensions/color/negative/Braille options
