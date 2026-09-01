---
name: research-paper-writing
title: Research Paper Writing Pipeline
description: "Write ML papers for NeurIPS/ICML/ICLR: design→submit."
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [semanticscholar, arxiv, habanero, requests, scipy, numpy, matplotlib, SciencePlots]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Paper Writing, Experiments, ML, AI, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, Citations, Statistical Analysis]
    category: research
    related_skills: [arxiv, subagent-driven-development]
    requires_toolsets: [terminal, files]
---

# Research Paper Writing Pipeline

role: end-to-end ML/AI research-paper pipeline operator
do: set up project; review literature; design/run/monitor/analyze experiments; draft/review/revise paper; prepare submission; ship post-acceptance artifacts
inputs: research idea/codebase, claims, data/results, target venue, compute/human-evaluation budget, reviews, deadlines
outputs: reproducible experiments/journal, verified citations/BibTeX, LaTeX/PDF/figures/tables, reviews/rebuttal, code release/poster/talk/blog
¬: hallucinate citations/results; run experiments without claim mapping; lose provenance; ignore negative results, statistics, anonymity, venue limits, or ethics; commit secrets; silently choose a consequential framing

End-to-end pipeline for publication-ready ML/AI papers targeting **NeurIPS,
ICML, ICLR, ACL, AAAI, and COLM**. The lifecycle is iterative: results trigger
experiments; reviews trigger analysis/revision; post-acceptance produces public
artifacts.

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

## When to Use

- start a paper from an idea or existing codebase
- design, run, monitor, or analyze claim-supporting experiments
- write/revise any paper section
- prepare submission to a conference/workshop
- respond to reviews with experiments/revisions
- convert between conference formats
- write theory, survey, benchmark, or position papers
- design human evaluations for NLP, HCI, or alignment research
- prepare posters, talks, code releases, or other post-acceptance deliverables

## Prerequisites

- repository/workspace, version control, and target data/code
- Python dependencies in frontmatter as needed: `semanticscholar`, `arxiv`,
  `habanero`, `requests`, `scipy`, `numpy`, `matplotlib`, `SciencePlots`
- LaTeX toolchain (`pdflatex`/`latexmk`/`bibtex`), `chktex`, and venue template
  for PDF work
- compute/API/human-evaluation budget; target venue/deadline when known
- Hermes `terminal`, `read_file`, `write_file`, `patch`, `web_search`,
  `web_extract`, `delegate_task`, `todo`, `memory`, and optional `cronjob`

## Operating Rules

1. Be proactive: draft with flagged uncertainties; block only when venue is
   unclear, framings conflict, results are incomplete, or user requests review first.
2. Never hallucinate citations; AI-generated citations have ~40% error rate;
   fetch programmatically and mark gaps `[CITATION NEEDED]`.
3. Paper = story, not experiment collection; state one contribution sentence;
   map every experiment to a claim.
4. Commit each completed experiment batch and meaningful draft update with a
   descriptive message; git history = experiment history.

### Proactivity and Collaboration

**Default: draft first, ask with the draft.**

| Confidence Level | Action |
|-----------------|--------|
| **High** (clear repo, obvious contribution) | Write full draft, deliver, iterate on feedback |
| **Medium** (some ambiguity) | Write draft with flagged uncertainties, continue |
| **Low** (major unknowns) | Ask 1-2 targeted questions via `clarify`, then draft |

| Section | Draft Autonomously? | Flag With Draft |
|---------|-------------------|-----------------|
| Abstract | Yes | "Framed contribution as X — adjust if needed" |
| Introduction | Yes | "Emphasized problem Y — correct if wrong" |
| Methods | Yes | "Included details A, B, C — add missing pieces" |
| Experiments | Yes | "Highlighted results 1, 2, 3 — reorder if needed" |
| Related Work | Yes | "Cited papers X, Y, Z — add any I missed" |

## Procedure

### Phase 0 — Project Setup

**Goal:** establish workspace, understand existing work, identify contribution.

#### 0.1 Explore the repository

```bash
# Understand project structure
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

Inspect:

- `README.md` for overview/claims
- `results/`, `outputs/`, `experiments/` for findings
- `configs/` for settings
- `.bib` files, drafts, notes

#### 0.2 Organize the workspace

```
workspace/
  paper/               # LaTeX source, figures, compiled PDFs
  experiments/         # Experiment runner scripts
  code/                # Core method implementation
  results/             # Raw experiment results (auto-generated)
  tasks/               # Task/benchmark definitions
  human_eval/          # Human evaluation materials (if needed)
```

#### 0.3 Version control

```bash
git init  # if not already
git remote add origin <repo-url>
git checkout -b paper-draft  # or main
```

Every completed experiment batch gets a descriptive commit, e.g.:

```
Add Monte Carlo constrained results (5 runs, Sonnet 4.6, policy memo task)
Add Haiku baseline comparison: autoreason vs refinement baselines at cheap model tier
```

#### 0.4 Identify the contribution

Before writing, answer **What** (single contribution), **Why** (supporting
evidence), and **So what** (reader value). Propose:

> Based on my understanding, the main contribution is: [one sentence]. The key results show [Y]. Is this the framing you want?

#### 0.5 Persistent TODO

Use the `todo` tool:

```
Research Paper TODO:
- [ ] Define one-sentence contribution
- [ ] Literature review (related work + baselines)
- [ ] Design core experiments
- [ ] Run experiments
- [ ] Analyze results
- [ ] Write first draft
- [ ] Self-review (simulate reviewers)
- [ ] Revise based on review
- [ ] Submission prep
```

Update after phase transitions; this is cross-session state.

#### 0.6 Compute budget

Estimate before experiments; add 30-50% contingency:

```
Compute Budget Checklist:
- [ ] API costs: (model price per token) × (estimated tokens per run) × (number of runs)
- [ ] GPU hours: (time per experiment) × (number of experiments) × (number of seeds)
- [ ] Human evaluation costs: (annotators) × (hours) × (hourly rate)
- [ ] Total budget ceiling and contingency (add 30-50% for reruns)
```

Track actual spend:

```python
# Simple cost tracker pattern
import json, os
from datetime import datetime

COST_LOG = "results/cost_log.jsonl"

def log_cost(experiment: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "experiment": experiment,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

Tight budget → pilot with 1-2 seeds/subset; debug with cheaper models; run final
sweeps on target models.

#### 0.7 Multi-author coordination

Most papers have 3-10 authors:

| Workflow | Tool | When to Use |
|----------|------|-------------|
| **Overleaf** | Browser-based | Multiple authors editing simultaneously, no git experience |
| **Git + LaTeX** | `git` with `.gitignore` for aux files | Technical teams, need branch-based review |
| **Overleaf + Git sync** | Overleaf premium | Best of both — live collab with version history |

Assign one primary author per section; others comment. Agree early on:

```
Author Coordination Checklist:
- [ ] Agree on section ownership (who writes what)
- [ ] Set up shared workspace (Overleaf or git repo)
- [ ] Establish notation conventions (before anyone writes)
- [ ] Schedule internal review rounds (not just at the end)
- [ ] Designate one person for final formatting pass
- [ ] Agree on figure style (colors, fonts, sizes) before creating figures
```

LaTeX conventions: `\method{}` naming macro; `\citet{}` vs `\citep{}`;
vector/matrix notation; British vs American spelling.

### Phase 1 — Literature Review

**Goal:** find related work/baselines and gather verified citations.

#### 1.1 Seed papers

```bash
# Via terminal:
grep -r "arxiv\|doi\|cite" --include="*.md" --include="*.bib" --include="*.py"
find . -name "*.bib"
```

#### 1.2 Search

Load `arxiv` for REST search, Semantic Scholar graphs, author profiles, and
BibTeX: `skill_view("arxiv")`. Use `web_search` for broad discovery and
`web_extract` for specific papers:

```
# Via web_search:
web_search("[main technique] + [application domain] site:arxiv.org")
web_search("[baseline method] comparison ICML NeurIPS 2024")

# Via web_extract (for specific papers):
web_extract("https://arxiv.org/abs/2303.17651")
```

Additional queries:

```
Search queries:
- "[main technique] + [application domain]"
- "[baseline method] comparison"
- "[problem name] state-of-the-art"
- Author names from existing citations
```

Optional Exa MCP:

```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```

#### 1.2b Breadth then depth

```
Iterative Literature Search:

Round 1 (Breadth): 4-6 parallel queries covering different angles
  - "[method] + [domain]"
  - "[problem name] state-of-the-art 2024 2025"
  - "[baseline method] comparison"
  - "[alternative approach] vs [your approach]"
  → Collect papers, extract key concepts and terminology

Round 2 (Depth): Generate follow-up queries from Round 1 learnings
  - New terminology discovered in Round 1 papers
  - Papers cited by the most relevant Round 1 results
  - Contradictory findings that need investigation
  → Collect papers, identify remaining gaps

Round 3 (Targeted): Fill specific gaps
  - Missing baselines identified in Rounds 1-2
  - Concurrent work (last 6 months, same problem)
  - Key negative results or failed approaches
  → Stop when new queries return mostly papers you've already seen
```

Stop at >80% already-seen papers; normally 2-3 rounds, surveys 4-5. For agent
workflows, delegate rounds in parallel, deduplicate, and generate next queries
from combined learnings.

#### 1.3 Verify every citation

**Never generate BibTeX from memory.** Per citation:

```
Citation Verification (MANDATORY per citation):
1. SEARCH → Query Semantic Scholar or Exa MCP with specific keywords
2. VERIFY → Confirm paper exists in 2+ sources (Semantic Scholar + arXiv/CrossRef)
3. RETRIEVE → Get BibTeX via DOI content negotiation (programmatically, not from memory)
4. VALIDATE → Confirm the claim you're citing actually appears in the paper
5. ADD → Add verified BibTeX to bibliography
If ANY step fails → mark as [CITATION NEEDED], inform scientist
```

```python
# Fetch BibTeX via DOI
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    response.raise_for_status()
    return response.text
```

Unverified placeholder:

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: Verify this citation exists
```

Tell the scientist how many placeholders remain. See
[references/citation-workflow.md](references/citation-workflow.md) for APIs and
`CitationManager`.

#### 1.4 Organize related work

Group by methodology, not paper-by-paper:

- Good: “One line of work uses X's assumption [refs] whereas we use Y's assumption because...”
- Bad: “Smith et al. introduced X. Jones et al. introduced Y. We combine both.”

### Phase 2 — Experiment Design

**Goal:** every experiment answers a claim-specific question.

#### 2.1 Map claims to experiments

| Claim | Experiment | Expected Evidence |
|-------|------------|-------------------|
| "Our method outperforms baselines" | Main comparison (Table 1) | Win rate, statistical significance |
| "Effect is larger for weaker models" | Model scaling study | Monotonic improvement curve |
| "Convergence requires scope constraints" | Constrained vs unconstrained | Convergence rate comparison |

No claim mapping → do not run.

#### 2.2 Baselines

Include:

- naive: simplest approach
- strong: best known existing method
- ablation: method minus one component
- compute-matched: equal compute, different allocation

Reviewers use baseline strength to distinguish accepted from rejected papers.

#### 2.3 Evaluation protocol

Specify before running: metrics and higher/lower direction; aggregation across
runs/tasks; statistical tests; sample sizes (runs/problems/tasks).

#### 2.4 Experiment scripts

Incremental saving enables crash recovery:

```python
# Save after each problem/task
result_path = f"results/{task}/{strategy}/result.json"
if os.path.exists(result_path):
    continue  # Skip already-completed work
# ... run experiment ...
with open(result_path, 'w') as f:
    json.dump(result, f, indent=2)
```

Preserve all intermediate outputs:

```
results/<experiment>/
  <task>/
    <strategy>/
      final_output.md          # Final result
      history.json             # Full trajectory
      pass_01/                 # Per-iteration artifacts
        version_a.md
        version_b.md
        critic.md
```

Separate generation/evaluation/visualization:

```
run_experiment.py              # Core experiment runner
run_baselines.py               # Baseline comparison
run_comparison_judge.py        # Blind evaluation
analyze_results.py             # Statistical analysis
make_charts.py                 # Visualization
```

See [references/experiment-patterns.md](references/experiment-patterns.md) for
patterns, cron monitoring, and recovery.

#### 2.5 Human evaluation

Design before automated runs when metrics miss fluency/helpfulness/safety,
claims concern readability/preference/trust, or ACL/EMNLP venues expect it.

| Decision | Options | Guidance |
|----------|---------|----------|
| **Annotator type** | Expert, crowdworker, end-user | Match to what your claims require |
| **Scale** | Likert (1-5), pairwise comparison, ranking | Pairwise is more reliable than Likert for LLM outputs |
| **Sample size** | Per annotator and total items | Power analysis or minimum 100 items, 3+ annotators |
| **Agreement metric** | Cohen's kappa, Krippendorff's alpha, ICC | Krippendorff's alpha for >2 annotators; report raw agreement too |
| **Platform** | Prolific, MTurk, internal team | Prolific for quality; MTurk for scale; internal for domain expertise |

```
- [ ] Clear task description with examples (good AND bad)
- [ ] Decision criteria for ambiguous cases
- [ ] At least 2 worked examples per category
- [ ] Attention checks / gold standard items (10-15% of total)
- [ ] Qualification task or screening round
- [ ] Estimated time per item and fair compensation (>= local minimum wage)
- [ ] IRB/ethics review if required by your institution
```

Report annotator count/qualifications, agreement metric/value, compensation and
hourly rate, interface/screenshot (appendix), and total annotation time. See
[references/human-evaluation.md](references/human-evaluation.md).

### Phase 3 — Experiment Execution & Monitoring

**Goal:** reliable runs, status visibility, failure recovery, committed results.

#### 3.1 Launch

```bash
nohup python run_experiment.py --config config.yaml > logs/experiment_01.log 2>&1 &
echo $!  # Record the PID
```

Parallel independent runs are valid, but 4+ concurrent calls against one API
may slow all runs through rate limits.

#### 3.2 Cron monitoring

```
Monitor Prompt Template:
1. Check if process is still running: ps aux | grep <pattern>
2. Read last 30 lines of log: tail -30 <logfile>
3. Check for completed results: ls <result_dir>
4. If results exist, read and report: cat <result_file>
5. If all done, commit: git add -A && git commit -m "<descriptive message>" && git push
6. Report in structured format (tables with key metrics)
7. Answer the key analytical question for this experiment
```

No changes since last check → exactly `[SILENT]`; report only news.

#### 3.3 Failure handling

| Failure | Detection | Recovery |
|---------|-----------|----------|
| API rate limit / credit exhaustion | 402/429 errors in logs | Wait, then re-run (scripts skip completed work) |
| Process crash | PID gone, incomplete results | Re-run from last checkpoint |
| Timeout on hard problems | Process stuck, no log progress | Kill and skip, note in results |
| Wrong model ID | Errors referencing model name | Fix ID and re-run |

Scripts must skip existing results; reruns are safe/efficient.

#### 3.4 Commit completed results

```bash
git add -A
git commit -m "Add <experiment name>: <key finding in 1 line>"
git push
```

#### 3.5 Experiment journal

Git records file changes; the journal records reasoning and the exploration tree:

```json
// experiment_journal.jsonl — append one entry per experiment attempt
{
  "id": "exp_003",
  "parent": "exp_001",
  "timestamp": "2025-05-10T14:30:00Z",
  "hypothesis": "Adding scope constraints will fix convergence failure from exp_001",
  "plan": "Re-run autoreason with max_tokens=2000 and fixed structure template",
  "config": {"model": "haiku", "strategy": "autoreason", "max_tokens": 2000},
  "status": "completed",
  "result_path": "results/exp_003/",
  "key_metrics": {"win_rate": 0.85, "convergence_rounds": 3},
  "analysis": "Scope constraints fixed convergence. Win rate jumped from 0.42 to 0.85.",
  "next_steps": ["Try same constraints on Sonnet", "Test without structure template"],
  "figures": ["figures/exp003_convergence.pdf"]
}
```

Use the tree to choose the path supporting claims; record dead ends as ablations
or negative results. Snapshot code per run:

```bash
cp experiment.py results/exp_003/experiment_snapshot.py
```

### Phase 4 — Result Analysis

**Goal:** aggregate metrics, quantify uncertainty, identify the paper story.

#### 4.1 Aggregate

Load all result files, compute per-task/aggregate metrics, and generate tables:

```python
# Standard analysis pattern
import json, os
from pathlib import Path

results = {}
for result_file in Path("results/").rglob("result.json"):
    data = json.loads(result_file.read_text())
    strategy = result_file.parent.name
    task = result_file.parent.parent.name
    results.setdefault(strategy, {})[task] = data

# Compute aggregate metrics
for strategy, tasks in results.items():
    scores = [t["score"] for t in tasks.values()]
    print(f"{strategy}: mean={np.mean(scores):.1f}, std={np.std(scores):.1f}")
```

#### 4.2 Statistics

Always report error bars (SD or SE, specify), 95% CIs, pairwise tests (McNemar
for two methods), and effect sizes (Cohen's d or h). See
[references/experiment-patterns.md](references/experiment-patterns.md).

#### 4.3 Identify the story

Answer: main finding (one sentence), surprise, failure, and required follow-up.

| Situation | Action | Venue Fit |
|-----------|--------|-----------|
| Hypothesis wrong but **why** is informative | Frame paper around the analysis of why | NeurIPS, ICML (if analysis is rigorous) |
| Method doesn't beat baselines but **reveals something new** | Reframe contribution as understanding/analysis | ICLR (values understanding), workshop papers |
| Clean negative result on popular claim | Write it up — the field needs to know | NeurIPS Datasets & Benchmarks, TMLR, workshops |
| Results inconclusive, no clear story | Pivot — run different experiments or reframe | Don't force a paper that isn't there |

Negative-result paper: lead with the belief and test rationale; make methods
airtight; present null result/statistics; explain why; discuss field implications.
Venues welcoming negative results include NeurIPS Datasets & Benchmarks, TMLR,
ML Reproducibility Challenge, and workshops.

#### 4.4 Figures and tables

Figures: vector PDF (`plt.savefig('fig.pdf')`); Okabe-Ito or Paul Tol palette;
self-contained captions; no title inside figure. Tables: `booktabs`; bold best
value; direction symbols; consistent decimal precision.

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

#### 4.5 Decide: more experiments or write

| Situation | Action |
|-----------|--------|
| Core claims supported, results significant | Move to Phase 5 (writing) |
| Results inconclusive, need more data | Back to Phase 2 (design) |
| Unexpected finding suggests new direction | Back to Phase 2 (design) |
| Missing one ablation reviewers will ask for | Run it, then Phase 5 |
| All experiments done but some failed | Note failures, move to Phase 5 |

#### 4.6 Experiment log (bridge to writeup)

Create `experiment_log.md`; commit it with described results:

```markdown
# Experiment Log

## Contribution (one sentence)
[The paper's main claim]

## Experiments Run

### Experiment 1: [Name]
- **Claim tested**: [Which paper claim this supports]
- **Setup**: [Model, dataset, config, number of runs]
- **Key result**: [One sentence with the number]
- **Result files**: results/exp1/final_info.json
- **Figures generated**: figures/exp1_comparison.pdf
- **Surprising findings**: [Anything unexpected]

### Experiment 2: [Name]
...

## Figures
| Filename | Description | Which section it belongs in |
|----------|-------------|-----------------------------|
| figures/main_comparison.pdf | Bar chart comparing all methods on benchmark X | Results, Figure 2 |
| figures/ablation.pdf | Ablation removing components A, B, C | Results, Figure 3 |
...

## Failed Experiments (document for honesty)
- [What was tried, why it failed, what it tells us]

## Open Questions
- [Anything the results raised that the paper should address]
```

### Iterative Refinement: Strategy Selection

Any paper draft, experiment script, or analysis may be refined. Choose strategy by
model/task:

| Your Situation | Strategy | Why |
|---------------|----------|-----|
| Mid-tier model + constrained task | **Autoreason** | Sweet spot. Generation-evaluation gap is widest. Baselines actively destroy weak model outputs. |
| Mid-tier model + open task | **Autoreason** with scope constraints added | Add fixed facts, structure, or deliverable to bound the improvement space. |
| Frontier model + constrained task | **Autoreason** | Wins 2/3 constrained tasks even at frontier. |
| Frontier model + unconstrained task | **Critique-and-revise** or **single pass** | Autoreason comes last. Model self-evaluates well enough. |
| Concrete technical task (system design) | **Critique-and-revise** | Direct find-and-fix loop is more efficient. |
| Template-filling task (one correct structure) | **Single pass** or **conservative** | Minimal decision space. Iteration adds no value. |
| Code with test cases | **Autoreason (code variant)** | Structured analysis of *why* it failed before fixing. Recovery rate 62% vs 43%. |
| Very weak model (Llama 8B class) | **Single pass** | Model too weak for diverse candidates. Invest in generation quality. |

Generation/evaluation gap:

```
Model Tier        │ Generation │ Self-Eval │ Gap    │ Autoreason Value
──────────────────┼────────────┼───────────┼────────┼─────────────────
Weak (Llama 8B)   │ Poor       │ Poor      │ Small  │ None — can't generate diverse candidates
Mid (Haiku 3.5)   │ Decent     │ Poor      │ LARGE  │ MAXIMUM — 42/42 perfect Borda
Mid (Gemini Flash)│ Decent     │ Moderate  │ Large  │ High — wins 2/3
Strong (Sonnet 4) │ Good       │ Decent    │ Medium │ Moderate — wins 3/5
Frontier (S4.6)   │ Excellent  │ Good       │ Small  │ Only with constraints
```

Gap is structural; as costs fall, frontier becomes mid-tier and the sweet spot
moves rather than disappearing.

Autoreason loop:

1. Critic finds problems in incumbent A (no fixes).
2. Author B revises A from critique.
3. Synthesizer merges A/B with randomized labels.
4. Three blind CoT judges rank A/B/AB by Borda.
5. Stop when A wins `k=2` consecutive passes.

Parameters: `k=2`; CoT judges always (3x faster convergence); temperature 0.8 authors/0.3 judges; incumbent
wins ties; every role is a fresh isolated agent. For paper drafts, give critic
actual data/result JSON/statistics, use ≥3 working judges, and constrain revision
to named weaknesses.

| Failure | Detection | Fix |
|---------|-----------|-----|
| No convergence (A never wins) | A wins <15% over 20+ passes | Add scope constraints to the task |
| Synthesis drift | Word counts grow unboundedly | Constrain structure and deliverable |
| Degradation below single pass | Baselines score higher than iterated output | Switch to single pass; model may be too weak |
| Overfitting (code) | High public-test pass, low private-test pass | Use structured analysis, not just test feedback |
| Broken judges | Parsing failures reduce panel below 3 | Fix parser before continuing |

See [references/autoreason-methodology.md](references/autoreason-methodology.md)
for prompts, Borda scoring, model guide, scope constraints, and compute budget.

### Phase 5 — Paper Drafting

The complete section order, LaTeX scaffolding, figure/table conventions,
abstract/intro formulas, and related-work positioning live in
`references/phase5-paper-drafting.md`; load with `read_file` at this phase.
Pair with `references/writing-guide.md` for prose rules.

### Phase 6 — Self-Review & Revision

**Goal:** simulate review, visual presentation, and claim verification before
submission.

#### 6.1 Ensemble reviews

Generate N=3-5 independent reviews with different models/temperatures; each sees
only the paper. Use negative bias; do not give benefit of doubt.

```
You are an expert reviewer for [VENUE]. You are critical and thorough.
If a paper has weaknesses or you are unsure about a claim, flag it clearly
and reflect that in your scores. Do not give the benefit of the doubt.

Review this paper according to the official reviewer guidelines. Evaluate:

1. Soundness (are claims well-supported? are baselines fair and strong?)
2. Clarity (is the paper well-written? could an expert reproduce it?)
3. Significance (does this matter to the community?)
4. Originality (new insights, not just incremental combination?)

Provide your review as structured JSON:
{
  "summary": "2-3 sentence summary",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1 (most critical)", "weakness 2", ...],
  "questions": ["question for authors 1", ...],
  "missing_references": ["paper that should be cited", ...],
  "soundness": 1-4,
  "presentation": 1-4,
  "contribution": 1-4,
  "overall": 1-10,
  "confidence": 1-5
}
```

Meta-review all reviews:

```
You are an Area Chair at [VENUE]. You have received [N] independent reviews
of a paper. Your job is to:

1. Identify consensus strengths and weaknesses across reviewers
2. Resolve disagreements by examining the paper directly
3. Produce a meta-review that represents the aggregate judgment
4. Use AVERAGED numerical scores across all reviews

Be conservative: if reviewers disagree on whether a weakness is serious,
treat it as serious until the authors address it.

Reviews:
[review_1]
[review_2]
...
```

Optional reflection: 2-3 rounds; stop on exact sentinel `I am done`. Use the
strongest available model independently from the writing model. Include 1-2 real
venue reviews for few-shot calibration when available; see
[references/reviewer-guidelines.md](references/reviewer-guidelines.md).

#### 6.1b Visual review

With a vision-capable model, review compiled PDF:

```
You are reviewing the visual presentation of this research paper PDF.
Check for:
1. Figure quality: Are plots readable? Labels legible? Colors distinguishable?
2. Figure-caption alignment: Does each caption accurately describe its figure?
3. Layout issues: Orphaned section headers, awkward page breaks, figures far from their references
4. Table formatting: Aligned columns, consistent decimal precision, bold for best results
5. Visual consistency: Same color scheme across all figures, consistent font sizes
6. Grayscale readability: Would the figures be understandable if printed in B&W?

For each issue, specify the page number and exact location.
```

#### 6.1c Claim verification

Extract every factual claim (numbers/comparisons/trends); trace each to an
experiment/result; compare paper number to result file; mark untraceable claims
`[VERIFY]`. Delegate to a fresh agent receiving only paper + raw results to avoid
confirmation bias.

#### 6.2 Prioritize

| Priority | Action |
|----------|--------|
| **Critical** (technical flaw, missing baseline) | Must fix. May require new experiments → back to Phase 2 |
| **High** (clarity issue, missing ablation) | Should fix in this revision |
| **Medium** (minor writing issues, extra experiments) | Fix if time allows |
| **Low** (style preferences, tangential suggestions) | Note for future work |

#### 6.3 Revision

For each critical/high issue: identify affected sections; draft fix; verify other
claims; update; re-check concern.

#### 6.4 Rebuttal

Point-by-point format:

```
> R1-W1: "The paper lacks comparison with Method X."

We thank the reviewer for this suggestion. We have added a comparison with 
Method X in Table 3 (revised). Our method outperforms X by 3.2pp on [metric] 
(p<0.05). We note that X requires 2x our compute budget.
```

Address every concern; lead strongest responses; concise/direct; include new
results; never defensive/dismissive; use `latexdiff`; thank specific actionable
feedback. Do not say “we respectfully disagree” or “out of scope” without
 evidence, and do not answer only strengths.

#### 6.5 Evolution snapshots

```
paper/
  paper.tex                    # Current working version
  paper_v1_first_draft.tex     # First complete draft
  paper_v2_post_review.tex     # After simulated review
  paper_v3_pre_submission.tex  # Final before submission
  paper_v4_camera_ready.tex    # Post-acceptance final
```

### Phase 7 — Submission Preparation

**Goal:** venue checklist, anonymity, format, clean compilation, release package.

#### 7.1 Venue checklist

See [references/checklists.md](references/checklists.md): NeurIPS 16-item;
ICML broader impact/reproducibility; ICLR LLM disclosure; ACL limitations;
universal pre-submission checklist.

#### 7.2 Anonymization

```
Anonymization Checklist:
- [ ] No author names or affiliations anywhere in the PDF
- [ ] No acknowledgments section (add after acceptance)
- [ ] Self-citations written in third person: "Smith et al. [1] showed..." not "We previously showed [1]..."
- [ ] No GitHub/GitLab URLs pointing to your personal repos
- [ ] Use Anonymous GitHub (https://anonymous.4open.science/) for code links
- [ ] No institutional logos or identifiers in figures
- [ ] No file metadata containing author names (check PDF properties)
- [ ] No "our previous work" or "in our earlier paper" phrasing
- [ ] Dataset names don't reveal institution (rename if needed)
- [ ] Supplementary materials don't contain identifying information
```

Check supplementary commit messages, watermarks, acknowledgments, and preprints;
posting before a double-blind deadline may expose identity.

#### 7.3 Formatting

```
Pre-Submission Format Check:
- [ ] Page limit respected (excluding references and appendix)
- [ ] All figures are vector (PDF) or high-res raster (600 DPI PNG)
- [ ] All figures readable in grayscale
- [ ] All tables use booktabs
- [ ] References compile correctly (no "?" in citations)
- [ ] No overfull hboxes in critical areas
- [ ] Appendix clearly labeled and separated
- [ ] Required sections present (limitations, broader impact, etc.)
```

#### 7.4 Pre-compilation validation

Run before `pdflatex`:

```bash
# 1. Lint with chktex (catches common LaTeX mistakes)
# Suppress noisy warnings: -n2 (sentence end), -n24 (parens), -n13 (intersentence), -n1 (command terminated)
chktex main.tex -q -n2 -n24 -n13 -n1

# 2. Verify all citations exist in .bib
# Extract \cite{...} from .tex, check each against .bib
python3 -c "
import re
tex = open('main.tex').read()
bib = open('references.bib').read()
cites = set(re.findall(r'\\\\cite[tp]?{([^}]+)}', tex))
for cite_group in cites:
    for cite in cite_group.split(','):
        cite = cite.strip()
        if cite and cite not in bib:
            print(f'WARNING: \\\\cite{{{cite}}} not found in references.bib')
"

# 3. Verify all referenced figures exist on disk
python3 -c "
import re, os
tex = open('main.tex').read()
figs = re.findall(r'\\\\includegraphics(?:\[.*?\])?{([^}]+)}', tex)
for fig in figs:
    if not os.path.exists(fig):
        print(f'WARNING: Figure file not found: {fig}')
"

# 4. Check for duplicate \label definitions
python3 -c "
import re
from collections import Counter
tex = open('main.tex').read()
labels = re.findall(r'\\\\label{([^}]+)}', tex)
dupes = {k: v for k, v in Counter(labels).items() if v > 1}
for label, count in dupes.items():
    print(f'WARNING: Duplicate label: {label} (appears {count} times)')
"
```

Fix all warnings before compilation; feed output to an agent for minimal fixes
when using delegated workflows.

#### 7.5 Final compilation

```bash
# Clean build
rm -f *.aux *.bbl *.blg *.log *.out *.pdf
latexmk -pdf main.tex

# Or manual (triple pdflatex + bibtex for cross-references)
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# Verify output exists and has content
ls -la main.pdf
```

First `.log` error guides recovery:

- Undefined control sequence → missing package/typo
- Missing $ inserted → math symbol outside math mode
- File not found → figure or `.sty` path
- Citation undefined → `.bib` missing or bibtex not run

#### 7.6 Venue-specific requirements

| Venue | Special Requirements |
|-------|---------------------|
| **NeurIPS** | Paper checklist in appendix, lay summary if accepted |
| **ICML** | Broader Impact Statement (after conclusion, doesn't count toward limit) |
| **ICLR** | LLM disclosure required, reciprocal reviewing agreement |
| **ACL** | Mandatory Limitations section, Responsible NLP checklist |
| **AAAI** | Strict style file — no modifications whatsoever |
| **COLM** | Frame contribution for language model community |

#### 7.7 Resubmission and format conversion

Never copy LaTeX preambles between templates:

```bash
# 1. Start fresh with target template
cp -r templates/icml2026/ new_submission/

# 2. Copy ONLY content sections (not preamble)
#    - Abstract text, section content, figures, tables, bib entries

# 3. Adjust for page limits
# 4. Add venue-specific required sections
# 5. Update references
```

| From → To | Page Change | Key Adjustments |
|-----------|-------------|-----------------|
| NeurIPS → ICML | 9 → 8 | Cut 1 page, add Broader Impact |
| ICML → ICLR | 8 → 9 | Expand experiments, add LLM disclosure |
| NeurIPS → ACL | 9 → 8 | Restructure for NLP conventions, add Limitations |
| ICLR → AAAI | 9 → 7 | Significant cuts, strict style adherence |
| Any → COLM | varies → 9 | Reframe for language model focus |

Cut pages: move proofs to appendix, condense related work, combine tables,
subfigures. Expand: ablations, limitations, baselines, qualitative examples.
After rejection, address concerns without a changes section or previous-submission
reference under blind review.

#### 7.8 Camera-ready

```
Camera-Ready Checklist:
- [ ] De-anonymize: add author names, affiliations, email addresses
- [ ] Add Acknowledgments section (funding, compute grants, helpful reviewers)
- [ ] Add public code/data URL (real GitHub, not anonymous)
- [ ] Address any mandatory revisions from meta-reviewer
- [ ] Switch template to camera-ready mode (if applicable — e.g., AAAI \anon → \camera)
- [ ] Add copyright notice if required by venue
- [ ] Update any "anonymous" placeholders in text
- [ ] Verify final PDF compiles cleanly
- [ ] Check page limit for camera-ready (sometimes differs from submission)
- [ ] Upload supplementary materials (code, data, appendix) to venue portal
```

#### 7.9 arXiv/preprint strategy

| Situation | Recommendation |
|-----------|---------------|
| Submitting to double-blind venue (NeurIPS, ICML, ACL) | Post to arXiv **after** submission deadline, not before. Posting before can technically violate anonymity policies, though enforcement varies. |
| Submitting to ICLR | ICLR explicitly allows arXiv posting before submission. But don't put author names in the submission itself. |
| Paper already on arXiv, submitting to new venue | Acceptable at most venues. Do NOT update arXiv version during review with changes that reference reviews. |
| Workshop paper | arXiv is fine at any time — workshops are typically not double-blind. |
| Want to establish priority | Post immediately if scooping is a concern — but accept the anonymity tradeoff. |

Categories:

| Category | Code | Best For |
|----------|------|----------|
| Machine Learning | `cs.LG` | General ML methods |
| Computation and Language | `cs.CL` | NLP, language models |
| Artificial Intelligence | `cs.AI` | Reasoning, planning, agents |
| Computer Vision | `cs.CV` | Vision models |
| Information Retrieval | `cs.IR` | Search, recommendation |

List primary + 1-2 genuinely relevant cross-lists. Versioning: v1 = submission;
v2 = post-acceptance/camera-ready, add “accepted at [Venue]”; do not post review-
responsive v2 during review.

```bash
# Check if your paper's title is already taken on arXiv
# (before choosing a title)
pip install arxiv
python -c "
import arxiv
results = list(arxiv.Search(query='ti:\"Your Exact Title\"', max_results=5).results())
print(f'Found {len(results)} matches')
for r in results: print(f'  {r.title} ({r.published.year})')
"
```

#### 7.10 Research code packaging

```
your-method/
  README.md              # Setup, usage, reproduction instructions
  requirements.txt       # Or environment.yml for conda
  setup.py               # For pip-installable packages
  LICENSE                # MIT or Apache 2.0 recommended for research
  configs/               # Experiment configurations
  src/                   # Core method implementation
  scripts/               # Training, evaluation, analysis scripts
    train.py
    evaluate.py
    reproduce_table1.sh  # One script per main result
  data/                  # Small data or download scripts
    download_data.sh
  results/               # Expected outputs for verification
```

```markdown
# [Paper Title]

Official implementation of "[Paper Title]" (Venue Year).

## Setup
[Exact commands to set up environment]

## Reproduction
To reproduce Table 1: `bash scripts/reproduce_table1.sh`
To reproduce Figure 2: `python scripts/make_figure2.py`

## Citation
[BibTeX entry]
```

```
- [ ] Code runs from a clean clone (test on fresh machine or Docker)
- [ ] All dependencies pinned to specific versions
- [ ] No hardcoded absolute paths
- [ ] No API keys, credentials, or personal data in repo
- [ ] README covers setup, reproduction, and citation
- [ ] LICENSE file present (MIT or Apache 2.0 for max reuse)
- [ ] Results are reproducible within expected variance
- [ ] .gitignore excludes data files, checkpoints, logs
```

Anonymous code:

```bash
# Use Anonymous GitHub for double-blind review
# https://anonymous.4open.science/
# Upload your repo → get an anonymous URL → put in paper
```

### Phase 8 — Post-Acceptance Deliverables

**Goal:** maximize impact through presentation and community artifacts.

#### 8.1 Poster

| Element | Guideline |
|---------|-----------|
| **Size** | Check venue requirements (typically 24"x36" or A0 portrait/landscape) |
| **Content** | Title, authors, 1-sentence contribution, method figure, 2-3 key results, conclusion |
| **Flow** | Top-left to bottom-right (Z-pattern) or columnar |
| **Text** | Title readable at 3m, body at 1m. No full paragraphs — bullet points only. |
| **Figures** | Reuse paper figures at higher resolution. Enlarge key result. |

Tools: LaTeX `beamerposter`, PowerPoint/Keynote, Figma, Canva. Order ≥2 weeks;
fabric posters are lighter; digital posters may be supported.

#### 8.2 Talk / spotlight

| Talk Type | Duration | Content |
|-----------|----------|---------|
| **Spotlight** | 5 min | Problem, approach, one key result. Rehearse to exactly 5 minutes. |
| **Oral** | 15-20 min | Full story: problem, approach, key results, ablations, limitations. |
| **Workshop talk** | 10-15 min | Adapt based on workshop audience — may need more background. |

Rules: one idea/slide; minimize text; animate key figures; final one-sentence
takeaway; backup slides for questions.

#### 8.3 Blog/social/project page

- X/Twitter thread: 5-8 tweets; lead result; include Figure 1/key result
- blog: 800-1500 words for practitioners; skip formalism; emphasize intuition/impact
- project page: HTML abstract, figures, demo, code, BibTeX; GitHub Pages

Post 1-2 days after proceedings or camera-ready arXiv appearance.

## Workshop & Short Papers

| Property | Workshop | Main Conference |
|----------|----------|-----------------|
| **Page limit** | 4-6 pages (typically) | 7-9 pages |
| **Review standard** | Lower bar for completeness | Must be complete, thorough |
| **Review process** | Usually single-blind or light review | Double-blind, rigorous |
| **What's valued** | Interesting ideas, preliminary results, position pieces | Complete empirical story with strong baselines |
| **arXiv** | Post anytime | Timing matters (see arXiv strategy) |
| **Contribution bar** | Novel direction, interesting negative result, work-in-progress | Significant advance with strong evidence |

Target workshops for early feedback, negative results, positions, replications,
or reproducibility reports.

### ACL Short Papers & Findings

| Type | Pages | What's Expected |
|------|-------|-----------------|
| **Long paper** | 8 | Complete study, strong baselines, ablations |
| **Short paper** | 4 | Focused contribution: one clear point with evidence |
| **Findings** | 8 | Solid work that narrowly missed main conference |

Short strategy: one claim supported thoroughly; write a focused paper, not a
compressed long paper.

## Paper Types Beyond Empirical ML

See [references/paper-types.md](references/paper-types.md) for detail.

### Theory

Structure: Introduction → Preliminaries → Main Results → Proof Sketches →
Discussion → Full Proofs appendix. Contribution = theorem/bound/impossibility,
not numbers; proofs are evidence; experiments optional but useful. State all
assumptions, give intuition first, keep sketch 0.5-1 page, use
`\begin{proof}...\end{proof}`, number assumptions.

### Survey / Tutorial

Structure: Introduction → Taxonomy/Organization → Detailed Coverage → Open
Problems → Conclusion. Contribution = organization/synthesis/open problems;
comprehensive within scope; taxonomy required; connect works. Venues: TMLR survey,
JMLR, Foundations and Trends in ML, ACM Computing Surveys.

### Benchmark

Structure: Introduction → Task Definition → Dataset Construction → Baseline
Evaluation → Analysis → Intended Use & Limitations. Benchmark fills evaluation gap;
dataset documentation/Datasheets mandatory; baselines must not saturate; demonstrate construct
validity. Venues: NeurIPS Datasets & Benchmarks, ACL resources, LREC-COLING.

### Position

Structure: Introduction → Background → Thesis/Argument → Supporting Evidence →
Counterarguments → Implications. Contribution = argument; engage counterarguments;
evidence may be empirical/theoretical/logical. Venues: ICML position track,
workshops, TMLR.

## Hermes Agent Integration

### Related Skills

| Skill | When to Use | How to Load |
|-------|-------------|-------------|
| **arxiv** | Phase 1: arXiv search, BibTeX, Semantic Scholar related work | `skill_view("arxiv")` |
| **subagent-driven-development** | Phase 5: parallel section writing with two-stage review | `skill_view("subagent-driven-development")` |
| **plan** | Phase 0: structured plan in `.hermes/plans/` | `skill_view("plan")` |
| **qmd** | Phase 1: local hybrid BM25+vector search | Install: `skill_manage("install", "qmd")` |
| **diagramming** | Phase 4-5: Excalidraw figures/architecture | `skill_view("diagramming")` |
| **data-science** | Phase 4: live-kernel analysis/visualization | `skill_view("data-science")` |

This skill supersedes `ml-paper-writing`; it includes that content plus the
experiment/analysis pipeline and autoreason methodology.

### Hermes Tools Reference

| Tool | Usage in This Pipeline |
|------|------------------------|
| **`terminal`** | LaTeX compilation (`latexmk -pdf`), git, experiments (`nohup python run.py &`), process checks |
| **`process`** | Background experiment management: `process("start", ...)`, `process("poll", pid)`, `process("log", pid)`, `process("kill", pid)` |
| **`execute_code`** | Citation verification, statistical analysis, aggregation; tool access via RPC |
| **`read_file`** / **`write_file`** / **`patch`** | Paper, experiment scripts, result files; `patch` for targeted large `.tex` edits |
| **`web_search`** | Literature discovery: `web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | Paper content/citation verification: `web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | Parallel section drafting and concurrent citation verification |
| **`todo`** | Persistent state across sessions; update after phase transitions |
| **`memory`** | Persist contribution, venue, feedback, decisions |
| **`cronjob`** | Experiment monitoring, deadline countdowns, arXiv checks |
| **`clarify`** | Targeted questions when blocked on venue/framing |
| **cron `deliver:` / `hermes send`** | Notify user when unattended experiments/drafts complete; no `send_message` tool — use a messaging `deliver:` target or `hermes send` |

### Tool Usage Patterns

**Experiment monitoring:**

```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<descriptive message>' && git push")
→ (final response auto-delivers "Experiment complete: <summary>"; for unattended runs, schedule via cron with a deliver: target)
```

**Parallel section drafting:**

```
delegate_task("Draft the Methods section based on these experiment scripts and configs. 
  Include: pseudocode, all hyperparameters, architectural details sufficient for 
  reproduction. Write in LaTeX using the neurips2025 template conventions.")

delegate_task("Draft the Related Work section. Use web_search and web_extract to 
  find papers. Verify every citation via Semantic Scholar. Group by methodology.")

delegate_task("Draft the Experiments section. Read all result files in results/. 
  State which claim each experiment supports. Include error bars and significance.")
```

Each delegate is fresh and needs all context; collect and integrate outputs.

**Citation verification:**

```python
# In execute_code:
from semanticscholar import SemanticScholar
import requests

sch = SemanticScholar()
results = sch.search_paper("attention mechanism transformers", limit=5)
for paper in results:
    doi = paper.externalIds.get('DOI', 'N/A')
    if doi != 'N/A':
        bibtex = requests.get(f"https://doi.org/{doi}", 
                              headers={"Accept": "application/x-bibtex"}).text
        print(bibtex)
```

### State with `memory` and `todo`

`memory` is bounded (~2200 chars) and stores decisions:

```
memory("add", "Paper: autoreason. Venue: NeurIPS 2025 (9 pages). 
  Contribution: structured refinement works when generation-evaluation gap is wide.
  Key results: Haiku 42/42, Sonnet 3/5, S4.6 constrained 2/3.
  Status: Phase 5 — drafting Methods section.")
```

`todo` tracks work:

```
todo("add", "Design constrained task experiments for Sonnet 4.6")
todo("add", "Run Haiku baseline comparison")
todo("add", "Draft Methods section")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

Session startup:

```
1. todo("list")                           # Check current task list
2. memory("read")                         # Recall key decisions
3. terminal("git log --oneline -10")      # Check recent commits
4. terminal("ps aux | grep python")       # Check running experiments
5. terminal("ls results/ | tail -20")     # Check for new results
6. Report status to user, ask for direction
```

### Cron Monitoring

```text
cronjob("create", {
  "schedule": "*/30 * * * *",  # Every 30 minutes
  "prompt": "Check experiment status:
    1. ps aux | grep run_experiment
    2. tail -30 logs/experiment_haiku.log
    3. ls results/haiku_baselines/
    4. If complete: read results, compute Borda scores, 
       git add -A && git commit -m 'Add Haiku results' && git push
    5. Report: table of results, key finding, next step
    6. If nothing changed: respond with [SILENT]"
})
```

`[SILENT]` exactly when unchanged; report only genuine changes. Deadline example:

```
cronjob("create", {
  "schedule": "0 9 * * *",  # Daily at 9am
  "prompt": "NeurIPS 2025 deadline: May 22. Today is {date}. 
    Days remaining: {compute}. 
    Check todo list — are we on track? 
    If <7 days: warn user about remaining tasks."
})
```

### Communication and decisions

Notify on completed batches/results tables, unexpected findings/failures needing
decision, draft readiness, and approaching deadlines. Use `[SILENT]` for running
experiments without changes and routine checks.

```
## Experiment: <name>
Status: Complete / Running / Failed

| Task | Method A | Method B | Method C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

Key finding: <one sentence>
Next step: <what happens next>
```

Use `clarify` only when genuinely blocked:

| Decision | When to Ask |
|----------|-------------|
| Target venue | Before starting paper (affects page limits, framing) |
| Contribution framing | When multiple valid framings exist |
| Experiment priority | When TODO list has more experiments than time allows |
| Submission readiness | Before final submission |

Choose proactively for word choice, section order, highlighted results, and
citation gaps; flag choices in draft.

## Reviewer Evaluation Criteria

| Criterion | What They Check |
|-----------|----------------|
| **Quality** | Technical soundness, well-supported claims, fair baselines |
| **Clarity** | Clear writing, reproducible by experts, consistent notation |
| **Significance** | Community impact, advances understanding |
| **Originality** | New insights (doesn't require new method) |

NeurIPS 6-point scale:

- 6 Strong Accept — groundbreaking, flawless
- 5 Accept — technically solid, high impact
- 4 Borderline Accept — solid, limited evaluation
- 3 Borderline Reject — weaknesses outweigh
- 2 Reject — technical flaws
- 1 Strong Reject — known results or ethics issues

See [references/reviewer-guidelines.md](references/reviewer-guidelines.md).

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Abstract too generic | Delete first sentence if it could prepend any ML paper. Start with your specific contribution. |
| Introduction exceeds 1.5 pages | Split background into Related Work. Front-load contribution bullets. |
| Experiments lack explicit claims | Add: "This experiment tests whether [specific claim]..." before each one. |
| Reviewers find paper hard to follow | Add signposting, use consistent terminology, make figure captions self-contained. |
| Missing statistical significance | Add error bars, number of runs, statistical tests, confidence intervals. |
| Scope creep in experiments | Every experiment must map to a specific claim. Cut experiments that don't. |
| Paper rejected, need to resubmit | See Conference Resubmission in Phase 7. Address reviewer concerns without referencing reviews. |
| Missing broader impact statement | See Step 5.10. Most venues require it. "No negative impacts" is almost never credible. |
| Human eval criticized as weak | See Step 2.5 and [references/human-evaluation.md](references/human-evaluation.md). Report agreement metrics, annotator details, compensation. |
| Reviewers question reproducibility | Release code (Step 7.9), document all hyperparameters, include seeds and compute details. |
| Theory paper lacks intuition | Add proof sketches with plain-language explanations before formal proofs. See [references/paper-types.md](references/paper-types.md). |
| Results are negative/null | See Phase 4.3 on handling negative results. Consider workshops, TMLR, or reframing as analysis. |

## Reference Documents

| Document | Contents |
|----------|----------|
| [references/writing-guide.md](references/writing-guide.md) | Gopen & Swan 7 principles, Perez micro-tips, Lipton word choice, Steinhardt precision, figure design |
| [references/citation-workflow.md](references/citation-workflow.md) | Citation APIs, Python code, CitationManager class, BibTeX management |
| [references/checklists.md](references/checklists.md) | NeurIPS 16-item, ICML, ICLR, ACL requirements, universal pre-submission checklist |
| [references/reviewer-guidelines.md](references/reviewer-guidelines.md) | Evaluation criteria, scoring, common concerns, rebuttal template |
| [references/sources.md](references/sources.md) | Complete bibliography of all writing guides, conference guidelines, APIs |
| [references/experiment-patterns.md](references/experiment-patterns.md) | Experiment design patterns, evaluation protocols, monitoring, error recovery |
| [references/autoreason-methodology.md](references/autoreason-methodology.md) | Autoreason loop, strategy selection, model guide, prompts, scope constraints, Borda scoring |
| [references/human-evaluation.md](references/human-evaluation.md) | Human evaluation design, annotation guidelines, agreement metrics, crowdsourcing QC, IRB guidance |
| [references/paper-types.md](references/paper-types.md) | Theory papers (proof writing, theorem structure), survey papers, benchmark papers, position papers |

### LaTeX Templates

Templates in `templates/` cover **NeurIPS 2025**, **ICML 2026**, **ICLR 2026**,
**ACL**, **AAAI 2026**, **COLM 2025**. See [templates/README.md](templates/README.md).

### Key External Sources

**Writing Philosophy:**

- [Neel Nanda: How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/)

**APIs:** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**Venues:** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)

## Pitfalls

- citation memory/hallucination; fetch and verify in ≥2 sources, mark gaps
- experiment without claim mapping; scope creep; weak/mismatched baselines
- missing incremental saves/checkpoints; rerun only after preserving completed work
- API 402/429, concurrency, wrong model IDs, crashed/blocked jobs
- reporting means without variance, CIs, tests, effect size, seeds, or run counts
- hiding negative/null results or forcing a story without evidence
- human evaluation without power/sample/agreement/compensation/ethics detail
- autoreason with broken judges, unconstrained drift, or fabricated paper data
- review positivity bias; use independent ensemble, negative bias, and meta-review
- text-only PDF review misses layout/readability/grayscale defects
- untraceable claims; run fresh claim-verification pass
- anonymity leaks via names, self-citations, URLs, metadata, logs, figures, data,
  supplements, or preprints
- copying LaTeX preambles across venues; violating page/style/checklist limits
- arXiv timing/version changes that reveal review response
- unreproducible release: absolute paths, floating dependencies, secrets, missing LICENSE
- commit results/logs and meaningful drafts; never claim completion from unverified output

## Verification

- contribution is one sentence; every experiment maps to a claim
- citations fetched, verified, BibTeX matched, and placeholders disclosed
- runs preserve checkpoints/artifacts, config/seeds/costs, journal, snapshots
- analysis reports uncertainty, significance/effect sizes, failures, and next decisions
- `experiment_log.md` bridges results to sections; files committed
- draft passes ensemble/meta/visual/claim review; critical/high issues addressed
- venue checklist, anonymity, page/figure/table/refs checks complete
- pre-compilation warnings fixed; `latexmk -pdf` or manual build yields non-empty PDF
- code release runs from clean clone, dependencies pinned, no secrets/absolute paths
- post-acceptance poster/talk/blog/project-page requirements match venue
