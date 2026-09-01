---
name: pdf
description: "PDF files: create, read, merge, fill, OCR, edit text."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pdf, documents, forms, ocr, text-extraction, reportlab, pypdf, pdfplumber, pymupdf, marker]
    category: productivity
    related_skills: [docx, xlsx, powerpoint]
---

# PDF Skill

role: PDF creation, extraction, form, manipulation, and security operator
do: inspect; create/read/merge/split/fill/OCR/edit/stamp/secure; route matching references; verify output
inputs: PDF/spec/form JSON; page ranges; field values; metadata/attachment/password request
outputs: PDF or extracted JSON/CSV/text/images; verified fields/pages/metadata; visual review status
¬: treat scanned empty text as no content; skip form layout lint/visual review when relevant; expose passwords; confuse 1-based CLI pages with 0-based pypdf APIs; claim success from logs alone

Create PDFs from specs; build/fill AcroForms with layout lint and overlays;
extract text/tables/metadata; merge/split/rotate/watermark/stamp; export images;
manage metadata/attachments; encrypt/decrypt using pypdf, reportlab, pdfplumber.
Two absorbed capabilities live in `references/` (read the matching file first):

- **Scanned/image-only PDFs and OCR** (pymupdf fast path, marker-pdf quality path, scripts/extract_pymupdf.py + scripts/extract_marker.py): `references/ocr-extraction.md`
- **Editing text inside an existing PDF via natural-language prompts** (nano-pdf CLI): `references/nano-pdf-editing.md`

## When to Use

- reports, invoices, or multi-page PDFs
- fillable AcroForms (text/checkbox/radio/dropdown) from JSON, with layout lint first
- PDF text, tables (JSON/CSV), metadata, or form-field extraction
- merge/split/rotate/subset/watermark/stamp/bookmark/compress operations
- page PNG export for review/OCR; metadata and attachment management
- AcroForm fill/flatten; password encryption/decryption
- NOT scanned/image-only PDFs → `references/ocr-extraction.md`; NOT pixel-perfect HTML-to-PDF → headless browser

## Prerequisites

- Python 3.10+ with `pypdf`, `reportlab`, `pdfplumber`:
  `python -m pip install pypdf reportlab pdfplumber`
- optional rasterization (`pdf_page_image.py`, overlays): `python -m pip install pypdfium2`, or poppler `pdftoppm` on PATH; fallback pypdfium2 → pdftoppm reports `{"rendered": false, "missing": [...]}` (exit 0) when neither exists
- helper scripts check imports lazily and print install hints

## How to Run

Helpers in `scripts/` are argparse CLIs; run with `terminal`; every one supports
`--help`. They read/write UTF-8 JSON, print JSON to stdout, and exit non-zero on failure.

```bash
python scripts/pdf_create.py spec.json -o out.pdf         # build PDF from JSON spec
python scripts/pdf_make_form.py formspec.json -o form.pdf # build fillable AcroForm from JSON spec
python scripts/pdf_form_layout.py formspec.json           # lint form layout BEFORE building
python scripts/pdf_form_layout.py formspec.json --render-overlay boxes.png [--pdf form.pdf]
python scripts/pdf_read.py doc.pdf --text                 # per-page text (JSON)
python scripts/pdf_read.py doc.pdf --tables --csv-dir t/  # tables to JSON + CSV files
python scripts/pdf_read.py doc.pdf --meta                 # metadata, page sizes, encrypted/scanned flags
python scripts/pdf_read.py form.pdf --fields              # form fields: name, type, value
python scripts/pdf_merge.py a.pdf b.pdf -o merged.pdf [--bookmarks]
python scripts/pdf_split.py doc.pdf --pages 1-3,7 -o part.pdf [--rotate 90]
python scripts/pdf_fill_form.py form.pdf --fields-json values.json -o filled.pdf [--flatten]
python scripts/pdf_secure.py doc.pdf --encrypt -o enc.pdf --user-password your-password
python scripts/pdf_secure.py enc.pdf --decrypt -o dec.pdf --password your-password
python scripts/pdf_watermark.py doc.pdf --stamp mark.pdf -o stamped.pdf [--under]
python scripts/pdf_stamp.py doc.pdf -o out.pdf --text "DRAFT" --x 150 --y 400 \
    --font-size 60 --rotation 45 --opacity 0.3 --color "#cc0000" [--pages 1-3]
python scripts/pdf_stamp.py doc.pdf -o out.pdf --image sig.png --x 400 --y 60 --width 120
python scripts/pdf_page_image.py doc.pdf --pages 1-3 --dpi 150 --out-dir imgs/
python scripts/pdf_meta.py doc.pdf --set-meta --title "T" --author "A" -o out.pdf
python scripts/pdf_meta.py doc.pdf --attach data.csv -o out.pdf
python scripts/pdf_meta.py doc.pdf --list-attachments | --extract-attachments dir/
```

## Quick Reference

| Task | Tool | Command / API |
|---|---|---|
| Create doc (headings, tables, images) | reportlab platypus | `pdf_create.py spec.json -o out.pdf` |
| Build fillable form | reportlab acroForm | `pdf_make_form.py formspec.json -o form.pdf` |
| Lint form layout / overlay image | pure python + PIL | `pdf_form_layout.py formspec.json [--render-overlay o.png]` |
| Per-page text | pdfplumber | `pdf_read.py f.pdf --text` |
| Tables → JSON/CSV | pdfplumber | `pdf_read.py f.pdf --tables` |
| Metadata / sizes / encrypted / scanned | pypdf + pdfplumber | `pdf_read.py f.pdf --meta` |
| Merge (+ outline) | pypdf | `pdf_merge.py a.pdf b.pdf -o m.pdf` |
| Split / extract / rotate | pypdf | `pdf_split.py f.pdf --pages 2-5 --rotate 90` |
| List / fill / flatten form | pypdf | `pdf_read.py --fields`, `pdf_fill_form.py` |
| Encrypt / decrypt (AES-256) | pypdf | `pdf_secure.py --encrypt/--decrypt` |
| Watermark / stamp PDF page | pypdf | `pdf_watermark.py f.pdf --stamp w.pdf` |
| Stamp text/image at coordinates | reportlab + pypdf | `pdf_stamp.py f.pdf --text "Sign here" --x 400 --y 60` |
| Pages → PNG (review / OCR hand-off) | pypdfium2 or pdftoppm | `pdf_page_image.py f.pdf --pages 1-3 --out-dir imgs/` |
| Set/clear metadata, attachments | pypdf | `pdf_meta.py --set-meta / --attach / --extract-attachments` |
| Compress content streams | pypdf | `pdf_split.py f.pdf --pages 1-N --compress` |

## Procedure

1. **Inspect first.** Run `pdf_read.py file.pdf --meta`; inspect `encrypted` (decrypt first with `pdf_secure.py --decrypt`) and `likely_scanned_pages`. For image-only pages, export with `pdf_page_image.py --pages <scanned> --dpi 300 --out-dir imgs/`; route PNGs to `references/ocr-extraction.md`; never call empty text "no content".
2. **Create.** Write JSON with `write_file` (elements `heading`, `paragraph`, `table`, `image`, `pagebreak`; optional `title`/`author`; automatic page numbers); run `pdf_create.py`; if layout matters, render and inspect with `vision_analyze`.
3. **Extract.** `--text` → per-page JSON strings; `--tables` → per-page row arrays and optional CSV. Read with `read_file`; never eyeball binary PDFs.
4. **Manipulate.** `pdf_merge.py` concatenates and can bookmark each source; `pdf_split.py` handles 1-based ranges (e.g. `1-3,5,9-`), 90° rotation, and `--compress`. Prepare a single-page stamp (e.g. `pdf_create.py`) and overlay with `pdf_watermark.py`; use `pdf_stamp.py` for one-liner stamps ("sign here", diagonal DRAFT, corner labels) with text/image at explicit coordinates.
5. **Build forms.** Write one form JSON with `label_box`/`entry_box` PDF points (see `references/forms.md`); lint with `pdf_form_layout.py`, fix every problem, optionally inspect `--render-overlay` PNG with `vision_analyze`, build with `pdf_make_form.py`, confirm with `pdf_read.py --fields`.
6. **Fill forms.** List fields (`--fields`) for exact names/types; write UTF-8 `{"FieldName": "value"}` via `write_file` (checkbox `true`/`false`; radio/choice values must match export options); run `pdf_fill_form.py`; re-read `--fields`.
7. **Metadata/attachments.** `pdf_meta.py --set-meta` writes Title/Author/Subject/Keywords (DocInfo); `--clear-meta` drops them; `--attach`/`--list-attachments`/`--extract-attachments` round-trip embedded files.
8. **Secure.** Encrypt with distinct user/owner passwords and AES-256. Known password + `--decrypt` → unencrypted copy.
9. **Verify** (see below) before reporting success.

## Pitfalls

- **Scanned PDFs**: empty `extract_text()` plus page images means there is no text layer. Route to `references/ocr-extraction.md`; do not fabricate text.
- **Flattening limits**: `pdf_fill_form.py --flatten` uses pypdf's flatten support, which converts widget appearances into page content. It is reliable for plain text fields and checkboxes but can drop or misrender exotic widgets (rich text, custom appearance streams, some radio groups). Verify the flattened output visually with `vision_analyze`; for bulletproof flattening use an external renderer (e.g. Ghostscript or `pdftoppm`+reassembly) as a fallback.
- **NeedAppearances**: after filling, viewers only render values if appearance streams exist. The fill script sets the AcroForm `NeedAppearances` flag so conforming viewers regenerate them; some minimal viewers ignore it — flatten if display fidelity matters.
- **Non-Latin form values**: values are stored correctly (UTF-16), but the field's default font may lack glyphs, so a viewer can show blanks even though the data round-trips. Verify with `--fields`, not just visually.
- **Compression expectations**: `--compress` only deflates content streams. Typical savings are 0–20%; it does nothing for PDFs dominated by images or already-compressed streams. It is not a substitute for image downsampling (Ghostscript territory).
- **Permission flags don't enforce**: owner-password permission bits (no-print, no-copy) are polite requests that viewers may honor; any library (including pypdf) can read and strip them. Only the user password actually gates content via encryption. Never present permission flags as security.
- **Table extraction is heuristic**: pdfplumber detects tables from ruling lines/word alignment; borderless or merged-cell tables may need `table_settings` tuning or manual cleanup.
- **Page indexing**: helper CLIs take 1-based pages; pypdf APIs are 0-based. The scripts convert — don't double-convert.
- **Rotated stamp text extraction**: pdfplumber's line grouping scrambles rotated glyphs (a 45° "DRAFT" extracts as stray letters); verify rotated stamps with `pypdf`'s `extract_text()` or a rendered image instead.
- **Radio groups**: reportlab needs ≥2 `radio()` widgets per group, fills need the slashed export value (`"/red"`), and flatten fidelity is worst for radios — see `references/forms.md`.
- **Metadata scope**: `pdf_meta.py` writes the classic DocInfo dictionary only; embedded XMP metadata (if any) is left untouched and may show different values in some viewers.
- **PDF/A is out of scope**: pypdf/reportlab cannot produce or validate conformant PDF/A. If archival conformance is required, run Ghostscript via the `terminal` tool (e.g. `gs -dPDFA=2 -dPDFACompatibilityPolicy=1 -sColorConversionStrategy=UseDeviceIndependentColor -sDEVICE=pdfwrite -o out.pdf in.pdf` with a suitable ICC profile) and validate with veraPDF — both are external installs, and the result still needs validation, not assumption.
- Rotation must be a multiple of 90; encrypted inputs must be decrypted before any other operation.

## Verification

- After create/merge/split: `pdf_read.py out.pdf --meta` — confirm `page_count`, and per-page `rotation` when you rotated.
- After extraction: check the JSON is non-empty and spot-check a known string or cell.
- Form design loop: `pdf_form_layout.py spec.json` must exit 0; then `--render-overlay boxes.png --pdf form.pdf` and review the PNG with `vision_analyze` (red = entry boxes with field names, blue = label boxes) asking about overlaps, misalignment, and labels detached from their fields. Iterate spec → lint → overlay until clean.
- After building a form: `pdf_read.py form.pdf --fields` lists every spec field with the right type and options.
- After form fill: `pdf_read.py filled.pdf --fields` and compare values (exact match, including non-ASCII).
- After stamping: re-extract text (pypdf for rotated stamps) or render the page with `pdf_page_image.py` and inspect with `vision_analyze`.
- After metadata/attachment edits: `pdf_read.py --meta` / `pdf_meta.py --list-attachments`, and re-extract an attachment to byte-compare.
- After encrypt: `--meta` shows `"encrypted": true` and opening without a password fails; after decrypt, text extraction matches the original.
- For anything visual (watermarks, flattened forms), render and inspect with `vision_analyze`.
