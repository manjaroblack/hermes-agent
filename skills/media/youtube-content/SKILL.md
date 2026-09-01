---
name: youtube-content
description: YouTube transcripts to summaries, threads, blogs.
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [YouTube, Video, Transcripts, Media]
    related_skills: []
---

# YouTube Content

role: transcript fetcher + content transformer
do: normalize video URL/ID; fetch transcript; validate language; chunk; produce requested format; verify output
inputs: YouTube URL/ID, language fallback list, output format, transcript size
outputs: transcript, chapters, summary, chapter summaries, X thread, blog, or timestamped quotes
¬: invent unavailable transcript; silently switch language; summarize >50K characters without overlap/chunking; skip final coherence check

## When to Use

- user shares a YouTube URL/video link
- user asks for transcript or video summary
- user wants chapters, a thread, blog post, or quotes
- content needs extraction/reformatting from a YouTube video

## Setup

Use `uv` in the Hermes-managed environment:

```bash
uv pip install youtube-transcript-api
```

## Helper

`SKILL_DIR` = directory containing this skill. The helper accepts standard
YouTube URLs, `youtu.be`, shorts, embeds, live links, and raw 11-character IDs.

```bash
# JSON output with metadata
uv run python SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
uv run python SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

- **chapters**: topic-shift groups with timestamps
- **summary**: concise 5–10 sentence overview
- **chapter summaries**: chapter list + short paragraph each
- **thread**: numbered Twitter/X posts, each <280 chars
- **blog post**: title, sections, key takeaways
- **quotes**: notable quotes with timestamps

Example chapter shape:

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Procedure

1. Fetch with `--text-only --timestamps` via `uv run python`.
2. Confirm non-empty output and expected language. If empty, retry without
   `--language`; if still empty, report transcripts likely disabled.
3. If >~50K characters, split into overlapping ~40K chunks with 2K overlap;
   summarize chunks, then merge.
4. Transform to requested format; default to summary when unspecified.
5. Re-read result; check coherence, timestamps, completeness.

## Pitfalls

- transcript disabled → tell user; suggest checking subtitles on video page
- private/unavailable → relay error; ask user to verify URL
- no matching language → retry without `--language`; report actual language
- missing dependency → `uv pip install youtube-transcript-api`, then retry

## Verification

- [ ] URL/ID normalized and helper ran
- [ ] transcript non-empty, language behavior reported
- [ ] long transcript chunked with overlap
- [ ] requested/default format constraints met
- [ ] timestamps and final content re-read for coherence/completeness