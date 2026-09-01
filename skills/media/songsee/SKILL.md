---
name: songsee
description: Audio spectrograms/features (mel, chroma, MFCC) via CLI.
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Audio, Visualization, Spectrogram, Music, Analysis]
    homepage: https://github.com/steipete/songsee
prerequisites:
  commands: [songsee]
---

# songsee

role: audio-feature visualization operator
do: render spectrogram/mel/chroma/HPSS/self-similarity/loudness/tempogram/MFCC/flux plots; slice or stream audio
inputs: audio path/stdin, visualization list, style/dimensions/FFT/frequency/time/output flags
outputs: PNG/JPG image for inspection or pipeline use
¬: assume non-WAV/MP3 decoding without `ffmpeg`; omit output path when artifact must persist

## When to Use

- inspect or compare audio outputs
- generate a spectrogram or multi-panel feature grid
- debug synthesis/audio processing
- document an audio pipeline

## Procedure

1. Verify `songsee`; install it and optional `ffmpeg` when required.
2. Select input, time slice, visualization panels, FFT/frequency/style settings.
3. Set explicit output path for persistent artifacts; run the matching command.
4. Inspect the rendered image and report path + selected visualization settings.

## Prerequisites

Requires [Go](https://go.dev/doc/install):

```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

Optional: `ffmpeg` for formats beyond WAV/MP3.

## Quick Start

```bash
# Basic spectrogram
songsee track.mp3

# Save to specific file
songsee track.mp3 -o spectrogram.png

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice (start at 12.5s, 8s duration)
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

## Visualization Types

Pass comma-separated values to `--viz`; multiple panels render as one grid.

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

## Flags

| Flag | Description |
|------|-------------|
| `--viz` | Visualization types (comma-separated) |
| `--style` | Color palette: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Output image dimensions |
| `--window` / `--hop` | FFT window and hop size |
| `--min-freq` / `--max-freq` | Frequency range filter |
| `--start` / `--duration` | Time slice of the audio |
| `--format` | Output format: `jpg` or `png` |
| `-o` | Output file path |

## Pitfalls

- WAV/MP3 decode natively; other formats need `ffmpeg`.
- Output is an image; use `vision_analyze` for automated visual/audio review.
- `--viz` values are comma-separated, not repeated flags.

## Verification

- [ ] `songsee` is installed and input decodes
- [ ] requested visualizations, slice, style, and format are set
- [ ] output image exists at the stated path
- [ ] image can be inspected for the requested analysis