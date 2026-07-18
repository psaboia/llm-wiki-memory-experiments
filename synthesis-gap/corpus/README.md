# Corpus — identity only, never the PDFs

This directory records **which** papers the experiment uses, not their bytes.

The source PDFs are third-party papers and this repo is public, so the PDFs are
**never committed** (copyright / redistribution, and binary bloat). They live in a
local directory outside the repo — by convention:

```
~/llm-wiki-exp-data/synthesis-gap/pdfs/
```

The harness reads them from there via a `--corpus` path.

`manifest.json` (generated from the local PDFs) is the committed record: one entry
per paper with `filename`, `sha256`, `source` URL, and `access` status — the same
identity the source wiki already keeps in page frontmatter (`fulltext_sha256`,
`source`). That makes a run reproducible **by reference**: anyone with the same
papers can verify they have the identical bytes via the sha256, without this repo
redistributing them.

To (re)generate the manifest after placing PDFs in the local dir, point the manifest
tool at that directory (added with the harness).
