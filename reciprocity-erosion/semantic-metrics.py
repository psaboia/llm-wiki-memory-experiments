#!/usr/bin/env python3
"""Score a wiki's link structure against the corpus ground truth.

Answers "does the reciprocity mechanism produce semantically meaningful edges?"
mechanically — no LLM judge, so no LLM-judging-LLM circularity.

Metrics (all over links between CANONICAL entities, i.e. pages that resolve to a
ground-truth entity via ground-truth.json's alias lists):

  recall          fraction of ground-truth relations represented by any link
  typed_coverage  fraction of ground-truth relations expressed as a FRONTMATTER
                  typed edge (the form the KG pipeline consumes), not merely a
                  body link
  spurious_rate   fraction of canonical-to-canonical links whose entity pair is
                  NOT asserted anywhere in the corpus — the hallucination /
                  padding proxy
  prose_backref   of the reciprocal back-references present, the fraction stated
                  in body prose rather than only inside a bare "See also" line —
                  the padding proxy (a See-also-only back-ref says "related"
                  without saying how)

Pages that do not resolve to a canonical entity (agent-invented decompositions
like Calibration-Header) are reported as `extra_pages` and excluded from scoring:
they are legitimate sub-entities of the corpus, not errors, and the ground truth
says nothing about them.

Usage: semantic-metrics.py <wiki-dir> [--ground-truth PATH] [--json]
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SPECIAL = re.compile(r'^(Home|Home_|index_|log_|SCHEMA_|Edge-Types)')
FM = re.compile(r'^---\n(.*?)\n---\n(.*)$', re.S)
WIKILINK = re.compile(r'\[\[([A-Za-z0-9_ -]+)\]\]')
BODYLINK = re.compile(r'\]\(([A-Za-z0-9_-]+)\)')
UP_FIELD = re.compile(r'^\s*up\s*:', re.M)
SEEALSO = re.compile(r'^\s*(##\s*)?see also', re.I)


def load_gt(path):
    gt = json.load(open(path, encoding="utf-8"))
    alias = {}
    for canon, names in gt["entities"].items():
        for n in names:
            alias[n.lower()] = canon
    pairs = {frozenset((r["a"], r["b"])) for r in gt["relations"]}
    return alias, pairs


def split_fm(text):
    m = FM.match(text)
    return (m.group(1), m.group(2)) if m else ('', text)


def analyze(wiki_dir, alias, gt_pairs):
    pages = {}
    for fn in sorted(os.listdir(wiki_dir)):
        if fn.endswith('.md') and not SPECIAL.match(fn[:-3]):
            pages[fn[:-3]] = open(os.path.join(wiki_dir, fn), encoding='utf-8').read()

    canon = {p: alias.get(p.lower()) for p in pages}
    extra = sorted(p for p, c in canon.items() if c is None)

    typed_pairs, any_pairs = set(), set()
    backrefs_prose, backrefs_seealso_only = 0, 0

    for name, text in pages.items():
        a = canon[name]
        fm, body = split_fm(text)
        # typed edges: frontmatter wikilinks EXCLUDING the mandatory `up:` line
        for line in fm.splitlines():
            if UP_FIELD.match(line):
                continue
            for t in WIKILINK.findall(line):
                b = canon.get(t)
                if a and b and a != b:
                    typed_pairs.add(frozenset((a, b)))
                    any_pairs.add(frozenset((a, b)))
        # body links
        for t in BODYLINK.findall(body):
            b = canon.get(t)
            if a and b and a != b:
                any_pairs.add(frozenset((a, b)))

    # prose vs see-also-only: for each body link, is the target named outside a
    # "See also" line on the source page?
    for name, text in pages.items():
        if not canon[name]:
            continue
        _, body = split_fm(text)
        in_seealso = False
        prose_targets, seealso_targets = set(), set()
        for line in body.splitlines():
            if SEEALSO.match(line):
                in_seealso = True
                for t in BODYLINK.findall(line):
                    seealso_targets.add(t)
                continue
            targets = BODYLINK.findall(line)
            if targets:
                (seealso_targets if in_seealso else prose_targets).update(targets)
            if line.startswith('#'):
                in_seealso = False
        for t in prose_targets:
            if canon.get(t):
                backrefs_prose += 1
        for t in seealso_targets - prose_targets:
            if canon.get(t):
                backrefs_seealso_only += 1

    spurious = {p for p in any_pairs if p not in gt_pairs}
    n_gt = len(gt_pairs)
    n_any = len(any_pairs) or 1
    n_back = (backrefs_prose + backrefs_seealso_only) or 1
    return {
        "content_pages": len(pages),
        "canonical_pages": sum(1 for c in canon.values() if c),
        "extra_pages": extra,
        "gt_relations": n_gt,
        "recall": round(len(any_pairs & gt_pairs) / n_gt, 3),
        "typed_coverage": round(len(typed_pairs & gt_pairs) / n_gt, 3),
        "spurious_rate": round(len(spurious) / n_any, 3),
        "spurious_pairs": sorted("|".join(sorted(p)) for p in spurious),
        "prose_backref_ratio": round(backrefs_prose / n_back, 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_dir")
    ap.add_argument("--ground-truth", default=os.path.join(HERE, "ground-truth.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    alias, pairs = load_gt(args.ground_truth)
    res = analyze(args.wiki_dir, alias, pairs)
    print(json.dumps(res) if args.json else json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
