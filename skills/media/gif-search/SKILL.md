---
name: gif-search
description: Search/download GIFs from Tenor via curl + jq.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [TENOR_API_KEY]
  commands: [curl, jq]
metadata:
  hermes:
    tags: [GIF, Media, Search, Tenor, API]
---

# GIF Search (Tenor API)

role: Tenor GIF search/download operator
do: find reaction or visual GIFs; return URLs/metadata; download selected result
inputs: query, result limit, optional format/safety/locale, `TENOR_API_KEY`
outputs: GIF URLs, metadata, or local `.gif` file
¬: expose API key; omit URL encoding; claim download without checking output

Use the Tenor API through `curl`; parse JSON with `jq`. No extra client tools
are required beyond the declared prerequisites.

## When to Use

- reaction GIF, visual-content, or chat-GIF request
- search by phrase and return one or more Tenor results
- download the top result or a selected result locally
- request dimensions, title, preview, or alternate media formats

## Setup

Store the secret in `${HERMES_HOME:-~/.hermes}/.env`:

```bash
TENOR_API_KEY=your_key_here
```

Get a free key at https://developers.google.com/tenor/guides/quickstart.
The Google Cloud Console Tenor API key is free and has generous rate limits.

## Prerequisites

- `curl` + `jq` (standard on macOS/Linux; verify availability on Windows)
- `TENOR_API_KEY` in the process environment

## Procedure

### 1. Search

```bash
# Search and get GIF URLs
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# Get smaller/preview versions
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.tinygif.url'
```

URL-encode spaces as `+` and special characters as `%XX`. Keep `limit` in the
API range 1–50 (default 20). Use `media_filter` when restricting formats.

### 2. Download

```bash
# Search and download the top result
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

Verify the output path and file before reporting success. `tinygif` is usually
lighter for chat; GIF URLs can be embedded as `![alt](url)`.

### 3. Inspect metadata

```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url, dimensions: .media_formats.gif.dims}'
```

## API Parameters

| Parameter | Description |
|-----------|-------------|
| `q` | Search query (URL-encode spaces as `+`) |
| `limit` | Max results (1-50, default 20) |
| `key` | API key (from `$TENOR_API_KEY` env var) |
| `media_filter` | Filter formats: `gif`, `tinygif`, `mp4`, `tinymp4`, `webm` |
| `contentfilter` | Safety: `off`, `low`, `medium`, `high` |
| `locale` | Language: `en_US`, `es`, `fr`, etc. |

## Media Formats

Each result exposes formats under `.media_formats`:

| Format | Use case |
|--------|----------|
| `gif` | Full quality GIF |
| `tinygif` | Small preview GIF |
| `mp4` | Video version (smaller file size) |
| `tinymp4` | Small preview video |
| `webm` | WebM video |
| `nanogif` | Tiny thumbnail |

## Pitfalls

- API key belongs in the environment/secret store, never output or URL logs.
- Query spaces/special characters require URL encoding.
- Use `tinygif` when chat payload size matters.
- Do not claim a file exists until the download path is checked.

## Verification

- [ ] `TENOR_API_KEY`, `curl`, and `jq` are available.
- [ ] Search response contains the requested result URLs.
- [ ] Metadata fields match the selected result when reported.
- [ ] Downloaded file exists at the stated path and is the intended format.