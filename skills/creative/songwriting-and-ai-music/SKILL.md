---
name: songwriting-and-ai-music
description: "Songwriting craft and Suno AI music prompts."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
tags: [songwriting, music, suno, parody, lyrics, creative]
platforms: [linux, macos, windows]
triggers:
  - writing a song
  - song lyrics
  - music prompt
  - suno prompt
  - parody song
  - adapting a song
  - AI music generation
---

# Songwriting & AI Music Generation

role: songwriter + AI-music prompt editor
do: shape structure, sound, meter, emotion, parody/adaptation, Suno tags, and optional local-generation inputs
inputs: concept/hook, lyrics, source song, vocal/genre brief, target generator
outputs: singable lyrics, style prompt, bracketed metatags, variation plan
¬: treat guidelines as laws; artist/trademark names in Suno style prompts; untested pronunciation; guaranteed output quality

Everything here is a GUIDELINE, not a rule. Art breaks rules on purpose. Use what serves the song; ignore what does not.

## When to Use

- write songs/lyrics, parody or adapt a song, or prepare music/Suno prompts
- craft structure, meter, vocal direction, phonetics, or AI-music variations

## 1. Structure

Mix, modify, or invent:

```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse (refrain-based)    (jazz standards, ballads)
ABAB    Verse/Chorus alternating                    (simple, direct)
AAA     Verse/Verse/Verse (strophic, no chorus)     (folk, storytelling)
```

Blocks: Intro (mood/pull-in), Verse (story/details/world), Pre-Chorus (optional tension ramp), Chorus (emotional core/memory), Bridge (detour/perspective/key shift), Outro (farewell/echo/subversion). A song may be one evolving section; structure serves emotion.

## 2. Rhyme, Meter, Sound

Rhyme from tight to loose: perfect `lean/mean`; family `crate/braid`; assonance `had/glass`; consonance `scene/when`; near/slant. Mix perfect and slant: all-perfect can sound nursery-rhyme; all-slant can sound lazy. Internal rhyme creates echoes:

> "We pruned the lies from bleeding trees / Distilled the storm from entropy" — "lies/flies," "trees/entropy" create internal echoes.

Meter = stressed/unstressed rhythm. Matching syllable counts helps singability, but stressed syllables matter more. Say it aloud; stumbling means revise. Intentional breaks can emphasize/surprise.

## 3. Emotional Arc + Dynamics

A song is a journey, not a flat road. Rough energy map: `Intro: 2-3 | Verse: 5-6 | Pre-Chorus: 7 | Chorus: 8-9 | Bridge: varies | Final Chorus: 9-10`.

Contrast carries power: whisper before scream, sparse before dense, slow before fast, low before high; buildup makes the drop work; silence is an instrument. `Whisper to roar to whisper` = intimate → full power → vulnerable strip-back.

## 4. Lyrics

Show, usually:

- `"I was sad"` = flat
- `"Your hoodie's still on the hook by the door"` = alive
- plain `"I give my life"` can be the power

Hook = remembered/hummed/repeated line, often title/core phrase; align melody + lyric + emotion; place where it lands hardest, often first/last chorus line.

Prosody: stable feeling → settled melody, perfect rhymes, resolved chords; unstable feeling → wandering melody, near-rhymes, unresolved chords; verse often lower, chorus higher; flip when useful.

Avoid unless purposeful: autopilot cliches, forced rhyme word order/"Yoda-speak", same energy every section, treating first draft as sacred. Revision is creation.

## 5. Parody + Adaptation

Map the original skeleton: syllables/line, rhyme scheme (ABAB/AABB/etc.), stressed syllables, held/sustained notes. Match stressed syllables to beats; total count may flex by 1–2 unstressed syllables. Match held-note vowel sound (`LOOOVE` → `FOOOD` better than `LIFE`); monosyllabic swaps keep rhythm (`Crime -> Code`, `Snake -> Noose`). Sing new words over original and revise stumbles.

Pick a concept strong enough for the whole song; start title/hook outward; generate puns/phrases/images before fitting; reverse-engineer rhyme backward for a required line. Leave a few original lines/structures for recognizability and connection.

## 6. Suno Style Prompt

Formula: `Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics`.

```
BAD:  "sad rock song"
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky
       sultry female vocalist, big band jazz, brass section with
       trumpets and french horns, sweeping strings, minor key,
       vintage analog warmth"
```

Describe the journey:

```
"Begins as a haunting whisper over sparse piano. Gradually layers
 in muted brass. Builds through the chorus with full orchestra.
 Second verse erupts with raw belting intensity. Outro strips back
 to a lone piano and a fragile whisper fading to silence."
```

V4.5+ Style field supports up to 1,000 chars. No artist names/trademarks: `"1960s Cold War spy thriller brass"`, not `"James Bond style"`; `"90s grunge"`, not `"Nirvana-style"`. Add BPM/key when wanted; use Exclude Styles; unexpected combos can work (`"bossa nova trap"`, `"Appalachian gothic"`, `"chiptune jazz"`). Describe vocal persona: `"A weathered torch singer with a smoky alto, slight rasp, who starts vulnerable and builds to devastating power"`.

## 7. Suno Metatags

Put tags in brackets in lyrics; reinforce important tags in style + lyrics; keep 5–8 per section and never contradict.

Structure: `[Intro] [Verse] [Verse 1] [Pre-Chorus] [Chorus] [Post-Chorus] [Hook] [Bridge] [Interlude] [Instrumental] [Instrumental Break] [Guitar Solo] [Breakdown] [Build-up] [Outro] [Silence] [End]`

Vocals: `[Whispered] [Spoken Word] [Belted] [Falsetto] [Powerful] [Soulful] [Raspy] [Breathy] [Smooth] [Gritty] [Staccato] [Legato] [Vibrato] [Melismatic] [Harmonies] [Choir] [Harmonized Chorus]`

Dynamics: `[High Energy] [Low Energy] [Building Energy] [Explosive] [Emotional Climax] [Gradual swell] [Orchestral swell] [Quiet arrangement] [Falling tension] [Slow Down]`

Gender: `[Female Vocals] [Male Vocals]`.

Atmosphere: `[Melancholic] [Euphoric] [Nostalgic] [Aggressive] [Dreamy] [Intimate] [Dark Atmosphere]`.

SFX: `[Vinyl Crackle] [Rain] [Applause] [Static] [Thunder]`.

Custom Mode: separate Style + Lyrics for serious work; lyrics limit ~3,000 chars (~40–60 lines); structural tags prevent flat verse/chorus/verse.

## 8. Phonetics for AI Singers

AI vocalists pronounce rather than read. Spell sound (`through` → `thru`); test proper nouns early; `Nous` → `Noose`; hyphenate syllables (`Re-search`, `bio-engineering`). ALL CAPS = louder/intense; vowel extension `lo-o-o-ove`; ellipses `I... need... you`; hyphenated stretch `ne-e-ed`. Spell numbers (`24/7` → `twenty four seven`); space acronyms (`AI` → `A I` or `A-I`); test unusual words in a 30-second clip; pronunciation is baked in, so fix lyrics first.

## Procedure

1. Concept/hook and emotional core.
2. Adaptation: map syllables/rhyme/stress.
3. Raw material before structure.
4. Draft lyrics.
5. Read/sing aloud; repair meter.
6. Dynamic Suno style description.
7. Lyrics metatags.
8. Generate 3–5 variations as recording takes.
9. Extend/Continue promising sections.
10. Keep good accidents.

Expect ~3–5 generations per good result. Extensions drift; restate genre/mood.

## 10. Lessons

- dynamic arc matters more than genre list; `Whisper to roar to whisper` gives a performance map
- original lines in parody add recognizability/emotional weight
- bridge transforms imagery while retaining emotional function (reflection, shift, revelation)
- monosyllabic hook/tag swaps preserve rhythm while changing meaning
- vocal persona beats any single metatag
- if broken meter hits harder, keep it; feeling matters, craft serves art

## 11. Local/Open-Source Generation

For GPU-based alternatives (heavy, optional):

- `heartmula` — full vocal songs from lyrics + tags, open-source Suno alternative, 8–16GB VRAM: `hermes skills install official/creative/heartmula`
- `audiocraft` — Meta MusicGen instrumental text-to-music + AudioGen sound effects: `hermes skills install official/creative/audiocraft-audio-generation`

The lyric/prompt craft applies to heartmula: bracketed structure tags + comma-separated style tags.

## Pitfalls

- do not name living artists or trademarks in a Suno style prompt; describe genre, instrumentation, voice, and energy instead
- do not hide awkward meter or pronunciation under prose; sing the draft and test a short generated clip
- preserve user intent and recognizable source material when adapting or parodying a work

## Verification

- lyrics can be sung aloud without unintended stumbles; structure/rhyme/stress serves emotion
- parody/adaptation maps original while respecting the concept; intentional originals retained where useful
- Suno prompt describes journey/persona and avoids artist/trademark names
- metatags are 5–8/section, consistent, and in both fields where needed
- pronunciation checked in a short clip; 3–5 variations generated before selecting
