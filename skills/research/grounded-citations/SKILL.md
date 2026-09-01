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
    related_skills: [arxiv, pdf]
---

# Grounded Citations

role: retrieval-grounded citation and evidence operator
do: reset/register sources; cite while drafting; render Sources; verify IDs/coverage; attach quotes for fact-checking
inputs: fetched URLs/text; draft; citation style; coverage/evidence threshold
outputs: inline numbered citations; generated Sources block; evidence ledger; verified or blocked draft
¬: invent IDs/URLs; register after drafting; cite search snippets as page evidence; retype Sources URLs; use `[unverified]` as an escape hatch

Every outside-source claim gets an inline numbered citation and generated
`Sources:` list, Perplexity-style. Ledger owns `url → [n]`; IDs/URLs come from
retrieval, never memory; emit only small ledger-returned integers.

For high-stakes work the ledger is also a fact-check chain: attach verbatim
quotes (rejected unless literally present in fetched page text); flag model-
knowledge claims `[unverified]`; `verify --evidence` fails cited sources without evidence.

Scope: chat answers, markdown/PDF/docx/slides, research reports. Not academic
BibTeX pipelines; conference papers → `arxiv` (see `references/citation-formats.md`).

## When to Use

Use when an answer/artifact rests on fetched information:

- Research, comparisons, news summaries, "what is the current state of X"
- Any deliverable you write to disk that quotes, paraphrases, or reports
  outside facts — reports, briefs, docs, decks, wiki pages
- Fact-finding where the user will want to check your work
- Multi-source synthesis where conflicting sources must be attributed

Skip inline citations when retrieval is incidental: quick syntax/version lookup
mid-coding, casual conversation, creative writing. Mention a URL only when useful.

## Prerequisites

None beyond standard tools. `scripts/sources.py` is stdlib-only Python 3.
Retrieve with configured `web_search`, `web_extract`, `browser_navigate`, or
`terminal` (curl, CLIs).

Ledger location: `$HERMES_HOME/cache/citations/ledger.json` (profile-aware).
Override per task with `--ledger <path>` or `HERMES_CITATION_LEDGER`.

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

`add` is idempotent and URL-normalized: a page keeps one ID within a ledger
across search/extract rounds.

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

① **Reset the ledger** at task start for a grounded answer/document. Skip reset
when continuing a draft with existing IDs; reuse keeps numbering stable.

② **Register every source at retrieval time.** After each `web_search` /
`web_extract` / `browser_navigate` / fetch, pass URLs to `sources.py add` (or
pipe raw JSON to `sources.py ingest`) *before* drafting. This prevents memory-
reconstructed IDs/URLs.

③ **Write cite-while-drafting.** Place the bracketed id(s) immediately after
each sentence the source supports:

```
Ice floats because it is less dense than liquid water.[1][2]
```

- no space before bracket; each ID in its own brackets
- max 3 IDs/sentence; cite each sentence, not one end dump
- ledger-returned IDs only; never invent ID/URL
- own knowledge → no citation
- conflicting sources → present both readings with separate IDs
- quote figures/dates/names exactly; state gaps ("no source found for X"), do not smooth them

④ **Append Sources** with `sources.py render --cited-in <draft>`; generate ID →
URL mechanically, never retype. Non-markdown → matching `--style` and
`references/citation-formats.md` (docx footnotes, PDF/LaTeX endnotes, deck
Sources slide, wiki per-page source lists).

⑤ **Verify before delivery** — `sources.py verify <draft>` exits non-zero for
unknown IDs, a Sources/ledger mismatch, or (with `--min-coverage`) thin citation
coverage. Fix and rerun.

⑥ **Chat answers** use the same steps: register, cite inline, end with rendered
`Sources:`. Short answer → `sources.py render --only <ids>` instead of a file.

## Fact-Checking Mode

When the reader must check the chain — medical, legal, financial, safety,
disputed claims, or an explicit fact-check request — upgrade citations to evidence:

① **Attach one verbatim quote per source.** Save extracted page text, then attach
the sentence(s) carrying each claim:

```bash
python "$S" quote 1 --text "Ice is about 9% less dense than liquid water." --from page1.txt
```

Quote is accepted only when verbatim in evidence text (ignoring whitespace,
case, and markdown markup; `_[ERAP1](https://…)_` matches visible prose), so a
paraphrase/misremembered figure cannot pose as evidence. Copy-paste fetched text;
never retype. Quote reader-visible text; matcher handles extractor markup and
escaped asterisks.

② **Flag model-knowledge claims with `[unverified]`.** A load-bearing unsourced
claim gets the marker, not a citation:

```
The refactor likely predates the 2.0 release.[unverified]
```

`verify --min-coverage` counts `[unverified]` as covered: goal = declared
provenance, not citation on every sentence. Check key claims when possible;
`[unverified]` is only for genuinely uncheckable claims. If most of a fact-check
deliverable is `[unverified]`, say so in its summary.

③ **Cross-check disputed facts** against a second independent source. When
sources disagree, cite both readings with IDs + quotes and state which you
weight and why. One source reports; two corroborate.

④ **Verify with the evidence gate and render the evidence block:**

```bash
python "$S" verify report.md --evidence --min-coverage 0.5
python "$S" render --style evidence --replace-in report.md
```

`--evidence` fails any cited source without a quote. `evidence` render prints
quotes beneath each URL: claim → source → exact support. `--replace-in <draft>`
rewrites Sources in place idempotently after new quotes; `--cited-in` prints to
stdout. Both emit `## Sources`; `--style plain` emits `Sources:`.

**`--min-coverage` counts:** `sentences with declared provenance / prose sentences`. Prose = non-empty 4+ word fragments after Sources; headings (`#`),
table rows (`|`), and fenced code are removed; blockquote markers are stripped.
`[n]` or `[unverified]` declares provenance; both on one sentence count once.
Run `verify` without a threshold first; choose a threshold from `info: stats:`.

## Pitfalls

- **Registering after writing.** Populate ledger from tool output, not the draft;
  later reconstruction reintroduces hallucinated-URL risk.
- **Renumbering mid-task.** IDs are ledger identities; if a draft cites `[4]`,
  `[4]` stays that source. Never hand-edit IDs; run `reset` only between tasks.
- **Retyping Sources URLs.** Always `render`; hand-typed URL = unverified claim.
- **Citing a search snippet as page content.** `web_search` supports only its
  literal description; use `web_extract` when the claim needs page text.
- **Over-citing.** Three IDs/sentence is the ceiling; citing every clause makes
  text unreadable and hides which source carries the claim.
- **Citing ledger in code/config.** Put source comments in prose deliverables/doc
  headers, not generated code.
- **Parallel subagents.** Each subagent has its own workdir; share one ledger with
  `--ledger` or `HERMES_CITATION_LEDGER` when merging outputs, or IDs collide.
- **Quoting snippets.** Evidence quotes require extracted page text, not a search
  description: `web_extract`, save text, then `quote --from` it.
- **Paraphrasing `quote --text`.** Verbatim check rejects it; find the actual sentence.
- **Using `[unverified]` as escape.** Reserve for genuinely unsourceable claims;
  mostly `[unverified]` means retrieve more, then state the limitation.
- **Hand-editing Sources.** Use `render --replace-in <draft>`; manual slicing can
  create stale/duplicate blocks that `verify` flags.

## Verification

```bash
python "$S" verify report.md --strict --min-coverage 0.5
```

Green means: every `[n]` in the draft exists in the ledger, the Sources block
lists exactly the cited ids with the ledger's URLs, and the cited share of
source-bearing sentences meets the threshold. Read the warnings even when the
exit code is 0 — uncited registered sources usually mean a claim lost its
attribution during editing.
