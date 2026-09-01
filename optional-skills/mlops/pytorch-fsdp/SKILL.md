---
name: pytorch-fsdp
description: Fully sharded data-parallel training for large models.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [torch>=2.0, transformers]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Distributed Training, PyTorch, FSDP, Data Parallel, Sharding, Mixed Precision, CPU Offloading, FSDP2, Large-Scale Training]

---

# Pytorch-Fsdp Skill

role: PyTorch FSDP large-model distributed-training operator
do: load linked FSDP patterns; wrap modules; choose sharding/mixed precision/offload; launch distributed training; checkpoint/load/reshard; inspect memory
inputs: PyTorch/Transformers model; process/GPU topology; auto-wrap policy; sharding strategy; precision/offload; checkpoint format/path
outputs: distributed checkpoint; training metrics; memory/throughput profile; load/reshard result; configuration guidance
¬: reconstruct APIs from stale snippets; wrap after optimizer creation; change topology without checkpoint plan; expose model data; claim scale without a real run

## When to Use

This skill should be triggered when:
- Working with pytorch-fsdp
- Asking about pytorch-fsdp features or APIs
- Implementing pytorch-fsdp solutions
- Debugging pytorch-fsdp code
- Learning pytorch-fsdp best practices


Assistance with pytorch-fsdp development, generated from official documentation.

## Procedure
- follow the selected workflow below; preserve documented commands, APIs, and version constraints

## Quick Reference

The full common-patterns catalog (~157k chars of runnable FSDP snippets) lives in `references/common-patterns.md` — load it with `read_file` when you need wrapping, sharding-strategy, checkpoint, or mixed-precision examples. Start there rather than reconstructing FSDP incantations from memory.

## Reference Files

This skill includes comprehensive documentation in `references/`:

- other.md - Other documentation

Use `read_file` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Pitfalls
- The runnable common-patterns catalog is in `references/common-patterns.md`; read it for current wrapping/checkpoint examples.
- FSDP wrapping, optimizer creation, state-dict type, and distributed initialization order matter.
- CPU offload and sharding reduce memory with communication/performance trade-offs.
- Checkpoint state-dict and world-size changes require tested reshard/load paths.

## Verification
- resolve the installed PyTorch/Transformers FSDP API and reference examples
- run a bounded multi-process smoke test with a tiny model
- save/load a checkpoint and inspect memory plus synchronization errors

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
