---
name: unsloth
description: "Unsloth: 2-5x faster LoRA/QLoRA fine-tuning, less VRAM."
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [unsloth, torch, transformers, trl, datasets, peft]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Fine-Tuning, Unsloth, Fast Training, LoRA, QLoRA, Memory-Efficient, Optimization, Llama, Mistral, Gemma, Qwen]

---

# Unsloth Skill

role: Unsloth LoRA/QLoRA fine-tuning operator
do: install/check Unsloth; select supported model; configure LoRA/QLoRA dataset/trainer; run/save training; inspect metrics; export adapter or merged model
inputs: base model; instruction/preference dataset; LoRA rank/targets; batch/sequence/LR/epochs; GPU and output path
outputs: adapter or merged checkpoint; tokenizer; training logs/metrics; reproducible config; VRAM/compatibility status
¬: train before checking CUDA/VRAM; treat placeholder patterns as a complete recipe; overwrite base weights; expose Hub tokens; claim speed/quality without a benchmark

## When to Use

This skill should be triggered when:
- Working with unsloth
- Asking about unsloth features or APIs
- Implementing unsloth solutions
- Debugging unsloth code
- Learning unsloth best practices


Assistance with unsloth development, generated from official documentation.

## Procedure
- follow the selected workflow below; preserve documented commands, APIs, and version constraints

## Quick Reference

### Common Patterns

*Quick reference patterns will be added as you use the skill.*

## Reference Files

This skill includes full documentation in `references/`:

- llms-txt.md - Llms-Txt documentation

Use `read_file` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Pitfalls
- The quick-reference section is intentionally a placeholder; load linked reference files for detailed API guidance.
- Check Unsloth, PyTorch, Transformers, TRL, and CUDA compatibility before a long run.
- Use QLoRA, smaller sequence/batch settings, or gradient accumulation when VRAM is insufficient.
- Save adapters/checkpoints frequently and validate on held-out data before merging.

## Verification
- confirm imports and the selected model/dataset load
- run a bounded smoke-training step and inspect loss/log output
- reload the saved adapter/checkpoint and verify inference

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information

<!-- Trigger re-upload 1763621536 -->
