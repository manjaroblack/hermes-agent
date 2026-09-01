---
name: serving-llms-vllm
description: "vLLM: high-throughput LLM serving, OpenAI API, quantization."
version: 1.0.1
author: Orchestra Research
license: MIT
dependencies: [vllm, torch, transformers]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [vLLM, Inference Serving, PagedAttention, Continuous Batching, High Throughput, Production, OpenAI API, Quantization, Tensor Parallelism]

---

# vLLM High-Performance Serving

role: LLM serving and inference operator
do: install/launch OpenAI-compatible server; run offline batches; tune PagedAttention, batching, cache, quantization, tensor/speculative parallelism; monitor/fix deployment
inputs: model, GPU count/memory, traffic target, context length, quantization, port/host, prompts/data
outputs: API/server, generated outputs, benchmark metrics, deployment diagnosis
¬: expose `0.0.0.0` without network controls; call target met without measurement; use model/quant/GPU settings not verified; rerun failed CI-style operations blindly

## When to Use

- production LLM API or multi-user chatbot
- OpenAI-compatible endpoint with high throughput/low latency
- large model in limited GPU memory
- offline batch inference
- AWQ/GPTQ/FP8 or tensor parallel deployment

## Procedure

1. Pin model access, GPU topology/memory, traffic goal, context, and exposure boundary.
2. Install + exercise Quick Start; choose production API, offline batch, or quantized workflow.
3. Tune measured bottlenecks only; record TTFT, throughput, utilization, and OOM state.
4. Diagnose Pitfalls with current flags; compare quantized quality to baseline.
5. Verify API/batch behavior and target metrics on the actual hardware.

vLLM uses PagedAttention (block KV cache) + continuous batching; the original
guide reports up to 24× throughput over standard Transformers.

## Quick Start

Install:

```bash
pip install vllm
```

Offline:

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Meta-Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)

outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

OpenAI-compatible server:

```bash
vllm serve meta-llama/Meta-Llama-3-8B-Instruct

# Query with OpenAI SDK
python -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Meta-Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
"
```

## Workflow 1: Production API

```
Deployment Progress:
- [ ] Step 1: Configure server settings
- [ ] Step 2: Test with limited traffic
- [ ] Step 3: Enable monitoring
- [ ] Step 4: Deploy to production
- [ ] Step 5: Verify performance metrics
```

### Configure

```bash
# For 7B-13B models on single GPU
vllm serve meta-llama/Meta-Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000

# For 30B-70B models with tensor parallelism
vllm serve meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --quantization awq \
  --port 8000

# For production with caching (Prometheus metrics are exposed
# automatically at /metrics on the API port)
vllm serve meta-llama/Meta-Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --port 8000 \
  --host 0.0.0.0
```

### Load-test before production

Target: TTFT <500 ms and throughput >100 req/s (or the user's stated target).

```bash
# Install load testing tool
pip install locust

# Create test_load.py with sample requests
# Run: locust -f test_load.py --host http://localhost:8000
```

### Monitor

Metrics are at `/metrics` on default API port 8000:

```bash
curl http://localhost:8000/metrics | grep vllm
```

Track `vllm:time_to_first_token_seconds`, `vllm:num_requests_running`,
`vllm:gpu_cache_usage_perc`.

### Deploy

```bash
# Run vLLM in Docker
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching
```

Verify TTFT <500 ms for short prompts, throughput target, GPU utilization
>80%, and no OOM logs.

## Workflow 2: Offline Batch

```
Batch Processing:
- [ ] Step 1: Prepare input data
- [ ] Step 2: Configure LLM engine
- [ ] Step 3: Run batch inference
- [ ] Step 4: Process results
```

Prepare:

```python
# Load prompts from file
prompts = []
with open("prompts.txt") as f:
    prompts = [line.strip() for line in f]

print(f"Loaded {len(prompts)} prompts")
```

Configure:

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    tensor_parallel_size=2,  # Use 2 GPUs
    gpu_memory_utilization=0.9,
    max_model_len=4096
)

sampling = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=512,
    stop=["</s>", "\n\n"]
)
```

Run; vLLM batches internally:

```python
# Process all prompts in one call
outputs = llm.generate(prompts, sampling)

# vLLM handles batching internally
# No need to manually chunk prompts
```

Process/save:

```python
# Extract generated text
results = []
for output in outputs:
    prompt = output.prompt
    generated = output.outputs[0].text
    results.append({
        "prompt": prompt,
        "generated": generated,
        "tokens": len(output.outputs[0].token_ids)
    })

# Save to file
import json
with open("results.jsonl", "w") as f:
    for result in results:
        f.write(json.dumps(result) + "\n")

print(f"Processed {len(results)} prompts")
```

## Workflow 3: Quantized Serving

```
Quantization Setup:
- [ ] Step 1: Choose quantization method
- [ ] Step 2: Find or create quantized model
- [ ] Step 3: Launch with quantization flag
- [ ] Step 4: Verify accuracy
```

Methods: AWQ (70B/minimal loss), GPTQ (broad support/compression), FP8
(fastest on H100). Find pre-quantized models on Hugging Face:

```bash
# Search for AWQ models
# Example: TheBloke/Llama-2-70B-AWQ
```

Launch:

```bash
# Using pre-quantized model
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95

# Results: 70B model in ~40GB VRAM
```

Check task-specific quality against unquantized output:

```python
# Compare quantized vs non-quantized responses
# Verify task-specific performance unchanged
```

## Choose vLLM vs Alternatives

vLLM: production APIs (100+ req/s), OpenAI endpoints, limited memory, multi-user,
low latency + high throughput. Alternatives: `llama.cpp` CPU/edge/single-user;
Hugging Face Transformers research/prototyping/one-off; TensorRT-LLM NVIDIA-only
maximum performance; Text-Generation-Inference for the Hugging Face ecosystem.

## Pitfalls

### OOM loading

```bash
vllm serve MODEL \
  --gpu-memory-utilization 0.7 \
  --max-model-len 4096
```

```bash
vllm serve MODEL --quantization awq
```

### Slow TTFT (>1 s)

```bash
vllm serve MODEL --enable-prefix-caching
```

```bash
vllm serve MODEL --enable-chunked-prefill
```

### Model not found

```bash
vllm serve MODEL --trust-remote-code
```

### Low throughput (<50 req/s)

```bash
vllm serve MODEL --max-num-seqs 512
```

Check `nvidia-smi`; GPU utilization should exceed 80%.

### Inference slower than expected

Use power-of-two GPU tensor parallelism:

```bash
vllm serve MODEL --tensor-parallel-size 4  # Not 3
```

Speculative decoding uses JSON config; `--speculative-model` was removed:

```bash
vllm serve MODEL \
  --speculative-config '{"model": "DRAFT_MODEL", "num_speculative_tokens": 5, "method": "draft_model"}'
```

## References

- [references/server-deployment.md](references/server-deployment.md): Docker, Kubernetes, load balancing
- [references/optimization.md](references/optimization.md): PagedAttention, continuous batching, benchmarks
- [references/quantization.md](references/quantization.md): AWQ/GPTQ/FP8, preparation, accuracy
- [references/troubleshooting.md](references/troubleshooting.md): errors, debugging, performance

## Hardware

- small 7B–13B: 1× A10 (24 GB) or A100 (40 GB)
- medium 30B–40B: 2× A100 (40 GB), tensor parallel
- large 70B+: 4× A100 (40 GB) or 2× A100 (80 GB), AWQ/GPTQ
- NVIDIA primary; AMD ROCm, Intel GPUs, TPUs supported

## Resources

- Official docs: https://docs.vllm.ai
- GitHub: https://github.com/vllm-project/vllm
- Paper: “Efficient Memory Management for Large Language Model Serving with PagedAttention” (SOSP 2023)
- Community: https://discuss.vllm.ai

## Verification

- [ ] dependency/runtime and model access verified
- [ ] server/API or batch path exercised
- [ ] target TTFT/throughput/GPU/OOM metrics measured, not assumed
- [ ] quantization/tensor-parallel settings match hardware
- [ ] monitoring endpoint and relevant metrics checked
- [ ] failures diagnosed from logs and config, not guessed