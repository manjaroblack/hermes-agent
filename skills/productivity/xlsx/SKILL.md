---
name: xlsx
description: Create, read, edit Excel .xlsx workbooks and CSVs.
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [excel, spreadsheet, xlsx, csv, openpyxl, productivity]
    category: productivity
    related_skills: [docx, pdf, powerpoint]
---

# XLSX

role: Excel/CSV workbook operator
do: create styled multi-sheet workbooks; inspect/dump; edit/restructure; recalculate; convert CSV↔XLSX; verify formulas/visuals
inputs: workbook/CSV, JSON spec, sheet/range/cell operations, formulas/styles/structure, encoding
outputs: `.xlsx`/CSV/JSON reports, formulas/cached results, charts/tables/names/notes, recalculation state
¬: treat openpyxl as formula engine; use raw insert/delete where references matter; treat sheet protection as security; save `data_only=True` workbooks; silently drop charts/images; handle `.xls` as `.xlsx`; hide `not_shifted` limitations

Use Python + openpyxl; helper scripts are argparse CLIs, JSON stdout, explicit
UTF-8 I/O. `.xls` legacy binary → LibreOffice conversion first.

## When to Use

- create reports with sheets, formulas/charts, styling, tables, validation,
  defined names, hyperlinks, notes, protection
- read inventory/data/formulas/cached values/notes/names/tables
- edit cells/rows/columns/sheets/tables/names/notes/protection
- restructure formulas/merges/filters/validations/table refs
- headless formula recalc or CSV interop

## Prerequisites

- Python 3.10+ + openpyxl: `pip install openpyxl`
- optional LibreOffice `soffice` for recalc/conversion

## Commands

Run from this skill's `scripts/`; all support `--help`:

```bash
python scripts/xlsx_create.py spec.json report.xlsx   # build from JSON spec
python scripts/xlsx_read.py report.xlsx --sheets      # inventory
python scripts/xlsx_read.py report.xlsx --json --sheet Data
python scripts/xlsx_read.py report.xlsx --formulas
python scripts/xlsx_edit.py report.xlsx --sheet Data --set B2=42 --recalc
python scripts/xlsx_restructure.py report.xlsx --sheet Data --insert-rows 3:2
python scripts/xlsx_recalc.py report.xlsx
python scripts/csv_to_xlsx.py data.csv out.xlsx --encoding utf-8
python scripts/xlsx_to_csv.py report.xlsx out.csv --sheet Data
```

Author specs with `write_file`; inspect JSON with `read_file`/stdout.

## Quick Reference

| Task | Command |
|---|---|
| Create workbook from spec | `xlsx_create.py spec.json out.xlsx` |
| Sheet names + dimensions | `xlsx_read.py f.xlsx --sheets` |
| Dump sheet as JSON | `xlsx_read.py f.xlsx --json --sheet S` |
| Dump sheet as CSV | `xlsx_read.py f.xlsx --csv --out d.csv` |
| List formulas + cached values | `xlsx_read.py f.xlsx --formulas` |
| Set a cell / formula | `xlsx_edit.py f.xlsx --set "A1==SUM(B:B)"` |
| Append a row | `xlsx_edit.py f.xlsx --append '[1,"x",true]'` |
| Insert 2 rows, refs NOT shifted | `xlsx_edit.py f.xlsx --insert-rows 3:2` |
| Insert 2 rows, refs shifted | `xlsx_restructure.py f.xlsx --insert-rows 3:2` |
| Delete a column, refs shifted | `xlsx_restructure.py f.xlsx --delete-cols B` |
| Create a native table | `xlsx_edit.py f.xlsx --add-table Sales:A1:C9` |
| Append inside a table | `--table-append 'Sales=["West",5]'` |
| List tables | `xlsx_edit.py f.xlsx --list-tables` |
| Defined names | `--define-name "Rates='Data'!$B$2:$B$9"` / `--delete-name Rates` / `xlsx_read.py f.xlsx --names` |
| Hyperlink | `--hyperlink "A1=https://example.com|Docs"` |
| Cell note | `--note "B2=Check this|Reviewer"`; read via `xlsx_read.py f.xlsx --notes` |
| Protect sheet (see Pitfalls) | `--protect your-password --unlock B2:B9` |
| Recalculate via LibreOffice | `xlsx_recalc.py f.xlsx` |
| Copy / rename sheet | `--copy-sheet Src:New --rename-sheet Old:New` |
| Force recalc on open | `xlsx_edit.py f.xlsx --recalc` |
| CSV -> styled xlsx | `csv_to_xlsx.py in.csv out.xlsx` |
| xlsx -> CSV | `xlsx_to_csv.py f.xlsx out.csv --encoding utf-8` |

## Procedure

1. **Create**: JSON sheet supports `rows` (scalars/styled cells), sparse
   `cells`, `column_widths`, `row_heights`, `merges`, `freeze_panes`,
   `autofilter`, `conditional_formats` (cell_is/color scales), `charts`
   (bar/line/pie ranges), `validations` (list dropdown), `tables` (native,
   style), `protection`; workbook `defined_names`; cell `hyperlink`/`note`.
   Typed numbers/bools pass through; dates use
   `{"value": "2026-01-31", "type": "date"}`. Excel formats:
   `"$#,##0.00"`, `"0.0%"`, `"yyyy-mm-dd"`.
2. **Formulas**: spec `"formula": "SUM(B2:B9)"` or editor
   `--set "C1==SUM(A:A)"`; use `"full_calc_on_load": true` or `--recalc`.
   openpyxl never evaluates formulas.
3. **Read**: `--sheets` inventory (names/dimensions/merges/chart count,
   tables/protection/names); `--json`/`--csv` data; `--formulas` formula +
   cached result; `--notes`; `--names`. Cached result only exists after a
   real spreadsheet app saves; fresh openpyxl files yield `null`. Run
   `xlsx_recalc.py`, then reload `--data-only`; absent `soffice` prints
   `{"recalculated": false, ...}` and exits 0.
4. **Edit**: `xlsx_edit.py` order = copy/rename → structural changes → set/
   append; in-place unless `--out`; copy first to preserve original.
5. **Restructure**: formulas/merges/tables/filters →
   `xlsx_restructure.py`, not raw editor. It rewrites formula refs on all
   sheets (absolute `$`, ranges, cross-sheet), shifts merges, autofilter,
   freeze panes, validation/conditional-format ranges, table refs, defined
   names, dimensions; JSON includes `not_shifted`. Rules/limits:
   `references/restructuring.md`.
6. **CSV**: `csv_to_xlsx.py` infers int/float/bool/ISO date and styles header;
   `xlsx_to_csv.py` emits ISO dates/blank strings. UTF-8 default; encodings
   include `utf-8-sig` and `cp1252`. European CSV may use `;` and decimal
   commas: `--delimiter ';'`; `"12,5"` remains string.

## Convert

```bash
# Legacy .xls conversion shorthand
soffice --headless --convert-to xlsx old.xls
soffice --headless --convert-to pdf report.xlsx --outdir out/
soffice --headless --convert-to csv report.xlsx --outdir out/  # 1st sheet only
```

Only first sheet converts to CSV; other sheets → `xlsx_to_csv.py --sheet NAME`.
No `soffice` → install LibreOffice or deliver unconverted.

## Pitfalls

- formula results need Excel/LibreOffice save; `load_workbook(path, data_only=True)`
  otherwise returns cached `None`
- `xlsx_edit.py` insert/delete does not shift refs; restructure does, but
  cannot move chart anchors/images/conditional-format RULE formulas; inspect
  JSON `not_shifted` + `references/restructuring.md`
- sheet protection hash is not security/encryption; anyone can strip it
- load `data_only=True` then save discards formulas
- openpyxl editing/saving drops charts/images; re-add or avoid re-save
- explicit encoding; European delimiter/decimal traps above
- dates return `datetime`/`date`, dumps emit ISO
- sheet names max 31 chars; reject `[ ] : * ? / \\`

## Verification

- create → `xlsx_read.py out.xlsx --sheets`; confirm names/dimensions/merges/charts
- dump `--json`; compare source values
- edit → re-dump touched range; formulas → `--formulas` + `--recalc`
- restructure → inspect JSON; rerun `--formulas` and `--sheets`
- visual →
  `soffice --headless --convert-to pdf out.xlsx` then inspect PDF
- `.xls` conversion and CSV encoding/delimiter recorded