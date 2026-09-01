---
name: heartmula
description: "HeartMuLa: Suno-like song generation from lyrics + tags."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [music, audio, generation, ai, heartmula, heartcodec, lyrics, songs]
    related_skills: [audiocraft-audio-generation, songwriting-and-ai-music]
---

# HeartMuLa — Open-Source Music Generation

role: HeartMuLa local music-generation operator
do: install heartlib; create Python 3.10 env; patch compatibility; download checkpoints; format lyrics/tags; choose GPU/CPU; generate MP3; verify output
inputs: lyrics file, comma-separated tags, model checkpoint, devices/dtypes, duration, output path
outputs: 48kHz stereo 128kbps MP3 song, model/download status, diagnostics
¬: use unpatched incompatible dependencies; use bf16 for HeartCodec; hide CPU slowness/RAM cost; expose API/credentials; claim GPU acceleration on unsupported hardware

HeartMuLa is an Apache-2.0 open-source model family for full-song generation from lyrics + tags, with multilingual support. Components: **HeartMuLa** music LM (3B/7B), **HeartCodec** 12.5Hz codec, **HeartTranscriptor** Whisper lyrics transcription, **HeartCLAP** audio-text alignment.

## When to Use

- local/offline song generation from lyrics and tags
- open-source Suno-like workflow
- questions about HeartMuLa, heartlib, or AI music

## Prerequisites

- NVIDIA GPU preferred: minimum 8GB VRAM with `--lazy_load true`; 16GB+ recommended; 3B lazy peak ~6.2GB
- multi-GPU: `--mula_device cuda:0 --codec_device cuda:1`
- CPU fallback: `--mula_device cpu --codec_device cpu`; ~12GB+ free RAM and 30-60+ min/song expected
- Python 3.10 and `uv`

## Procedure

### 1. Clone and install

```bash
cd ~/  # or desired directory
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. Resolve dependency compatibility

As of Feb 2026, upgrade packages whose pins conflict with newer `pyarrow`/`huggingface-hub`:

```bash
uv pip install --upgrade datasets
uv pip install --upgrade transformers
```

### 3. Apply required source patches

**Patch 1:** `src/heartlib/heartmula/modeling_heartmula.py`, `HeartMuLa.setup_caches`; after the `reset_caches` try/except and before `with device:` add:

```python
# Re-initialize RoPE caches that were skipped during meta-device loading
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

Reason: `from_pretrained` constructs on meta device; `Llama3ScaledRoPE.rope_init()` skips cache construction there and otherwise never rebuilds after weights reach the real device.

**Patch 2:** `src/heartlib/pipelines/music_generation.py`; add `ignore_mismatched_sizes=True` to both `HeartCodec.from_pretrained()` calls (eager `__init__` and lazy `codec` property). Checkpoint `initted` is `[1]` while model buffer is `[]`; same data, scalar vs 0-D tensor.

### 4. Download checkpoints

```bash
cd heartlib  # project root
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

The three downloads can run in parallel; total size is several GB.

### 5. Check CUDA/CPU

CUDA defaults: `--mula_device cuda --codec_device cuda`. Installed `torch==2.4.1` includes CUDA 12.1; `torchtune` may display `0.4.0+cpu` metadata while still using PyTorch CUDA. Look for `CUDA memory` lines such as `CUDA memory before unloading: 6.20 GB`.

Without NVIDIA GPU, use CPU flags only with explicit user expectation of extreme slowness; recommend Google Colab T4, Lambda Labs, or https://heartmula.github.io/ instead when appropriate.

### 6. Generate

```bash
cd heartlib
. .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="$ASSETS_DIR/lyrics.txt" \
  --tags="$ASSETS_DIR/tags.txt" \
  --save_path="$ASSETS_DIR/output.mp3" \
  --lazy_load true
```

Tags are comma-separated without spaces:

```
piano,happy,wedding,synthesizer,romantic
```

Lyrics use bracketed sections:

```
[Intro]

[Verse]
Your lyrics here...

[Chorus]
Chorus lyrics...

[Bridge]
Bridge lyrics...

[Outro]
```

## Quick Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Max length in ms (240s = 4 min) |
| `--topk` | 50 | Top-k sampling |
| `--temperature` | 1.0 | Sampling temperature |
| `--cfg_scale` | 1.5 | Classifier-free guidance scale |
| `--lazy_load` | false | Load/unload models on demand (saves VRAM) |
| `--mula_dtype` | bfloat16 | Dtype for HeartMuLa (bf16 recommended) |
| `--codec_dtype` | float32 | Dtype for HeartCodec (fp32 recommended for quality) |

Performance: RTF≈1.0; 4-minute song≈4 minutes on expected GPU path; output MP3, 48kHz stereo, 128kbps.

## Pitfalls

- Do **not** use bf16 for HeartCodec; it degrades audio. Keep fp32.
- Tags can be ignored (known issue #90); lyrics dominate; experiment with tag order.
- Triton is unavailable on macOS; GPU acceleration is Linux/CUDA-only.
- RTX 5080 incompatibility is reported upstream.
- Manual dependency upgrades and both source patches are required for the described newer-package setup.
- CPU generation is extremely slow and RAM-heavy; suggest cloud GPU/online demo rather than hiding the trade-off.

## Verification

- `python --version` reports 3.10 environment
- all three checkpoints exist under `ckpt/`
- patched setup reaches a real device and codec loads without shape error
- generation writes non-empty `$ASSETS_DIR/output.mp3`
- output is 48kHz stereo 128kbps where the pipeline reports defaults
- CUDA log shows expected memory on GPU; CPU mode is explicitly labeled slow

## Links

- Repo: https://github.com/HeartMuLa/heartlib
- Models: https://huggingface.co/HeartMuLa
- Paper: https://arxiv.org/abs/2601.10547
- License: Apache-2.0
