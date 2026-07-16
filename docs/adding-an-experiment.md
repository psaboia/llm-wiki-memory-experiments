# Adding an experiment

How to add a new experiment folder to this repo and stay aligned with the
conventions the existing ones follow. Read this before creating a directory.

`reciprocity-erosion/` is the reference instance — copy its shape, and follow the
disciplines below, which are what make its results trustworthy rather than merely
present.

## Layout

One directory per experiment, self-contained, named after the question (not the
method):

```
<experiment-name>/
  PROTOCOL.md          how to run it: design, conditions, provenance, limitations
  REPORT.md            what the data say: results, interpretation, threats
  results/             raw data, one file per battery, never edited by hand
    battery-A-<slug>.jsonl
    battery-B-<slug>.jsonl
  <inputs>/            fixed inputs (corpus/, rounds/, fixtures/ …)
  scripts/             what ran: seeding, orchestration, measurement drivers
  measure.py           the measurement instrument (deterministic, auditable)
  plot.py              regenerates every figure from results/
  figures/             generated; never hand-edited
```

**Three layers, kept separate.** `PROTOCOL.md` = how to run. `results/` = raw data.
`REPORT.md` = what it means. Do not mix them: a protocol that argues conclusions,
or a report that hides the design, both rot.

**Naming.** Batteries get a letter in run order plus a slug
(`battery-C-natural.jsonl`). One JSON object per measured point, carrying enough
keys to re-aggregate without the script that wrote it (`cond`, `chain`, `round`/
`step`, and the metrics).

## Disciplines (non-negotiable)

These are not style preferences; each exists because violating it produced a wrong
or unfalsifiable result.

1. **Measure the artifacts, never the agents' self-reports.** Agents run the
   condition; the *parent* measures the resulting files (ideally from git history,
   so every intermediate state is recoverable). Tell agents not to report metrics —
   an agent's claim about its own work is not evidence.
2. **Seed hermetically.** Build the system-under-test from `git archive HEAD`, not
   `cp -R` of a working tree: an archive carries only tracked files, so local,
   untracked, or dogfood artifacts cannot leak in and contaminate a run. (A working-
   tree copy in the template's own harness swept a local dev wiki into sandboxes and
   produced false failures — that is the failure mode this rule prevents.)
3. **Isolate completely.** Everything runs in a scratch directory. The repo under
   study is read-only; never write to it, never let a chain reach outside its own
   directory. Verify isolation after the run, do not assume it.
4. **Fresh context per step when modelling time.** If the experiment is about what
   happens across sessions, each step must be a fresh agent that rediscovers state
   from disk. An agent that remembers earlier steps under-estimates drift — the
   memory *is* the variable.
5. **Replicate.** ≥3 per condition. Report the spread, not just the mean; a trend
   is only a trend if it survives the noise.
6. **Include a control.** A condition where the effect should *not* appear. If the
   control moves too, the instrument is measuring something else.
7. **Watch the check fail.** Before trusting a measurement script, confirm it goes
   red on a known-bad input and green when fixed. A number that has never been wrong
   teaches nothing. (See `.claude/rules/observe-the-failure.md` in the template.)
8. **State the limitations in both PROTOCOL and REPORT.** Synthetic inputs, small N,
   single model family, near-worst-case conditions, and any circularity **must** be
   named. In particular: this repo's data are agent-generated and measured by
   LLM-authored scripts — that coupling is disclosed every time.
9. **Beware conditions that are true by construction.** If agents fix until a
   checker reports zero and you measure with that checker, "zero" is partly
   tautological. Say so, and name the non-circular contrast that carries the claim.
10. **Figures regenerate from raw data.** `plot.py` reads `results/` and writes
    `figures/`; never hand-edit a figure. Use a CVD-safe categorical palette with
    secondary encoding (line style + marker) so figures survive greyscale and print.
11. **Scripts are kept in fidelity, not convenience.** The orchestration scripts are
    the literal record of what ran — hardcoded paths and all. Do not "clean them up"
    into parameterised versions; PROTOCOL explains what to edit to re-run.
12. **Reproducible means the trend replicates, not the numbers.** Agents sample.
    Never promise identical counts.

## Steps

1. Write `PROTOCOL.md` first: the question, the design, the conditions (and what
   differs between them — ideally one thing), the metric, provenance (which commit
   of the system-under-test), and the limitations you already know.
2. Fix the inputs. Identical across conditions; commit them.
3. Write `measure.py`. Prove it can fail (discipline 7) before trusting a single
   number from it.
4. Seed and run. Save the orchestration scripts (discipline 11).
5. Measure from the artifacts, write `results/battery-*.jsonl`.
6. Write `REPORT.md`: results, interpretation, threats to validity, and what it
   bears on for the template or the paper.
7. Add `plot.py` output and embed the figure in `REPORT.md`.
8. Add a section to the root `README.md` summarising the experiment and its headline.

## What does not belong here

- Changes to the template itself — those are PRs against
  `crcresearch/llm-wiki-memory-template`. This repo studies it; it does not ship it.
- Conclusions without the data that produced them, or data without the protocol
  that explains it.
