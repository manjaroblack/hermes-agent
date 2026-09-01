---
name: nano-pdf
description: Edit text in existing PDFs via natural-language prompts.
version: 1.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Editing, NLP, Productivity]
    homepage: https://pypi.org/project/nano-pdf/
    related_skills: [pdf, ocr-and-documents]
---

# nano-pdf

role: natural-language PDF text editor
do: install; target file/page; issue precise edit; inspect resulting PDF
inputs: PDF, page number, instruction, API-key configuration
outputs: edited PDF, verification result
¬: use for merge/split/forms/watermarks/creation (use `pdf`); use for scan OCR (use `ocr-and-documents`); assume page base; trust complex layout edits without inspection; expose API key

## When to Use

Use for text changes on an existing PDF: title/date/name corrections or small
page-local edits. The underlying tool uses an LLM and needs an API key; check
`nano-pdf --help` for configuration.

## Procedure

1. Verify `nano-pdf` + API-key configuration; preserve source PDF.
2. Confirm target page and precise text-only instruction.
3. Run `nano-pdf edit`; if page base is wrong, retry once at adjacent index.
4. Open/render the result and verify requested text + surrounding layout.

## Install

```bash
# Install with uv (recommended — already available in Hermes)
uv pip install nano-pdf

# Or with pip
pip install nano-pdf
```

## Usage

```bash
nano-pdf edit <file.pdf> <page_number> "<instruction>"
```

## Examples

```bash
# Change a title on page 1
nano-pdf edit deck.pdf 1 "Change the title to 'Q3 Results' and fix the typo in the subtitle"

# Update a date on a specific page
nano-pdf edit report.pdf 3 "Update the date from January to February 2026"

# Fix content
nano-pdf edit contract.pdf 2 "Change the client name from 'Acme Corp' to 'Acme Industries'"
```

## Pitfalls

- page numbering may be 0- or 1-based by version; if wrong page, retry ±1
- text edits work best; complex layout may need another approach

## Verification

- verify output PDF with `read_file` (file size) or open it
- [ ] intended page/content changed
- [ ] output opens and size/content is plausible
- [ ] API key stayed private