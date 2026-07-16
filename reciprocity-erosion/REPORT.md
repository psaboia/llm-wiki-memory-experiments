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
  that continuous mechanical enforcement holds reciprocity at zero. A hook PR would
  still need a harness test for the *wiring* (does the hook fire); this battery
  covers the *efficacy*, not the plumbing.
- **Clear the existing debt** (the 29 typed / 59 any-means, or 64 by the shipped
  checker's any-means union, measured on the template wiki) with a one-time lint
  sweep, triaging genuine hubs to `hub: true`; it is accumulated history, not a
  per-commit tax.
