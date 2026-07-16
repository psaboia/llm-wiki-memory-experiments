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
- **D — periodic mechanical lint** (`results/battery-D-periodic-lint.jsonl`):
  natural editing, plus a mechanical `wiki-reciprocity.py` lint-and-fix sweep
  after rounds 4 and 8 (models "someone runs `/wiki-lint` periodically"). Chains
  seeded from the feature branch so the real checker is present. 3 replicates.
- **E — per-write mechanical nudge** (`results/battery-E-nudge.jsonl`): each round
  ingests, then runs the checker on its own writes and fixes what it reports
  before committing (a faithful proxy for the PostToolUse hook — the mechanism
  surfaces violations, not the agent's memory). 3 replicates.

The five conditions form a spectrum of enforcement strength: `off` (check
suppressed) < `natural` (procedure only) < `periodic-lint` (mechanical, every 4
rounds) < `gate-on` (instruction, every round) < `nudge` (mechanical, every
write).

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

## Result 2 — reciprocity erodes over rounds; enforcement strength sets the ceiling

Typed-edge violations (what the gate checks today), mean of 3 replicates, by round:

| condition | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| `off` (suppressed, worst case) | 0.3 | 2.3 | 4.7 | 8.3 | 12.0 | 14.7 | 18.7 | **21.3** |
| `natural` (procedure only) | 0.3 | 0.7 | 1.0 | 2.0 | 3.0 | 3.3 | 3.7 | **3.7** |
| `periodic-lint` (mechanical, every 4 rounds) | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 1.3 | **1.3** |
| `gate-on` (instruction, every round) | 0.0 | 0.0 | 0.0 | 0.7 | 0.7 | 0.7 | 0.7 | **0.7** |
| `nudge` (mechanical, every write) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** |

The `periodic-lint` mechanical sweep produces a **sawtooth**: state climbs between
sweeps and drops at each sweep (any-means reset from 4.3 at round 4 to 0.3 right
after `lint4`, then climbs again and drops at `lint8`). It bounds erosion to a low
ceiling rather than eliminating it.

![The periodic-lint sawtooth: violations climb between sweeps and drop at each
lint sweep (marked at 4.5 and 8.5), staying well below the un-swept natural
condition which climbs monotonically.](figures/sawtooth-periodic-lint.png)

*Figure: the sawtooth, plotted in event sequence so the sweeps are visible (the
five-condition chart above plots round-end state only and therefore cannot show
them). `natural` overlaid for contrast. Regenerate with `python3 plot.py`.*

Both conditions grow the wiki to about the same size (~11–12 content pages at r8),
so the difference is not "the stricter conditions wrote less" — it is that they
kept links bidirectional while the weaker ones let them go one-way.

![Reciprocity vs enforcement strength across five conditions over 8 editing
rounds: off runs away to 21.3 while natural (3.7), periodic-lint (1.3), gate-on
(0.7), and nudge (0.0) stay low; the right panel zooms in to separate the four
low conditions.](figures/erosion-curves.png)

*Figure: typed-edge violations, mean of 3 replicates. Left = full scale; right =
zoom to 0–4.5. Regenerate with `python3 plot.py`.*

## Interpretation

1. **Erosion over time is real, not an artifact of the worst case.** Under normal
   documented behavior (`natural`), typed-edge violations still climb
   monotonically, 0.3 → 3.7 over 8 rounds. The `gate-off` case erodes ~6× faster
   (→ 21.3), but it is not needed to demonstrate the effect.
2. **Enforcement is load-bearing, and strength sets the ceiling.** The final
   violation count is monotone in enforcement strength: off 21.3 > natural 3.7 >
   periodic-lint 1.3 > gate-on 0.7 > nudge 0.0. More frequent, more mechanical
   enforcement → lower steady-state erosion.
3. **Periodic mechanical lint bounds erosion to a sawtooth; it does not eliminate
   it.** Detection at lint-time (the shipped `/wiki-lint` wiring) lets state climb
   between sweeps and resets it at each — a low bounded sawtooth (~1.3 ceiling),
   far below un-swept `natural`, but not the flat line of continuous enforcement.
4. **A mechanical per-write nudge matches or beats the instruction gate.** `nudge`
   (mechanical check every write) held at 0.0, versus `gate-on` (instruction every
   write) at 0.7 — the mechanism surfaces violations the agent's diligence misses.
   This is the behavioral evidence for a PostToolUse-hook implementation.
   *Caveat — partly by construction:* `nudge` agents fixed until the checker
   reported zero and we measure with the same checker, so exact 0.0 is not a free
   result; what it genuinely shows is that the fix loop **converges** (fixes do not
   spawn violations faster than they close) and **stays at zero across 8 rounds**.
   The non-circular contrast is `nudge` (mechanical) vs `gate-on` (instruction),
   since the latter never runs the script.
5. **The lever is mechanical enforcement, not the choice of criterion.** typed vs
   any-means makes little difference *when a check runs* (both low under `gate-on`/
   `nudge`); both erode when none does. The decision-relevant move is turning a
   followed-with-normal-diligence *procedure* into a *check that runs*.
6. **Consistency with a real wiki (cautious).** The template's own wiki, measured
   separately at ~33 pages, had 29 typed / 59 any-means violations — above
   `natural` at r8, consistent with more than 8 rounds of edits and heterogeneous
   real content. This is a consistency check on the mechanism, not a prediction of
   absolute counts.

## Result 3 — the edges are semantically sound, but KG-visible typed edges collapse

Does enforcement produce *meaningful* edges, or padded/hallucinated ones? Scored
mechanically against the corpus ground truth (21 relations; `ground-truth.json`,
`semantic-metrics.py`, `results/phase1-semantic-scores.jsonl`). Final state, mean
of 3 replicates:

| condition | recall | **typed_coverage** | spurious_rate | prose_backref |
|---|---|---|---|---|
| `off` | 0.87 | **0.83** | 0.13 | 0.94 |
| `natural` | 0.95 | **0.56** | 0.22 | 1.00 |
| `periodic-lint` | 0.94 | **0.68** | 0.21 | 0.88 |
| `gate-on` | 0.97 | **0.38** | 0.18 | 0.97 |
| `nudge` | 0.95 | **0.21** | 0.14 | 0.92 |

**No padding, no hallucination.** `spurious_rate` does not rise with enforcement
(nudge 0.14 is *below* natural's 0.22), and `prose_backref_ratio` is 0.88–1.00
everywhere — back-references are substantive prose, not bare "See also" filler.
**Recall improves** under enforcement (0.87 → 0.94–0.97): the mechanism covers
*more* of what the corpus asserts.

**But `typed_coverage` collapses under per-write enforcement**: off 0.83 → natural
0.56 → periodic-lint 0.68 → gate-on 0.38 → nudge 0.21. Replicates do not overlap
between the extremes (nudge [0.24, 0.19, 0.19] vs off [0.91, 0.86, 0.71]). Under a
per-write check, only ~1 in 5 true relations stays visible to the knowledge-graph
pipeline: the relations are still present and correct, but expressed in body prose
rather than as frontmatter typed edges — excellent for human readers, invisible to
the KG.

**`periodic-lint` (what PR #84 ships) does not show the effect**: 0.68
([0.62, 0.71, 0.71]) sits *above* `natural`'s 0.56. Mechanically consistent — its
ingest agent never runs a check; only the sweep repairs. This is the evidence that
#84 is safe, and that the cost lands on a per-write hook instead.

*Evidence strength: Phase 1 is exploratory — n=3, ground truth formalised after
the runs (though derived solely from the pre-existing corpus), and a seed-source
confound. **The typed_coverage claim above did not replicate**: see Result 4, where
the pre-registered n=5 test falsifies H1. Read this table as the exploratory signal
that motivated Phase 2, not as a finding.*

## Result 4 — Phase 2 (pre-registered, n=5): H1 falsified, H2/H3/H4 sustained

Phase 1's typed-edge suppression signal was tested as a stated hypothesis on fresh
chains (n=5, all seeded from one commit, scorer and ground truth frozen at the
pre-registration commit `78679bf`; see PROTOCOL § Phase 2).
Data: `results/phase2-semantic-scores.jsonl`.

| condition | n | typed_coverage median | full replicate range | recall median | spurious median |
|---|---|---|---|---|---|
| `natural` | 5 | 0.33 | [0.19 – 0.86] | 1.00 | 0.34 |
| `periodic-lint` | 5 | 0.29 | [0.19 – 0.62] | 1.00 | 0.34 |
| `nudge` | 5 | 0.19 | [0.10 – 0.48] | 1.00 | 0.28 |

- **H1 — FALSIFIED.** `nudge` [0.10–0.48] and `natural` [0.19–0.86] overlap
  heavily; the pre-registered falsification criterion (non-overlapping ranges) is
  not met. **Phase 1's headline (typed_coverage 0.56 → 0.21) did not replicate.**
  Its cause is visible in the Phase-2 spread: `natural` runs
  [0.19, 0.29, 0.33, 0.33, **0.86**] — one outlier drags the *mean* to 0.44 while
  the *median* is 0.33. Phase 1's n=3 mean of 0.56, plus its seed-source confound
  (natural from `main`, nudge from the branch), manufactured a gap that a
  confirmatory design does not reproduce.
  *Precisely:* falsified ≠ "no effect exists". The medians still order
  0.33 > 0.29 > 0.19; if an effect exists it is smaller than the noise at n=5.
  There is simply **no basis to claim per-write enforcement degrades the KG**.
- **H2 — SUSTAINED.** `periodic-lint` [0.19–0.62] overlaps `natural` [0.19–0.86];
  medians 0.29 vs 0.33. A periodic sweep does not reduce typed-edge coverage.
- **H3 — SUSTAINED.** Spurious rate does not rise with enforcement (`nudge` is the
  *lowest*: 0.28 vs natural 0.34). No induced hallucination or padding.
- **H4 — SUSTAINED.** Recall is **1.00** in every condition: every wiki represents
  all 21 corpus relations, enforced or not.

Two honest notes Phase 2 surfaced: `spurious_rate` is uniformly higher than in
Phase 1 (0.28–0.34 vs 0.13–0.22) — equal across conditions, so it is a property of
how these wikis get built, not of enforcement; and `recall` is higher (1.00 vs
0.94–0.97).

**Bearing:** PR #84 (the `/wiki-lint` mechanical check) is supported — H2, H3, H4
all hold. The semantic objection raised against a per-write hook after Phase 1 is
**withdrawn**: it did not survive its own confirmatory test.

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

Supports three decisions on the live template
(`crcresearch/llm-wiki-memory-template`):

- **Mechanical check in `/wiki-lint`** (shipped: PR #84, `scripts/wiki-reciprocity.py`).
  The `periodic-lint` condition confirms it bounds erosion to a low sawtooth — a
  real improvement over the procedural checklist (`natural`), though not the flat
  line of continuous enforcement.
- **A per-write PostToolUse hook** running the same check. The `nudge` condition
  (0.0, matching/beating the instruction gate's 0.7) is the behavioral evidence
  that continuous mechanical enforcement holds reciprocity at zero, and Phase 2
  found **no** semantic cost to it (H1 falsified, H3/H4 sustained). A hook PR would
  still need a harness test for the *wiring* (does the hook fire); this battery
  covers the *efficacy*, not the plumbing.
- **Clear the existing debt** (the 29 typed / 59 any-means, or 64 by the shipped
  checker's any-means union, measured on the template wiki) with a one-time lint
  sweep, triaging genuine hubs to `hub: true`; it is accumulated history, not a
  per-commit tax.
