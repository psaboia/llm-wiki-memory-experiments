# llm-wiki-memory-experiments

Reproducibility artifacts for experiments accompanying the
[llm-wiki-memory-template](https://github.com/crcresearch/llm-wiki-memory-template)
and the paper *Beyond Memory: A Templated Substrate for Heterogeneous
Collaborative Knowledge Work with LLM Agents* (Saboia Moreira, Vardeman, Sweet,
University of Notre Dame; draft: https://zenodo.org/records/21229213).

Each subdirectory is one self-contained experiment: fixed inputs, the scripts
that run it, the raw results, and a `PROTOCOL.md` describing the design and its
limitations. Experiments here are studies *about* the template; they are kept in
a separate repo (not a template branch) so the template stays clean and the
studies stay independently versioned and citable.

## Experiments

### `reciprocity-erosion/`

Does the template's verification gate preserve cross-reference (link) integrity
in an LLM-maintained wiki as it is edited across many independent sessions?

Two batteries ran so far (see `reciprocity-erosion/results/`):

- **Battery A — single-ingest variance** (`battery-A-single-ingest.jsonl`):
  5 independent fresh ingests of the same 4-doc corpus. Reciprocity violations
  were ~0 and stable (typed-gate 0/0/0/0/0; any-means 1/0/0/0/1) — a diligent
  fresh ingest achieves near-perfect reciprocity, so violations are not per-ingest
  noise.

- **Battery B — erosion over 8 rounds** (`battery-B-erosion.jsonl`,
  `battery-C-natural.jsonl`): chains of 8 sequential rounds, fresh agent per
  round, 3 replicates per condition. Typed-edge reciprocity violations, mean of
  3 replicates, by round:

  | condition | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
  |---|---|---|---|---|---|---|---|---|
  | `gate-off` (gate suppressed, worst case) | 0.3 | 2.3 | 4.7 | 8.3 | 12.0 | 14.7 | 18.7 | **21.3** |
  | `natural` (documented procedure, realistic) | 0.3 | 0.7 | 1.0 | 2.0 | 3.0 | 3.3 | 3.7 | **3.7** |
  | `gate-on` (gate enforced) | 0.0 | 0.0 | 0.0 | 0.7 | 0.7 | 0.7 | 0.7 | **0.7** |

  Reciprocity erodes monotonically over rounds even under normal documented
  behavior (`natural`: 0.3 → 3.7); the suppressed case erodes ~6× faster
  (→ 21.3); enforcing the gate holds it near zero (→ 0.7). The any-means
  criterion shows the same ordering (off 25.7 / natural 9.7 / on 1.7 at r8).
  Interpretation: the discipline mechanism is load-bearing, and the value lies
  in *mechanical enforcement* over a followed-with-normal-diligence procedure —
  the gap between `natural` and `gate-on`.

See `reciprocity-erosion/PROTOCOL.md` for the full design, provenance, and honest
limitations (synthetic corpus, single model family, N=3, agent-generated data).

## Status

Private working repo for in-progress research. Intended to be archived to Zenodo
for a DOI once the accompanying experiment section is finalized.
