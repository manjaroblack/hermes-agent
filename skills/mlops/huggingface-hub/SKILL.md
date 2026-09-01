---
name: huggingface-hub
description: "HuggingFace hf CLI: search/download/upload models, datasets."
version: 1.0.1
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face CLI (`hf`)

role: Hugging Face Hub CLI operator
do: inspect env/version; authenticate; manage model/dataset/Space repos; query datasets/models; operate endpoints/jobs/buckets/cache/webhooks/collections; extend CLI/skills
inputs: Hub repo IDs, local paths, token, dataset SQL, endpoint/job/storage parameters
outputs: downloaded/uploaded assets, repo refs, query/results metadata, compute/storage state
¬: use deprecated `huggingface-cli`; print tokens; delete/move repos without explicit target/approval; run raw dataset SQL without scope review

## When to Use

- search/download/upload Hub models or datasets
- create, duplicate, move, branch/tag, or delete Hub repositories
- inspect datasets, parquet URLs, models, papers, discussions/PRs
- deploy/manage Inference Endpoints or Jobs; operate Spaces
- manage buckets, cache, webhooks, collections, extensions, or skills

## Procedure

1. Install/verify modern `hf`; authenticate through stored `HF_TOKEN` or prompt.
2. Resolve exact repo ID/type, local path, revision, and intended mutation.
3. Choose Core Commands or Specialized Operations; request approval for destructive work.
4. Use JSON/quiet output for automation; preserve returned IDs and refs.
5. Read back repo/compute/storage state and complete Verification.

## Prerequisites + Auth

Install:

`curl -LsSf https://hf.co/cli/install.sh | bash -s`

`hf` replaces deprecated `huggingface-cli`. Use `HF_TOKEN` or `--token`; use
the token page https://huggingface.co/settings/tokens for session tokens.

## Core Commands

### General

- `hf download REPO_ID`: download Hub files
- `hf upload REPO_ID`: upload files/folders; recommended for single-commit and resumable large-directory uploads
- `hf upload-large-folder REPO_ID LOCAL_PATH`: deprecated; use `hf upload`
- `hf sync`: sync local directory and bucket
- `hf env` / `hf version`: environment/version details

### Authentication (`hf auth`)

- `login` / `logout`: manage token sessions
- `list` / `switch`: manage multiple stored tokens
- `whoami`: current account

### Repository (`hf repos`)

- `create` / `delete`: create or permanently remove repos
- `duplicate`: copy model, dataset, or Space to a new ID
- `move`: transfer between namespaces
- `branch` / `tag`: Git-like refs
- `delete-files`: remove matching files

## Specialized Operations

### Datasets + models

- datasets: `hf datasets list`, `info`, `parquet` (parquet URLs)
- SQL: `hf datasets sql SQL` runs raw DuckDB SQL against dataset parquet URLs
- models: `hf models list`, `info`
- papers: `hf papers ls` (daily papers)

### Discussions + PRs (`hf discussions`)

`list`, `create`, `info`, `comment`, `close`, `reopen`, `rename`, `diff`,
`merge`; `diff` views changes and `merge` finalizes a PR.

### Infrastructure + compute

- Endpoints: `deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`
- Jobs: compute tasks; `hf jobs uv` runs Python with inline dependencies;
  `stats` monitors resources
- Spaces: interactive apps; `dev-mode` + `hot-reload` avoid full Python restarts

### Storage + automation

- Buckets: S3-like `create`, `cp`, `mv`, `rm`, `sync`
- Cache: `list`, `prune` detached revisions, `verify` checksums
- Webhooks: `create`, `watch`, `enable`, `disable`
- Collections: `add-item`, `update`, `list`

## Global Flags + Extensions

- `--format json`: machine-readable automation output
- `-q` / `--quiet`: IDs only
- `hf extensions install REPO_ID`: install a GitHub-backed extension
- `hf skills add`: manage AI assistant skills

## Pitfalls

- `huggingface-cli` and `hf upload-large-folder` are deprecated; use `hf` + `hf upload`.
- Never print tokens; scope repo IDs, paths, types, revisions, and namespaces exactly.
- Delete/move, cache prune, bucket mutation, webhook changes, and compute jobs need explicit scope/approval.
- JSON/quiet output improves parsing but does not prove mutation success; read state back.

## Verification

- [ ] `hf --help`/`hf version` confirms modern CLI
- [ ] auth uses `HF_TOKEN` or `--token` without token output
- [ ] repo ID/path and mutation are explicitly scoped
- [ ] downloads/uploads or management commands report expected IDs/state
- [ ] destructive operations are confirmed and read back