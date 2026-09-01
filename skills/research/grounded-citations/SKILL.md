---
name: grounded-citations
description: "Ground answers and documents in cited, verifiable sources."
version: 1.1.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Citations, Grounding, Sources, Web, Reports]
    category: research
    related_skills: [research-paper-writing, arxiv, ocr-and-documents]
---

# Grounded Citations

role: cited-answer and evidence-led document operator
do: register retrieved URLs; cite inline; render Sources; attach verbatim evidence; verify IDs/coverage; flag unsourced claims
inputs: fetched pages/tool output, draft/chat/document target, ledger path, citation style, coverage/evidence threshold
outputs: inline `[n]` citations, rendered `Sources` block, evidence quotes, verification result
¬: cite from memory; invent IDs/URLs; retype Sources; paraphrase evidence quotes; treat snippets as page text; hide conflicts or gaps

Outside-source claims get inline numbered citations and a mechanically rendered
`Sources:` list. `scripts/sources.py` owns normalized `url → [n]`; the model emits
only ledger IDs. High-stakes work adds verbatim quotes and `[unverified]` markers.
Academic BibTeX pipelines belong to `research-paper-writing`.

## When to Use

- research, comparisons, news/current-state answers
- reports, briefs, docs, decks, wiki pages quoting/paraphrasing outside facts
- fact-finding and multi-source synthesis with attribution/conflicts
- high-stakes medical, legal, financial, safety, or disputed claims

Skip inline citations when retrieval is incidental to coding/version lookup,
casual conversation, or creative writing; mention a URL only when useful.

## Prerequisites

- standard retrieval: `web_search`, `web_extract`, `browser_navigate`, or `terminal`
- stdlib-only `scripts/sources.py` on Python 3
- ledger: `$HERMES_HOME/cache/citations/ledger.json`; override `--ledger <path>` or `HERMES_CITATION_LEDGER`

## How to Run

```bash
S=~/.hermes/skills/research/grounded-citations/scripts/sources.py

python "$S" reset                                  # start a clean ledger
python "$S" add https://example.com/a --title "A"  # prints: [1]
python "$S" add https://example.com/b --title "B"  # prints: [2]
python "$S" list                                   # ledger table
python "$S" render                                 # Sources: block
python "$S" verify draft.md                        # catch bad citations
```

`add` is idempotent and URL-normalized; a page keeps one ID within a ledger.

## Quick Reference

| Action | Command |
|---|---|
| Fresh ledger for a new task | `sources.py reset` |
| Register a source, get its id | `sources.py add <url> [--title T]` |
| Register several at once | `sources.py add <url1> <url2> ...` |
| Register from JSON tool output | `sources.py ingest results.json` |
| Attach verbatim evidence to a source | `sources.py quote <id> --text "exact wording" --from page.txt` |
| Show ledger | `sources.py list [--json]` |
| Render the Sources block | `sources.py render [--style markdown\|plain\|footnotes\|bibtex\|evidence] [--only 1,3]` |
| Render only what a draft cites | `sources.py render --cited-in draft.md` |
| Rewrite a draft's Sources block in place | `sources.py render --replace-in draft.md` |
| Check a draft's citations | `sources.py verify draft.md [--strict] [--min-coverage 0.6] [--evidence]` |

## Procedure

1. **Reset** at task start; skip only when continuing a draft whose IDs must stay
   stable.
2. **Register at retrieval time** after each `web_search`/`web_extract`/
   `browser_navigate`/fetch, before writing prose; use `ingest` for raw JSON.
3. **Cite while drafting** immediately after each supported sentence:

```
Ice floats because it is less dense than liquid water.[1][2]
```

   - no space before brackets; one ID per bracket; max 3 IDs/sentence
   - use only ledger IDs; own knowledge gets no citation
   - conflicts → present both readings, each ID; preserve exact figures/dates/names
   - state "no source found for X" instead of smoothing gaps
4. **Render Sources** with `--cited-in <draft>`; select matching non-Markdown style
   and use `references/citation-formats.md` for docx/PDF/LaTeX/decks/wiki placement.
5. **Verify** before delivery; unknown IDs, ledger/Source disagreement, or thin
   coverage must be fixed and re-run.
6. **Chat** follows the same ledger/citation/render steps; short answers may use
   `render --only <ids>` without a draft file.

## Fact-Checking Mode

For medical/legal/financial/safety/disputed work or explicit fact-checking:

1. Save fetched text; attach a verbatim quote per source:

```bash
python "$S" quote 1 --text "Ice is about 9% less dense than liquid water." --from page1.txt
```

Quote is accepted only if it appears verbatim in evidence (whitespace/case/
Markdown-insensitive; inline links and escaped markup are normalized). Copy from
fetched text; never retype or paraphrase.

2. Mark genuinely unsourceable load-bearing claims `[unverified]`:

```
The refactor likely predates the 2.0 release.[unverified]
```

`verify --min-coverage` counts `[unverified]` as declared provenance; a deliverable
dominated by it must say more retrieval was unavailable.
3. Cross-check disputed facts with an independent source; cite both quotes and
   explain weighting.
4. Run evidence gate/render:

```bash
python "$S" verify report.md --evidence --min-coverage 0.5
python "$S" render --style evidence --replace-in report.md
```

`--evidence` rejects cited sources without quotes. Evidence output shows
claim → source → exact text. `--replace-in` is idempotent; `--cited-in` prints;
both heading forms are `## Sources` (`plain` uses `Sources:`).

**Coverage:** `sentences with declared provenance / prose sentences`. A prose
sentence = non-empty line fragment of 4+ words after Sources; headings (`#`),
tables (`|`), fenced code, and blockquote markers are excluded. Provenance =
`[n]` or `[unverified]`; both on one sentence count once. Run `verify` without a
threshold first; inspect `info: stats:` before choosing one.

## Pitfalls

- registering after drafting reconstructs URLs from memory and invites hallucination
- `reset` mid-task renumbers IDs; never hand-edit them
- hand-typed Sources blocks are unverified; always `render`
- search snippets support only literal snippet claims; extract the page for body claims
- max 3 IDs/sentence; over-citation obscures source responsibility
- do not put ledger citations inside generated code/config; use prose/doc headers
- parallel agents need one shared `--ledger`/`HERMES_CITATION_LEDGER` or IDs collide
- evidence quotes must come from extracted page text, not snippets
- `[unverified]` is not an escape hatch for avoidable retrieval
- `render --replace-in` avoids stale/duplicated Sources blocks
- Preserve source notation when quoting extracted text, e.g. `_[ERAP1](https://…)_`,
  rather than silently converting it to an uncited claim.

## Verification

```bash
python "$S" verify report.md --strict --min-coverage 0.5
```

Green means each draft `[n]` exists in ledger; Sources lists exactly cited IDs and
ledger URLs; cited share meets threshold. Read warnings even on exit 0: registered
but uncited sources can signal lost attribution.
