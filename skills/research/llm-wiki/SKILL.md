---
name: llm-wiki
description: "Karpathy's LLM Wiki: build/query interlinked markdown KB."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, research, notes, markdown, rag-alternative]
    category: research
    related_skills: [obsidian, arxiv]
---

# Karpathy's LLM Wiki

role: persistent interlinked-markdown knowledge-base curator
do: initialize/orient wiki; ingest immutable sources; create/update/cross-link pages; query/synthesize; lint/audit; archive; maintain index/log/schema
inputs: `WIKI_PATH` or `~/wiki`, URLs/files/pastes, domain/taxonomy, query, existing wiki state
outputs: `SCHEMA.md`, `index.md`, append-only `log.md`, raw sources, entity/concept/comparison/query pages, lint findings
¬: modify `raw/`; skip orientation; duplicate pages; use tags outside taxonomy; omit index/log/cross-links/frontmatter; silently overwrite contradictions; expose passwords

Build a persistent, compounding knowledge base as interlinked markdown files,
based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
The wiki compiles knowledge once, keeps it current, and preserves links,
contradictions, and synthesis. Human curates sources/directs analysis; agent
summarizes, cross-references, files, and maintains consistency.

## When to Use

- create/start a wiki or knowledge base
- ingest/add/process a source into an existing wiki
- answer a question when a configured wiki exists
- lint, audit, or health-check a wiki
- reference a wiki/knowledge base/notes for research

## Prerequisites

- Markdown-capable directory; no database or special tooling
- `WIKI_PATH` optional; otherwise `~/wiki`
- `web_extract` for URL/PDF capture; `read_file`, `write_file`, `search_files`,
  `execute_code`, and `terminal` for operations
- optional Obsidian desktop/headless; headless requires Node.js 22+ and Sync

## Wiki Location

Set via `WIKI_PATH` (for example in `${HERMES_HOME:-~/.hermes}/.env`); unset →
`~/wiki`:

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

## Architecture

```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log (append-only, rotated yearly)
├── raw/                # Layer 1: Immutable source material
│   ├── articles/       # Web articles, clippings
│   ├── papers/         # PDFs, arxiv papers
│   ├── transcripts/    # Meeting notes, interviews
│   └── assets/         # Images, diagrams referenced by sources
├── entities/           # Layer 2: Entity pages (people, orgs, products, models)
├── concepts/           # Layer 2: Concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
└── queries/            # Layer 2: Filed query results worth keeping
```

Layer 1 raw sources = immutable; read, never modify. Layer 2 wiki pages = agent
owned. Layer 3 schema = `SCHEMA.md` conventions/taxonomy.

## Procedure

### 1. Resume an Existing Wiki (every session)

1. Read `SCHEMA.md`; learn domain, conventions, taxonomy.
2. Read `index.md`; learn pages and summaries.
3. Read last 20-30 `log.md` entries; understand recent work.
4. For 100+ pages, `search_files` for the active topic before creating anything.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
# Orientation reads at session start
read_file "$WIKI/SCHEMA.md"
read_file "$WIKI/index.md"
read_file "$WIKI/log.md" offset=<last 30 lines>
```

Only then ingest/query/lint. Orientation prevents duplicate pages, missing
links, schema contradictions, and repeated logged work.

### 2. Initialize a New Wiki

1. Resolve `WIKI_PATH`, or ask user; default `~/wiki`.
2. Create the architecture above.
3. Ask the domain, specifically.
4. Write customized `SCHEMA.md`.
5. Write sectioned `index.md`.
6. Write creation entry in `log.md`.
7. Confirm readiness and suggest first sources.

#### `SCHEMA.md` Template

Adapt domain; schema constrains behavior and consistency:

```markdown
# Wiki Schema

## Domain
[What this wiki covers — e.g., "AI/ML research", "personal health", "startup intelligence"]

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]`
  at the end of paragraphs whose claims come from a specific source. This lets a reader trace each
  claim back without re-reading the whole raw file. Optional on single-source pages where the
  `sources:` frontmatter is enough.

## Frontmatter
  ```yaml
  ---
  title: Page Title
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  type: entity | concept | comparison | query | summary
  tags: [from taxonomy below]
  sources: [raw/articles/source-name.md]
  # Optional quality signals:
  confidence: high | medium | low        # how well-supported the claims are
  contested: true                        # set when the page has unresolved contradictions
  contradictions: [other-page-slug]      # pages this one conflicts with
  ---
  ```

`confidence` and `contested` are optional but recommended for opinion-heavy or fast-moving
 topics. Lint surfaces `contested: true` and `confidence: low` pages for review so weak claims
don't silently harden into accepted wiki fact.

### raw/ Frontmatter

Raw sources ALSO get a small frontmatter block so re-ingests can detect drift:

```yaml
---
source_url: https://example.com/article   # original URL, if applicable
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

The `sha256:` lets a future re-ingest of the same URL skip processing when content is unchanged,
and flag drift when it has changed. Compute over the body only (everything after the closing
`---`), not the frontmatter itself.

## Tag Taxonomy
[Define 10-20 top-level tags for the domain. Add new tags here BEFORE using them.]

Example for AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine-tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed,
add it here first, then use it. This prevents tag sprawl.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`, remove from index

## Entity Pages
One page per notable entity. Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities ([[wikilinks]])
- Source references

## Concept Pages
One page per concept or topic. Include:
- Definition / explanation
- Current state of knowledge
- Open questions or debates
- Related concepts ([[wikilinks]])

## Comparison Pages
Side-by-side analyses. Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Verdict or synthesis
- Sources

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
```

#### `index.md` Template

Section by type; one line per entry: wikilink + summary.

```markdown
# Wiki Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

Scaling: section >50 entries → split by first letter/sub-domain; index >200 total
→ create `_meta/topic-map.md` grouped by theme.

#### `log.md` Template

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, index.md, log.md
```

### 3. Ingest a Source

For URL, file, or paste:

1. Capture immutable raw source:
   - URL → `web_extract`; save `raw/articles/`
   - PDF → `web_extract`; save `raw/papers/`
   - paste → appropriate `raw/` directory
   - descriptive name, e.g. `raw/articles/karpathy-llm-wiki-2026.md`
   - add `source_url`, `ingested`, and body `sha256`
   - re-ingest: recompute/compare; identical → skip; changed → flag/update
2. Discuss takeaways with user; skip in automated/cron contexts.
3. Search `index.md` and use `search_files` for existing entities/concepts.
4. Create/update pages at thresholds; bump `updated`; apply contradiction policy.
5. Cross-link every new/updated page to ≥2 other pages and check backlinks.
6. Use taxonomy tags only; add new tags to `SCHEMA.md` first.
7. For 3+ source synthesis, add paragraph provenance markers.
8. Set `confidence: medium|low` for opinion-heavy/fast-moving/single-source claims;
   reserve `high` for multi-source support.
9. Update `index.md` alphabetically, total count, date; append
   `## [YYYY-MM-DD] ingest | Source Title` + every created/updated file to `log.md`.
10. Report every changed file. One source may update 5-15 pages; this is expected.

### 4. Query

1. Read `index.md` for relevant pages.
2. For 100+ pages, `search_files` all `.md` for key terms.
3. Read relevant pages with `read_file`.
4. Synthesize and cite wiki pages: `Based on [[page-a]] and [[page-b]]...`.
5. File substantial comparison/deep dive/novel synthesis in `queries/` or
   `comparisons/`; do not file trivial lookups.
6. Log query and whether it was filed.

### 5. Lint / Health Check

Run all checks and report paths/actions:

1. Orphans: pages in `entities/`, `concepts/`, `comparisons/`, `queries/` with no inbound wikilinks.
2. Broken wikilinks: `[[links]]` whose target page is absent.
3. Index completeness: every wiki page listed in `index.md`.
4. Frontmatter: `title`, `created`, `updated`, `type`, `tags`, `sources`; tags in taxonomy.
5. Stale content: `updated` >90 days older than newest source mentioning same entities.
6. Contradictions: conflicting same-topic claims; surface `contested: true`/
   `contradictions:` pages for user review.
7. Quality: list `confidence: low` and single-source pages lacking confidence.
8. Source drift: recompute raw body `sha256`; flag mismatch, not hard error.
9. Page size: flag pages >200 lines.
10. Tag audit: list tags not in `SCHEMA.md` taxonomy.
11. Log rotation: >500 entries → rotate.
12. Group findings severity: broken links > orphans > source drift > contested >
    stale > style.
13. Append `## [YYYY-MM-DD] lint | N issues found` to `log.md`.

```python
# Use execute_code for this — programmatic scan across all wiki pages
import os, re
from collections import defaultdict
wiki = "<WIKI_PATH>"
# Scan all .md files in entities/, concepts/, comparisons/, queries/
# Extract all [[wikilinks]] — build inbound link map
# Pages with zero inbound links are orphans
```

## Working with the Wiki

### Searching

```bash
# Find pages by content
search_files "transformer" path="$WIKI" file_glob="*.md"

# Find pages by filename
search_files "*.md" target="files" path="$WIKI"

# Find pages by tag
search_files "tags:.*alignment" path="$WIKI" file_glob="*.md"

# Recent activity
read_file "$WIKI/log.md" offset=<last 20 lines>
```

### Bulk Ingest

1. Read all sources first.
2. Identify entities/concepts across all sources.
3. Check existing pages in one search pass.
4. Create/update pages in one pass.
5. Update `index.md` once.
6. Write one batch log entry.

### Archiving

1. Create `_archive/` if absent.
2. Move page to `_archive/` preserving original path, e.g.
   `_archive/entities/old-page.md`.
3. Remove from `index.md`.
4. Replace inbound wikilinks with plain text + `(archived)`.
5. Log archive action.

### Obsidian Integration

The directory is an Obsidian vault: wikilinks are clickable; Graph View shows the
network; YAML frontmatter powers Dataview; `raw/assets/` stores `![[image.png]]`.
Set attachment folder `raw/assets/`; enable Wikilinks; install Dataview for:
`TABLE tags FROM "entities" WHERE contains(tags, "company")`.
If using the Obsidian skill, set `OBSIDIAN_VAULT_PATH` = wiki path.

### Obsidian Headless (servers and headless machines)

Use `obsidian-headless` on display-less hosts; Sync connects agent-written wiki
with Obsidian desktop elsewhere.

```bash
# Requires Node.js 22+
npm install -g obsidian-headless

# Login (requires Obsidian account with Sync subscription)
ob login --email <email> --password '<password>'

# Create a remote vault for the wiki
ob sync-create-remote --name "LLM Wiki"

# Connect the wiki directory to the vault
cd ~/wiki
ob sync-setup --vault "<vault-id>"

# Initial sync
ob sync

# Continuous sync (foreground — use systemd for background)
ob sync --continuous
```

```ini
# ~/.config/systemd/user/obsidian-wiki-sync.service
[Unit]
Description=Obsidian LLM Wiki Sync
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/path/to/ob sync --continuous
WorkingDirectory=%h/wiki
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsidian-wiki-sync
# Enable linger so sync survives logout:
sudo loginctl enable-linger $USER
```

## Pitfalls

- raw sources immutable; corrections belong in wiki pages
- orient first: `SCHEMA.md` + `index.md` + recent `log.md`
- index/log are the navigation backbone; update both every operation
- passing mention/footnote does not meet Page Thresholds
- every page needs ≥2 cross-links; frontmatter enables search/staleness checks
- taxonomy tags only; add new tags to `SCHEMA.md` first
- split pages >200 lines; keep pages scannable
- ask before ingest that would touch 10+ existing pages
- rotate `log.md` at 500 entries and check during lint
- preserve both sides of contradictions with dates/sources; flag review
- shell/headless sync credentials are user-managed; never expose passwords

## Verification

- existing wiki: schema/index/recent log read before operation
- new wiki: architecture + domain schema + index + creation log exist
- raw capture has frontmatter and body hash; raw files unchanged after ingest
- every created/updated page meets frontmatter, threshold, tags, and ≥2-link rules
- index count/date and log entry list all changed files
- query cites pages; substantial answer filed, trivial answer not
- lint reports broken links/orphans/drift/stale/contradictions/quality/size/tags/log
- archive removes index entry and repairs inbound links

## Related Tools

[llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) is a Node.js CLI
for batch-compiling sources into an Obsidian-compatible concept wiki. Use this
skill for agent-in-loop curation; use `llmwiki` for batch compilation. Trade-offs:
the compiler owns page generation and is tuned for small corpora.
