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

- **Battery B — erosion over 8 rounds** (`battery-B-erosion.jsonl`):
  6 chains (gate-on ×3, gate-off ×3), 8 sequential rounds each, fresh agent per
  round. Without the gate, typed-edge violations climbed roughly linearly
  (mean 0.3 → 21.3 over 8 rounds); with the gate they stayed near zero
  (0 → 0.7). The gate holds link integrity; its absence lets it erode over time.

A third condition (`natural` — normal documented procedure, gate neither pushed
nor suppressed) is being added to estimate realistic erosion between the two
extremes.

See `reciprocity-erosion/PROTOCOL.md` for the full design, provenance, and honest
limitations (synthetic corpus, single model family, N=3, agent-generated data).

## Status

Private working repo for in-progress research. Intended to be archived to Zenodo
for a DOI once the accompanying experiment section is finalized.
