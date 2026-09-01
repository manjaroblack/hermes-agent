---
name: codebase-inspection
description: "Inspect codebases w/ pygount: LOC, languages, ratios."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, Repository]
    related_skills: [github-repo-management]
prerequisites:
  commands: [pygount]
---

# Codebase Inspection with pygount

role: repository-size and composition analyst
do: measure LOC; break down languages/files; compare code/comment ratios; exclude dependency/build trees
inputs: repository path, optional suffix filters, skip-folder policy, output format
outputs: pygount summary or file-level metrics with interpretation
¬: crawl dependency/build directories by default; report Markdown comments as code; infer exact JSON LOC from pygount

## When to Use

- LOC or codebase-size request
- language/file composition breakdown
- code-vs-comment ratio request
- general “how big is this repository?” inspection

## Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## Procedure

### 1. Run the bounded summary

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

Always set `--folders-to-skip`; otherwise dependency trees can make the scan
very slow or hang.

### 2. Tune exclusions

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

### 3. Filter language

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

### 4. Inspect files and choose format

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## Interpret Results

Summary columns:

- **Language**: detected programming language
- **Files**: count for that language
- **Code**: executable/declarative lines
- **Comment**: comments/documentation
- **%**: percentage of total

Pseudo-languages: `__empty__` empty files; `__binary__` binary files;
`__generated__` heuristically generated files; `__duplicate__` identical files;
`__unknown__` unrecognized file types.

## Pitfalls

- omit `.git`, `node_modules`, or `venv` → crawl/hang risk
- Markdown is classified as comments, so code count 0 is expected
- JSON counts can be conservative; use `wc -l` for raw JSON line count
- large monorepo → target languages with `--suffix`

## Verification

- [ ] repository path is the intended root
- [ ] dependency/build exclusions are present
- [ ] selected suffix/output format matches the question
- [ ] interpretation distinguishes code, comments, pseudo-languages, and raw-line caveats