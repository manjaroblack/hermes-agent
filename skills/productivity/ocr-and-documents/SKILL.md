---
name: ocr-and-documents
description: Extract text from PDFs/scans (pymupdf, marker-pdf).
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [pdf, docx, powerpoint]
---

# PDF + Document Extraction

role: document text/OCR extractor
do: prefer remote extraction; choose lightweight vs OCR engine; extract text/tables/images/metadata; split/merge/search; report coverage/confidence
inputs: URL/local PDF/scan/EPUB, page range, output format, disk budget
outputs: text/Markdown/JSON/tables/images/metadata, page coverage and OCR caveats
¬: use for DOCX/PPTX authoring (use `docx`/`powerpoint`); use for PDF manipulation (use `pdf`); treat text-layer extraction as OCR; install marker without disk check; hide unreadable pages

DOCX: use `docx`/`python-docx`; PPTX: `powerpoint`; PDF merge/split/forms/
watermarks/creation: `pdf`. This skill covers text extraction from PDFs/scans.

## When to Use

- extract PDF/scan text, tables, equations, code, forms, images, metadata
- OCR many pages or complex layout
- read arXiv papers
- split/merge/search PDF with PyMuPDF
- handle `read_file` EXTRACTION COVERAGE WARNING

## Procedure

1. If a URL exists, try `web_extract` before installing a local engine.
2. For local input, inspect text-layer coverage; choose pymupdf or marker by table.
3. Check disk before marker; constrain pages/output and run extraction/OCR.
4. Inspect page coverage, tables/images/metadata, and unreadable/low-confidence spans.
5. Render/OCR warned pages or report exact gaps; complete Verification.

If `read_file` reports coverage warning, it read text layer only. For a few
empty pages render + `vision_analyze`:

`pdftoppm -jpeg -r 150 -f N -l N file.pdf /tmp/page`

For many pages use marker-pdf below.

## Step 1: Remote URL

Always try `web_extract` first when URL exists:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

Firecrawl PDF→Markdown; no local dependency. Use local only for local files,
failed web extraction, or batch work.

## Step 2: Local Engine

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

Decision: pymupdf unless OCR, equations, forms, or complex layout analysis.
If marker is needed but free disk <~5 GB, state available space and offer:
free space, provide URL for `web_extract`, or try pymupdf (text PDFs only;
not scans/equations).

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

Helper:

```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

Inline:

```bash
python -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

## marker-pdf (OCR/complex layouts)

Check disk before install:

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

First marker use downloads ~2.5 GB models to `~/.cache/huggingface/`.

## ArXiv

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge, Search

Use `execute_code` or inline Python; no extra dependency beyond pymupdf:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

## Pitfalls

- URL → `web_extract` first
- safe default → pymupdf: instant/no models/everywhere
- marker → OCR/scans/equations/complex layout only
- both helpers support `--help`
- DOCX: `pip install python-docx`; structural parse beats OCR
- PPTX: use `powerpoint` (python-pptx)

## Verification

- [ ] source type/URL/local path and chosen engine recorded
- [ ] disk check before marker; model/cache footprint disclosed
- [ ] output format/pages/tables/images/metadata match request
- [ ] coverage warning pages rendered/OCRed or explicitly reported
- [ ] low-confidence/unreadable content remains visible