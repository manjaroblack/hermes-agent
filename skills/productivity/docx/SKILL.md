---
name: docx
description: Create, read, edit, template, and review Word .docx files.
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [word, docx, documents, office, templates, revisions, comments]
    category: productivity
    related_skills: [pdf, xlsx, powerpoint]
---

# Word `.docx`

role: OOXML document operator using `python-docx` helpers
do: create/read/edit/template; manage styles/lists/tables/media/fields; inspect revisions/comments; convert via LibreOffice; validate package
inputs: JSON spec, `.docx`/template, values, text/style/table/revision/comment operation, local images
outputs: `.docx`, text/structure/images/revision/comment JSON, PDF when renderer exists, health result
¬: edit legacy `.doc`, `.odt`, or WYSIWYG layouts; render with python-docx; unzip/edit XML; assume fields computed; resolve unsupported revision types silently; claim validation = XSD

Handles text, styles, lists, tables, images, headers/footers, `{{token}}`
templates, tracked-change list/accept/reject, comments list/add/delete, TOC and
page-number fields, package health. PDF requires LibreOffice; `.doc` unsupported.

## When to Use

- create report/letter/contract
- read text, outline, styles, images
- replace text/table cells/paragraphs/styles/runs
- fill template placeholders
- review/accept/reject tracked changes or comments
- diagnose a corrupt/unopenable package
- add TOC or `Page X of Y`

## Prerequisites

- Python 3.10+ + `python-docx` (`pip install python-docx`; import `docx`; lxml included)
- comments `add`: native API python-docx >=1.2; XML fallback older, automatic
- image blocks: local PNG/JPEG files

## Helpers

Helpers are beside this file in `scripts/`; run via `terminal`; each supports
`--help` and JSON stdout:

```bash
python scripts/docx_create.py spec.json out.docx
python scripts/docx_read.py out.docx --text
python scripts/docx_edit.py replace out.docx --find old --replace new
python scripts/docx_template.py tpl.docx values.json filled.docx
python scripts/docx_revisions.py list out.docx
python scripts/docx_comments.py list out.docx
python scripts/docx_validate.py out.docx
```

## Command Map

| Task | Command |
| --- | --- |
| Create from JSON spec | `docx_create.py spec.json out.docx` |
| Full text (body+tables+headers/footers) | `docx_read.py f.docx --text` |
| Heading outline + table shapes | `docx_read.py f.docx --structure` |
| Styles actually used | `docx_read.py f.docx --styles` |
| Extract embedded images | `docx_read.py f.docx --images outdir/` |
| Detect tracked changes/comments | `docx_read.py f.docx --revisions` |
| Find/replace (formatting kept) | `docx_edit.py replace f.docx --find A --replace B -o out.docx` |
| Set a table cell | `docx_edit.py set-cell f.docx --table 0 --row 1 --col 2 --text X` |
| Insert paragraph before index N | `docx_edit.py insert f.docx --index N --text X --style Normal` |
| Delete paragraph N | `docx_edit.py delete f.docx --index N` |
| Apply style to paragraph N | `docx_edit.py style f.docx --index N --style "Heading 1"` |
| Merge equal-format adjacent runs | `docx_edit.py normalize f.docx -o out.docx` |
| Insert TOC field before para N | `docx_edit.py toc f.docx --index N -o out.docx` |
| "Page X of Y" footer fields | `docx_edit.py page-numbers f.docx` |
| Fill `{{tokens}}` | `docx_template.py tpl.docx values.json out.docx --strict` |
| List revisions (id/author/date/text) | `docx_revisions.py list f.docx` |
| Accept / reject all revisions | `docx_revisions.py accept-all f.docx -o out.docx` (or `reject-all`) |
| Accept / reject one revision | `docx_revisions.py accept f.docx --id 3 -o out.docx` |
| List comments (+anchored text) | `docx_comments.py list f.docx` |
| Add comment anchored to text | `docx_comments.py add f.docx --target "phrase" --text "note" --author You` |
| Delete comment by id | `docx_comments.py delete f.docx --id 0` |
| Health-check the package | `docx_validate.py f.docx` (exit 1 on errors) |

## Procedure

1. **Create.** `write_file` a JSON spec; run `docx_create.py`. Spec supports
   `page` (size/margins mm), `header`/`footer`, `footer_page_numbers`, custom
   `styles` (font/size/bold/italic/hex `color`), and `blocks`: `heading`
   (1–9), `paragraph` (`text` or styled `runs`), `bullet_list`,
   `numbered_list`, `table` (`header`, `rows`, optional built-in style such as
   `Table Grid`), `image` (`path`, optional `width_mm`), `toc`, `page_break`.
   Full format is documented at top of `scripts/docx_create.py`.
2. **Read.** Use exactly one `docx_read.py` mode. `--text` returns body,
   table cells, headers/footers; `--structure` heading outline + paragraph/
   table/section counts; `--images DIR` copies `word/media/`.
3. **Edit.** `replace` covers body/nested tables/headers/footers and preserves
   runs; `--body-only` skips headers/footers. `-o out.docx` preserves original;
   omit for in-place. Paragraph indices follow `--structure`/`--text` body
   order. Run `normalize` after heavy Word editing to merge equal-format runs.
4. **Revisions.** `list` reports every `w:ins`/`w:del` (id/author/date/text) in
   body/tables/headers/footers. `accept-all`/`reject-all` bulk resolve;
   `accept`/`reject --id N` single. Accept keeps insertions/drops deleted text;
   reject reverses.
5. **Comments.** `list` returns id/author/date/body/anchored text. `add --target`
   anchors first matching phrase, splitting runs while preserving formatting;
   `delete --id N` removes comment/markers only.
6. **Template.** Put `{{name}}`; pass JSON object to `docx_template.py`.
   `--strict` fails remaining tokens; JSON reports `filled` and
   `unfilled_tokens` either way.
7. **Verify always.** Re-read `--text`/`--structure`; validate documents after
   revision/comment surgery.

## PDF Conversion

LibreOffice required; python-docx cannot render. Check renderer first with
`command -v soffice || command -v libreoffice`; if absent report unavailable.

```bash
soffice --headless --convert-to pdf --outdir outdir/ file.docx
```

## Pitfalls

- text split across runs: normalize first; replace collapses matched runs and
  inherits first-run formatting
- revision resolver handles run-level insert/delete; `--revisions` detects
  paragraph-mark/table-row revisions, format changes, moves but does not resolve
  them; use [references/revisions-and-comments.md](references/revisions-and-comments.md)/Word
- replies/resolved status in `commentsExtended.xml` ignored; added comments plain top-level
- TOC/page fields write field codes; Word/LibreOffice computes results on open;
  python-docx does not, so placeholders show until update
- validator checks zip/parts/relationships/image magic/styles, not XSD; Word may still dislike file
- undefined style raises `KeyError`; built-ins `Heading 1`, `List Bullet`,
  `List Number`, `Table Grid`; custom styles first in create spec
- separate `List Number` blocks may continue numbering
- `set-cell` resets cell runs/plain formatting
- JSON specs/values UTF-8; do not rely on locale
- use scripts/python-docx, never unzip + text-replace `document.xml`; patch/write
  JSON inputs only, not `.docx`

## Verification

- [ ] create/edit/template: `docx_read.py out.docx --text`; expected new strings,
  old strings absent
- [ ] accept/reject: revision list empty except intentionally retained IDs
- [ ] comment surgery: comment list changed; text unchanged
- [ ] `docx_validate.py out.docx` exits 0 and returns `"ok": true`
- [ ] template `--strict` or `unfilled_tokens == []`
- [ ] `--structure` outline/table shapes and `--styles` custom style use match spec