# Synthesis gap — does the ingestion workflow, not the LLM, cause the missing tension edges?

Pre-registration. Companion experiment to *Beyond Memory*. **Written and committed
before any data is collected; git history is the audit trail.**

## Background — why this is re-scoped

A real coverage-discovery wiki (built with the llm-wiki pattern on an AI-for-science
corpus) was observed to accumulate summary pages but almost no *tension* edges
(`extends` / `supports` / `criticizes`) and no `synthesis` pages — the very things
the pattern exists to produce. Pipeline archaeology (reading how that wiki was
built, not an experiment) found the likely cause: the sources were pre-processed by
a separate extraction tool into page templates, and **no LLM attached to the wiki
ever read the papers to look for relationships**. The graph's edges reflect
structural field overlaps, not reading.

So the "why" is largely answered by inspection. This experiment tests the **fix**:
if an agent actually reads the source and is asked to relate it to existing pages,
do valid tension edges appear — and does depth of reading or repetition matter? It
also serves as a controlled, on-substrate baseline the collaboration can measure a
proposed intervention against.

**This experiment studies the mechanism, not any specific project's private wiki.
The corpus is a fixed set of open-access papers used identically across conditions;
no third-party wiki content is reproduced here.**

## Hypotheses (stated before data)

- **H1 — the fix works.** An ingestion condition that reads the full source and is
  asked to cross-reference it produces more valid tension edges than an
  extract-and-template condition with no relationship step.
  *Falsified if the C1 and C0 replicate ranges overlap.*
- **H2 — depth of reading matters.** Reading the full text produces more valid
  tension edges than reading only the abstract.
  *Falsified if C1 and C_abs ranges overlap.*
- **H3 — reliability comes from repetition.** Repeated compare-and-contrast passes
  produce more valid tension edges than a single reading pass.
  *Falsified if C2 does not exceed C1.*

## Conditions

The same fixed corpus is ingested under each condition into a fresh wiki. Conditions
differ only in the ingestion instruction:

- **C0 — extract-and-template** (reproduces the observed antipattern): the agent
  extracts fields from the source into the page template; it is **not** asked to
  find or type relationships. Expected floor: ~0 tension edges.
- **C_abs — abstract-only + cross-reference**: the agent reads only the abstract,
  then is asked to relate the new page to existing pages with typed edges where the
  content warrants.
- **C1 — full-text + cross-reference (single pass)**: same as C_abs but the agent
  reads the full paper.
- **C2 — full-text + repeated compare-and-contrast**: after the single pass, run
  additional passes over page groups (siblings under a hub, tag-overlap pairs,
  co-mention pairs), each proposing typed edges; reliability accrues across passes.

## Metric

Measured mechanically from the wiki's git history, never from agent self-reports.

- **Primary — valid tension-edge count.** Number of `extends`/`supports`/`criticizes`
  edges between real content pages. "Valid" = well-formed mechanically: both
  endpoints are real content pages (not ghost/scaffolding nodes — cf. template
  issue #85), and the predicate is in the declared SCHEMA vocabulary.
- **Secondary — synthesis pages produced** (`type: synthesis`).
- **Groundedness — LLM-judge, circularity declared.** Well-formedness is mechanical;
  whether an asserted relationship is actually *supported by the papers* is not, and
  no human reviewer is available. So groundedness is rated by an **LLM judge** given
  both papers' text and the asserted edge. This is circular — an LLM judging
  LLM-produced edges — and is declared as such: it measures plausibility-to-a-careful-
  reader, not ground truth. **Count is never claimed as improvement without it** — 40
  edges at 30% grounded is worse than 15 at 90%.

## Phase 0 — groundedness calibration (before the main battery)

To bound how much the LLM-judge can be trusted, a **curated subset** of the corpus
is selected first: papers whose relationships are clear enough to pin down. On that
subset a **reference relation-set** is built by a separate, higher-effort protocol —
read each paper in full and enumerate every defensible tension relationship among
the subset. Then:

- On the subset, groundedness is scored against the reference *mechanically* (an edge
  is grounded iff it is in the reference), giving partial ground truth.
- The judge is run on the same subset and its **agreement with the reference** is
  reported as its reliability envelope — "not perfect, but an idea of what to expect"
  off the subset.

Honest framing: the reference is itself LLM-built (no human bandwidth), so it is a
*stricter, independent* protocol on a small, spot-checkable set — not an oracle. The
subset is chosen from the shared corpus for tractability of pinning relationships,
and that selection is recorded. This is a calibration crutch, disclosed as one, not
a substitute for ground truth.

## Corpus handling (no PDFs in this repo)

The source PDFs are **never committed** — third-party papers (copyright /
redistribution) and binary bloat, and this repo is public. They live in a local
directory *outside* the repo (e.g. `~/llm-wiki-exp-data/synthesis-gap/pdfs/`); the
harness reads them via a `--corpus` path. The repo records only
`corpus/manifest.json` — per paper: filename, `sha256`, `source` URL, access status
— mirroring the source wiki's own frontmatter convention (`fulltext_sha256`,
`source`). A run is then reproducible *by reference* without redistributing the
papers.

## Design

- Fixed corpus: a set of open-access papers (target ~12, enough that inter-paper
  relationships can exist), identical across all conditions.
- Replicates: ≥3 per condition (agents are nondeterministic); target 5, final N set
  before running given cost (4 conditions × N × per-paper ingestion is a large run;
  see Cost).
- Isolation: a fresh wiki per condition per replicate, seeded hermetically
  (`git archive`, never `cp -R`); all work in a scratch copy or a fork — **never the
  source-of-truth wiki**; measured from git history.
- Fresh agent per ingestion step (no cross-step memory), per the over-time discipline.

## Analysis plan

Report medians and **full replicate ranges** per condition, for count and
groundedness. No significance test claimed at this N — range overlap or separation
is the evidence, reported honestly either way. The scorer is frozen at the commit
that precedes the run; prove it can fail (well-formed vs malformed edge) before use.

## Threats to validity / limitations

- **No mechanical ground truth for relationship correctness.** Real papers have no
  ready ground-truth relation set (unlike the synthetic reciprocity corpus).
  Groundedness therefore rests on an LLM-judge, calibrated on a small LLM-built
  reference subset (Phase 0). **This is circular** — LLMs producing, judging, and
  referencing the edges — and only the human-free tooling we have; the claim it
  supports is "plausible & well-formed edges," not "true edges." The calibration
  agreement rate is the honest bound on how far to trust it.
- **Agent-generated data, LLM-authored scorer.** The scorer is deterministic and
  auditable but sits inside the system under study; disclose it.
- **C0 is an antipattern reconstruction**, our best reproduction of the observed
  pipeline, not that pipeline itself.
- **Open-access papers may differ** in structure from the original corpus; the
  mechanism should transfer, absolute counts may not.
- Non-determinism is intrinsic: "reproducible" means the trend replicates, not the
  numbers.

## What it decides

- H1 holding says the missing tension edges are a **workflow** problem (no reading
  step), fixable by adding one — not an LLM-capability ceiling.
- H2 isolates whether *depth* of reading is the lever (Chris Sweet's "the LLM never
  saw the papers").
- H3 tests whether single-shot authoring is unreliable and repetition is required
  (the RWR/compare-and-contrast line) — informing whether a fix should be one step
  or a distribution of passes, and how the coverage-discovery feature (issue #79)
  should compose.

## Cost note

At 4 conditions × 5 replicates × ~12 papers, plus C2's extra passes, this is a
large agent run. The final corpus size and N are decided (and recorded here) before
launch; a reduced pilot (fewer papers, N=3) may run first to validate the harness
and the scorer before the full battery.
