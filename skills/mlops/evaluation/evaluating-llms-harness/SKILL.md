---
name: evaluating-llms-harness
description: "lm-eval-harness: benchmark LLMs (MMLU, GSM8K, etc.)."
version: 1.0.1
author: Orchestra Research
license: MIT
dependencies: [lm-eval, transformers, vllm]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Evaluation, LM Evaluation Harness, Benchmarking, MMLU, HumanEval, GSM8K, EleutherAI, Model Quality, Academic Benchmarks, Industry Standard]

---

# lm-evaluation-harness

role: reproducible LLM benchmark operator
do: install harness; select tasks; configure HF/vLLM/API model; run/evaluate; track checkpoints; compare models; diagnose results
inputs: model/checkpoint/tokenizer, task suite, few-shot count, device/batch, output path, safety confirmation
outputs: standardized metrics, stderr/config/sample artifacts, curves/comparison table
¬: compare runs with mismatched task/few-shot/tokenizer; execute generated code without explicit flag; call slow/failed run complete; report only aggregate without config

## When to Use

- benchmark model quality or compare models
- report academic/standardized results
- track training progress across checkpoints
- evaluate Hugging Face, vLLM, or API models
- use MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag, ARC, MBPP

## Procedure

1. Install + list tasks; pin model, tokenizer, task suite, few-shot, and output.
2. Choose standard benchmark, checkpoint-progress, comparison, or vLLM workflow.
3. Run with recorded device/batch settings; save config, metrics, stderr, samples.
4. Diagnose Common Issues; use unsafe-code confirmation only when explicitly intended.
5. Compare only matching task/config semantics; complete Verification.

The harness covers 60+ academic benchmarks and is used by EleutherAI,
Hugging Face, and major labs; supports Hugging Face, vLLM, and APIs.

## Quick Start

```bash
pip install lm-eval
```

```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 \
  --batch_size 8
```

```bash
lm-eval ls tasks
```

## Workflow 1: Standard Benchmarks

```
Benchmark Evaluation:
- [ ] Step 1: Choose benchmark suite
- [ ] Step 2: Configure model
- [ ] Step 3: Run evaluation
- [ ] Step 4: Analyze results
```

Task families:

- reasoning: MMLU (57 subjects/multiple choice), GSM8K, HellaSwag,
  TruthfulQA, ARC
- code: HumanEval (164 Python problems), MBPP
- release suite:

```bash
--tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge
```

Configure models:

```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,dtype=bfloat16 \
  --tasks mmlu \
  --device cuda:0 \
  --batch_size auto  # Auto-detect optimal batch size
```

```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,load_in_4bit=True \
  --tasks mmlu \
  --device cuda:0
```

```bash
lm_eval --model hf \
  --model_args pretrained=/path/to/my-model,tokenizer=/path/to/tokenizer \
  --tasks mmlu \
  --device cuda:0
```

Run:

```bash
# Full MMLU evaluation (57 subjects)
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --num_fewshot 5 \  # 5-shot evaluation (standard)
  --batch_size 8 \
  --output_path results/ \
  --log_samples  # Save individual predictions

# Multiple benchmarks at once
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge \
  --num_fewshot 5 \
  --batch_size 8 \
  --output_path results/llama2-7b-eval.json
```

Expected result shape:

```json
{
  "results": {
    "mmlu": {
      "acc": 0.459,
      "acc_stderr": 0.004
    },
    "gsm8k": {
      "exact_match": 0.142,
      "exact_match_stderr": 0.006
    },
    "hellaswag": {
      "acc_norm": 0.765,
      "acc_norm_stderr": 0.004
    }
  },
  "config": {
    "model": "hf",
    "model_args": "pretrained=meta-llama/Llama-2-7b-hf",
    "num_fewshot": 5
  }
}
```

## Workflow 2: Training Progress

```
Training Progress Tracking:
- [ ] Step 1: Set up periodic evaluation
- [ ] Step 2: Choose quick benchmarks
- [ ] Step 3: Automate evaluation
- [ ] Step 4: Plot learning curves
```

Evaluate checkpoints every N steps:

```bash
#!/bin/bash
# eval_checkpoint.sh

CHECKPOINT_DIR=$1
STEP=$2

lm_eval --model hf \
  --model_args pretrained=$CHECKPOINT_DIR/checkpoint-$STEP \
  --tasks gsm8k,hellaswag \
  --num_fewshot 0 \  # 0-shot for speed
  --batch_size 16 \
  --output_path results/step-$STEP.json
```

Quick: HellaSwag ~10 min/1 GPU, GSM8K ~5 min, PIQA ~2 min. Avoid frequent
full MMLU (~2 h/57 subjects) and HumanEval (code execution).

Training-loop integration:

```python
# In training loop
if step % eval_interval == 0:
    model.save_pretrained(f"checkpoints/step-{step}")

    # Run evaluation
    os.system(f"./eval_checkpoint.sh checkpoints step-{step}")
```

```python
from pytorch_lightning import Callback

class EvalHarnessCallback(Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        step = trainer.global_step
        checkpoint_path = f"checkpoints/step-{step}"

        # Save checkpoint
        trainer.save_checkpoint(checkpoint_path)

        # Run lm-eval
        os.system(f"lm_eval --model hf --model_args pretrained={checkpoint_path} ...")
```

Plot curves:

```python
import json
import matplotlib.pyplot as plt

# Load all results
steps = []
mmlu_scores = []

for file in sorted(glob.glob("results/step-*.json")):
    with open(file) as f:
        data = json.load(f)
        step = int(file.split("-")[1].split(".")[0])
        steps.append(step)
        mmlu_scores.append(data["results"]["mmlu"]["acc"])

# Plot
plt.plot(steps, mmlu_scores)
plt.xlabel("Training Step")
plt.ylabel("MMLU Accuracy")
plt.title("Training Progress")
plt.savefig("training_curve.png")
```

## Workflow 3: Compare Models

```
Model Comparison:
- [ ] Step 1: Define model list
- [ ] Step 2: Run evaluations
- [ ] Step 3: Generate comparison table
```

Model list:

```bash
# models.txt
meta-llama/Llama-2-7b-hf
meta-llama/Llama-2-13b-hf
mistralai/Mistral-7B-v0.1
microsoft/phi-2
```

Evaluate:

```bash
#!/bin/bash
# eval_all_models.sh

TASKS="mmlu,gsm8k,hellaswag,truthfulqa"

while read model; do
    echo "Evaluating $model"

    # Extract model name for output file
    model_name=$(echo $model | sed 's/\//-/g')

    lm_eval --model hf \
      --model_args pretrained=$model,dtype=bfloat16 \
      --tasks $TASKS \
      --num_fewshot 5 \
      --batch_size auto \
      --output_path results/$model_name.json

done < models.txt
```

Generate table:

```python
import json
import pandas as pd

models = [
    "meta-llama-Llama-2-7b-hf",
    "meta-llama-Llama-2-13b-hf",
    "mistralai-Mistral-7B-v0.1",
    "microsoft-phi-2"
]

tasks = ["mmlu", "gsm8k", "hellaswag", "truthfulqa"]

results = []
for model in models:
    with open(f"results/{model}.json") as f:
        data = json.load(f)
        row = {"Model": model.replace("-", "/")}
        for task in tasks:
            # Get primary metric for each task
            metrics = data["results"][task]
            if "acc" in metrics:
                row[task.upper()] = f"{metrics['acc']:.3f}"
            elif "exact_match" in metrics:
                row[task.upper()] = f"{metrics['exact_match']:.3f}"
        results.append(row)

df = pd.DataFrame(results)
print(df.to_markdown(index=False))
```

```
| Model                  | MMLU  | GSM8K | HELLASWAG | TRUTHFULQA |
|------------------------|-------|-------|-----------|------------|
| meta-llama/Llama-2-7b  | 0.459 | 0.142 | 0.765     | 0.391      |
| meta-llama/Llama-2-13b | 0.549 | 0.287 | 0.801     | 0.430      |
| mistralai/Mistral-7B   | 0.626 | 0.395 | 0.812     | 0.428      |
| microsoft/phi-2        | 0.560 | 0.613 | 0.682     | 0.447      |
```

## Workflow 4: vLLM Backend

vLLM is documented here as 5–10× faster for inference.

```
vLLM Evaluation:
- [ ] Step 1: Install vLLM
- [ ] Step 2: Configure vLLM backend
- [ ] Step 3: Run evaluation
```

```bash
pip install vllm
```

```bash
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=1,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks mmlu \
  --batch_size auto
```

```bash
# Standard HF: ~2 hours for MMLU on 7B model
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --batch_size 8

# vLLM: ~15-20 minutes for MMLU on 7B model
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=2 \
  --tasks mmlu \
  --batch_size auto
```

## Choose Alternatives

Use harness for standardized/reproducible academic comparison and progress
tracking. Use HELM for fairness/efficiency/calibration; AlpacaEval for
instruction-following LLM judges; MT-Bench for multi-turn conversation; custom
scripts for domain-specific evaluation.

## Pitfalls

### Too slow

```bash
lm_eval --model vllm \
  --model_args pretrained=model-name,tensor_parallel_size=2
```

```bash
--num_fewshot 0  # Instead of 5
```

```bash
--tasks mmlu_stem  # Only STEM subjects
```

### OOM

```bash
--batch_size 1  # Or --batch_size auto
```

```bash
--model_args pretrained=model-name,load_in_8bit=True
```

```bash
--model_args pretrained=model-name,device_map=auto,offload_folder=offload
```

### Results differ

```bash
--num_fewshot 5  # Most papers use 5-shot
```

```bash
--tasks mmlu  # Not mmlu_direct or mmlu_fewshot
```

```bash
--model_args pretrained=model-name,tokenizer=same-model-name
```

### HumanEval/MBPP code execution

Explicitly pass the safety flag:

```bash
lm_eval --model hf \
  --model_args pretrained=model-name \
  --tasks humaneval \
  --confirm_run_unsafe_code  # Required to run tasks that execute generated code
```

Without it, lm-eval refuses rather than silently skipping code execution.

## References

- [references/benchmark-guide.md](references/benchmark-guide.md): 60+ tasks, measures, interpretation
- [references/custom-tasks.md](references/custom-tasks.md): domain-specific tasks
- [references/api-evaluation.md](references/api-evaluation.md): OpenAI, Anthropic, other APIs
- [references/distributed-eval.md](references/distributed-eval.md): data/tensor parallel evaluation

## Hardware + Timing

- GPU: NVIDIA CUDA 11.8+; CPU works but is very slow
- VRAM: 7B = 16 GB bf16/8 GB 8-bit; 13B = 28 GB bf16/14 GB 8-bit; 70B = multi-GPU or quantized
- 7B on one A100: HellaSwag 10 min, GSM8K 5 min, full MMLU 2 h, HumanEval 20 min

## Resources

- GitHub: https://github.com/EleutherAI/lm-evaluation-harness
- Docs: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs
- Task library: 60+ tasks including MMLU, GSM8K, HumanEval, TruthfulQA, HellaSwag, ARC, WinoGrande, etc.
- Leaderboard: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard

## Verification

- [ ] task suite, few-shot count, model, tokenizer, device, batch, and output path recorded
- [ ] standard metrics + stderr/config/samples saved
- [ ] comparable runs use matching task/config semantics
- [ ] code-executing tasks used `--confirm_run_unsafe_code`
- [ ] vLLM/HF performance claims measured on target hardware
- [ ] failures distinguish OOM, task mismatch, tokenizer mismatch, and execution refusal