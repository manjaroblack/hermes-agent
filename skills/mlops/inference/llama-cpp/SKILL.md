---
name: llama-cpp
description: llama.cpp local GGUF inference + HF Hub model discovery.
version: 2.1.2
author: Orchestra Research
license: MIT
dependencies: [llama-cpp-python>=0.2.0]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llama.cpp, GGUF, Quantization, Hugging Face Hub, CPU Inference, Apple Silicon, Edge Deployment, AMD GPUs, Intel GPUs, NVIDIA, URL-first]
---

# llama.cpp + GGUF

role: local GGUF inference + Hugging Face discovery operator
do: discover repo/quant/file; launch `llama-cli`/`llama-server`; call OpenAI-compatible API; use Python bindings; tune quant/hardware
inputs: Hub repo/search URL, hardware RAM/VRAM/backend, quant preference, prompt, context/offload settings
outputs: exact GGUF filename/size/label, launch command, generated text/embeddings, server endpoint
¬: invent repo files/sizes; normalize repo-native quant labels; treat `mmproj` as main model; convert Transformers weights when GGUF already exists; trust generic quant table over HF hardware section

## When to Use

- local CPU, Apple Silicon, CUDA, ROCm, or Intel GPU inference
- find GGUFs for a Hugging Face repo
- build `llama-server`/`llama-cli` command from Hub
- discover llama.cpp-compatible models
- enumerate `.gguf` names/sizes and choose Q4/Q5/Q6/IQ for memory

## Procedure

1. Run Model Discovery Workflow; capture exact repo, local-app/tree URLs, files, sizes.
2. Separate model shards/projectors; preserve repo-native quant labels.
3. Choose quant from target RAM/VRAM + hardware notes; record fallback assumptions.
4. Launch CLI/server/Python path with the selected file; exercise output/API.
5. Report command + sources and complete Verification.

## Model Discovery Workflow

Prefer URL workflows before `hf`, Python, or custom scripts.

1. Search candidates:
   - `https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - add `search=<term>` for family
   - add `num_parameters=min:0,max:24B` (or constraint)
2. Open `https://huggingface.co/<repo>?local-app=llama.cpp`.
3. If visible, treat local-app snippet as source of truth: copy exact
   `llama-server`/`llama-cli` command and recommended quant.
4. Read same URL as page text/HTML; extract `Hardware compatibility`:
   prefer exact labels/sizes; preserve `UD-Q4_K_M`, `IQ4_NL_XL`, etc. If absent
   in fetched source, state that and fall back to tree API + generic guidance.
5. Confirm actual files with
   `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`:
   retain `type=file` paths ending `.gguf`; `path` + `size` are filename/byte
   truth; separate main checkpoints, `mmproj-*.gguf`, and `BF16/` shards.
   Human fallback: `https://huggingface.co/<repo>/tree/main`.
6. If snippet is not text-visible, reconstruct:
   - `llama-server -hf <repo>:<QUANT>`
   - `llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. Suggest Transformers conversion only when repo exposes no GGUF.

## Quick Start

### Install

```bash
# macOS / Linux (simplest)
brew install llama.cpp
```

```bash
winget install llama.cpp
```

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

### Hub launch

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Exact file

Use when tree API has custom naming or local-app command is absent.

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### OpenAI-compatible check

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python Bindings (`llama-cpp-python`)

`pip install llama-cpp-python`; CUDA:
`CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`;
Metal: `CMAKE_ARGS="-DGGML_METAL=on" ...`.

### Generation

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,     # 0 for CPU, 99 to offload everything
    n_threads=8,
)

out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])
```

### Chat + streaming

```python
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3",   # or "chatml", "mistral", etc.
)

resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    max_tokens=256,
)
print(resp["choices"][0]["message"]["content"])

# Streaming
for chunk in llm("Explain quantum computing:", max_tokens=256, stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

### Embeddings

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

Load from Hub:

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## Quant Selection

HF hardware compatibility first; heuristics second:

- general chat → `Q4_K_M`
- code/technical → `Q5_K_M` or `Q6_K` if memory allows
- tight RAM → `Q3_K_M`, `IQ`, or `Q2` only when fit outranks quality
- multimodal → report `mmproj-*.gguf` separately; projector != main model
- preserve labels such as `UD-Q4_K_M`

## Enumerate GGUFs

Return filename, byte/file size, quant label, and main vs auxiliary projector.
Ignore README, BF16 shards, imatrix/calibration artifacts unless requested.
Use `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`.

Example `unsloth/Qwen3.6-35B-A3B-GGUF`: local-app may show `UD-Q4_K_M`,
`UD-Q5_K_M`, `UD-Q6_K`, `Q8_0`; tree API may show exact
`Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` / `Qwen3.6-35B-A3B-Q8_0.gguf` and byte sizes.
Use tree API to map label → exact filename.

## Search URL Shapes

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## Discovery Output

```text
Repo: <repo>
Recommended quant from HF: <label> (<size>)
llama-server: <command>
Other GGUFs:
- <filename> - <size>
- <filename> - <size>
Source URLs:
- <local-app URL>
- <tree API URL>
```

## References

- [hub-discovery.md](references/hub-discovery.md) — URL-first search, GGUF extraction, command reconstruction
- [advanced-usage.md](references/advanced-usage.md) — speculative decoding, batching, grammars, LoRA, multi-GPU, builds, benchmarks
- [quantization.md](references/quantization.md) — Q4/Q5/Q6/IQ tradeoffs, size scaling, imatrix
- [server.md](references/server.md) — Hub server, OpenAI API, Docker, NGINX, monitoring
- [optimization.md](references/optimization.md) — threads, BLAS, offload, batch tuning, benchmarks
- [troubleshooting.md](references/troubleshooting.md) — install/convert/quantize/inference/server, Apple Silicon, debugging

## Resources

- GitHub: https://github.com/ggml-org/llama.cpp
- Hugging Face GGUF + llama.cpp docs: https://huggingface.co/docs/hub/gguf-llamacpp
- Hugging Face Local Apps docs: https://huggingface.co/docs/hub/main/local-apps
- Hugging Face Local Agents docs: https://huggingface.co/docs/hub/agents-local
- Example local-app page: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- Example tree API: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- Example llama.cpp search: https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- License: MIT

## Pitfalls

- Never invent filenames/sizes or normalize repo-native quant labels.
- `mmproj-*.gguf` is a projector, not the main checkpoint; separate BF16 shards too.
- Prefer the repo hardware/local-app guidance over generic quant tables.
- Recommend Transformers conversion only when the repository exposes no GGUF.

## Verification

- [ ] exact repo/local-app/tree URLs inspected
- [ ] hardware section used when visible; fallback disclosed when absent
- [ ] filenames/sizes come from tree API, with projectors/shards separated
- [ ] repo-native quant label preserved
- [ ] launch command matches chosen file/quant and hardware
- [ ] server/API or Python output checked