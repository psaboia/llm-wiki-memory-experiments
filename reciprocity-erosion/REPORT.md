# Reciprocity-erosion — findings

What the data say. This is the analysis layer, distinct from `PROTOCOL.md` (how
to run it) and `results/*.jsonl` (raw data). All numbers below are computed by
`measure.py` over the wikis' git history; none are agent self-reports.

## Question

If page A links to page B, the wiki convention says B should reference A back, so
a reader (or the knowledge graph) arriving at B can find A. As an LLM-maintained
wiki is edited across many independent sessions, do these back-references erode,
and does running the verification gate prevent it?

## Batteries

- **A — single-ingest variance** (`results/battery-A-single-ingest.jsonl`):
  5 independent fresh ingests of the same 4-document corpus, one agent each.
- **B — erosion, gate-off vs gate-on** (`results/battery-B-erosion.jsonl`):
  8 sequential edit rounds per chain, a fresh agent per round (no memory of prior
  rounds), 3 replicates per condition.
- **C — erosion, natural condition** (`results/battery-C-natural.jsonl`): same
  8-round design, agent follows the documented ingest procedure with the gate
  neither emphasized nor suppressed. 3 replicates.

Conditions differ only in the per-round instruction: `gate-on` (run the gate,
make every new link bidirectional), `gate-off` (do not run the gate, do not go
back for back-references), `natural` (do what the documented procedure says, no
more, no less).

## Result 1 — a diligent fresh ingest achieves near-perfect reciprocity

Battery A, violations across the 5 independent ingests:

| metric | run1 | run2 | run3 | run4 | run5 |
|---|---|---|---|---|---|
| typed-edge (current gate) | 0 | 0 | 0 | 0 | 0 |
| any-means (proposed) | 1 | 0 | 0 | 0 | 1 |

Violations are ~0 and stable (typed sd = 0; any-means range 0–1). So reciprocity
violations are **not per-ingest noise** — a single careful ingest gets it right.
Structural choices did vary (pages 6–7; one run invented `dependsOn`/`feedsInto`
edges outside the SCHEMA vocabulary), but reciprocity itself was consistently met.

## Result 2 — reciprocity erodes over rounds, and the gate holds it

Typed-edge violations (what the gate checks today), mean of 3 replicates, by round:

| condition | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| `gate-off` (suppressed, worst case) | 0.3 | 2.3 | 4.7 | 8.3 | 12.0 | 14.7 | 18.7 | **21.3** |
| `natural` (documented procedure) | 0.3 | 0.7 | 1.0 | 2.0 | 3.0 | 3.3 | 3.7 | **3.7** |
| `gate-on` (enforced) | 0.0 | 0.0 | 0.0 | 0.7 | 0.7 | 0.7 | 0.7 | **0.7** |

Any-means violations (the proposed stricter criterion) show the same ordering:

| condition | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| `gate-off` | 3.3 | 6.0 | 8.0 | 11.7 | 15.7 | 18.7 | 23.0 | **25.7** |
| `natural` | 4.3 | 4.3 | 5.0 | 6.7 | 8.3 | 8.7 | 9.7 | **9.7** |
| `gate-on` | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.7 | **1.7** |

Both conditions grow the wiki to about the same size (12.3 / 12.0 / 11.0 content
pages at r8), so the difference is not "gate-on wrote less" — it is that gate-on
kept links bidirectional while the others let them go one-way.

## Interpretation

1. **Erosion over time is real, not an artifact of the worst case.** Under normal
   documented behavior (`natural`), typed-edge violations still climb
   monotonically, 0.3 → 3.7 over 8 rounds. The `gate-off` case erodes ~6× faster
   (→ 21.3), but it is not needed to demonstrate the effect.
2. **The gate is load-bearing.** Enforcing it holds violations near zero (→ 0.7)
   across all 8 rounds and every replicate.
3. **The lever is mechanical enforcement, not the choice of criterion.** typed vs
   any-means makes little difference *when the gate runs* (both ~0–2 under
   `gate-on`); both erode when it does not. The decision-relevant gap is
   `natural` → `gate-on` — i.e. turning a followed-with-normal-diligence
   *procedure* into a *check that runs every time*.
4. **Consistency with a real wiki (cautious).** The template's own wiki, measured
   separately at ~33 pages, had 29 typed / 59 any-means violations — above
   `natural` at r8, consistent with more than 8 rounds of edits and heterogeneous
   real content. This is a consistency check on the mechanism, not a prediction of
   absolute counts.

## Threats to validity

- **Synthetic corpus** (fictional, fixed) — chosen for a controlled, identical
  cross-reference web across chains; external validity to real literature is not
  established here.
- **`gate-off` is near-worst-case** (reciprocity actively suppressed); treat it as
  an upper bound, and `natural` as the realistic estimate.
- **Single model family, N = 3.** The erosion *rate* is noisy (gate-off any-means
  r8 spanned 20–34 across replicates); the *direction* is unambiguous (monotonic
  every round, every replicate).
- **Agent-generated data, LLM-authored measure.** `measure.py` is deterministic
  and auditable, but it is a *lenient* approximation of the gate criterion (it
  accepts a back-reference by any means, incl. frontmatter) and both data
  generation and measurement sit inside the system under study — disclose this.
- **Non-determinism is intrinsic.** "Reproducible" means the trend and
  distribution replicate, not identical counts.

## Bearing on the template

Supports two decisions on the live template
(`crcresearch/llm-wiki-memory-template`):

- Adopt the any-means reciprocity criterion (its maintenance cost under
  enforcement is ~0–2 violations, i.e. near-free) **and back it with a mechanical
  check** in `/wiki-lint` rather than leaving it a procedural checklist — because
  the procedure alone erodes (`natural`), the check does not (`gate-on`).
- Clear the existing debt (the 29/59 measured on the template wiki) with a
  one-time lint sweep; it is accumulated history, not a per-commit tax.
