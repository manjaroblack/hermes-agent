---
name: pdf
description: Create, read, merge, fill, and secure PDF files.
version: 1.0.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pdf, documents, forms, reportlab, pypdf, pdfplumber]
    category: productivity
    related_skills: [docx, xlsx, powerpoint, ocr-and-documents]
---

# PDF

role: PDF creator/extractor/form/manipulation operator
do: inspect; create report/form; extract text/tables/meta/fields; merge/split/rotate; watermark/stamp/bookmark/compress; render; attach; encrypt/decrypt; verify
inputs: PDF/spec/formspec/field values, page ranges/coordinates, passwords, metadata/attachments
outputs: PDF/PNG/JSON/CSV, fields/meta/attachments, render status, verification evidence
¬: OCR image-only PDFs (use `ocr-and-documents`); HTML pixel-perfect rendering (use headless browser); call permission bits security; skip layout lint/visual check; report empty text as no content; expose passwords

Uses pypdf, reportlab, pdfplumber. Scanned/image-only pages lack text layer:
stop and hand to `ocr-and-documents`.

## When to Use

- reports/invoices/multi-page PDFs
- fillable AcroForms: text/checkbox/radio/dropdown, layout lint + overlay
- text/tables (JSON/CSV), metadata, form values
- merge/split/rotate/subset/watermark/stamp/bookmark/compress
- page PNGs, metadata, attachments, fill/flatten, encrypt/decrypt

## Prerequisites + Runtime

- Python 3.10+ + `pypdf`, `reportlab`, `pdfplumber`:
  `python -m pip install pypdf reportlab pdfplumber`
- optional page raster: `python -m pip install pypdfium2`, or poppler
  `pdftoppm`; fallback pypdfium2 → pdftoppm; neither →
  `{"rendered": false, "missing": [...]}` exit 0
- helpers lazy-check imports, print install hint, all support `--help`
- JSON strict UTF-8 stdout; non-zero on failure; invoke via `terminal`

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

1. **Inspect**: `pdf_read.py file.pdf --meta`; check `encrypted` and
   `likely_scanned_pages`. Encrypted → decrypt first. Image-only pages →
   `pdf_page_image.py --pages <scanned> --dpi 300 --out-dir imgs/` →
   `ocr-and-documents`; never call empty text no content.
2. **Create**: `write_file` JSON elements `heading`, `paragraph`, `table`,
   `image`, `pagebreak`; optional `title`/`author`; automatic page numbers;
   `pdf_create.py`; visual `vision_analyze` when layout matters.
3. **Extract**: `--text` per-page JSON; `--tables` row arrays + optional CSV;
   inspect with `read_file`, not binary eyeballing.
4. **Manipulate**: merge bookmarks one/source; split 1-based ranges
   (`1-3,5,9-`), 90° rotation, `--compress`; watermark single-page stamp;
   `pdf_stamp.py` for text/image coordinates.
5. **Forms**: formspec `label_box`/`entry_box` in PDF points
   ([references/forms.md](references/forms.md)); lint and fix every issue;
   optional overlay `vision_analyze`; build; confirm `--fields`.
6. **Fill**: list exact names/types; UTF-8 `{"FieldName": "value"}`;
   checkbox bool; radio/choice exact export option; fill; re-read.
7. **Metadata/files**: `--set-meta` Title/Author/Subject/Keywords DocInfo;
   `--clear-meta`; attach/list/extract round-trip.
8. **Secure**: distinct user/owner passwords + AES-256; known password
   `--decrypt` writes unencrypted copy.
9. **Verify** below.

## Pitfalls

- scanned PDF = empty `extract_text()` + page images → OCR skill; no fabrication
- flattening: `--flatten` pypdf appearance→page content; reliable plain text/
  checkbox, may drop exotic widgets/radios; render `vision_analyze`; external
  Ghostscript or `pdftoppm`+reassembly for bulletproof fallback
- `NeedAppearances` set for conforming viewers; minimal viewers may ignore;
  flatten when display fidelity matters
- non-Latin values stored UTF-16 but default field font may lack glyphs; verify
  `--fields`, not visual only
- `--compress` deflates streams only (0–20% typical); no image downsampling
- owner permission bits are polite, removable; only user password gates content
- table extraction heuristic; tune `table_settings`/clean manually
- CLI pages 1-based; pypdf APIs 0-based; scripts convert once
- rotated text extraction may scramble; pypdf `extract_text()`/render instead
- radio groups: ≥2 `radio()` widgets; fill slashed export (`"/red"`); see
  [references/forms.md](references/forms.md)
- `pdf_meta.py` classic DocInfo only; XMP untouched
- PDF/A out of scope; use `terminal` Ghostscript (e.g.
  `gs -dPDFA=2 -dPDFACompatibilityPolicy=1 -sColorConversionStrategy=UseDeviceIndependentColor -sDEVICE=pdfwrite -o out.pdf in.pdf` with suitable ICC) + veraPDF; validate
- rotation multiple of 90; decrypt encrypted input before operations

## Verification

- create/merge/split → `pdf_read.py out.pdf --meta`; page count + rotations
- extraction → non-empty JSON; known string/cell spot-check
- form loop: layout lint exit 0 → overlay `boxes.png` with `vision_analyze`;
  red entry boxes/field names, blue labels; iterate until no overlap/misalignment/detachment
- built form → `pdf_read.py form.pdf --fields`: every type/options
- filled → `pdf_read.py filled.pdf --fields`; exact values incl. non-ASCII
- stamp → pypdf text for rotated or render with `pdf_page_image.py` + vision
- metadata/attachment → meta/list; extract + byte-compare
- encrypt → `"encrypted": true`, password required; decrypt text matches
- visual watermark/flattened form → render + `vision_analyze`