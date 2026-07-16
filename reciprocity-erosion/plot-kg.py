#!/usr/bin/env python3
"""Render the ACTUAL knowledge graph the template's KG pipeline produces.

Not a link graph: this reads the pipeline's own output (`graph-full.ttl`, built by
scripts/kg/build-graph.sh) and draws the semantic triples — page --predicate--> page
— which is what "KG-visible" means. Hierarchy (`up:`) is drawn faintly as context;
the semantic predicates carry the ink and are labelled.

Two things the figure surfaces, both real:
  * ghost nodes — the pipeline ingests SCHEMA_*.md and Edge-Types.md as if they
    were content pages, so their *illustrative examples* (Theory-X, Page-Name,
    Parent-Page, WIKI-INDEX) become real entities in the graph;
  * off-vocabulary predicates — the SCHEMA declares extends/supports/criticizes/
    related/source/derived_from, but agents invent others (dependsOn, partOf) and
    the pipeline passes them through unflagged.

Usage: plot-kg.py --ttl <graph-full.ttl> --out figures/kg.png [--title "..."]
"""
import argparse
import os
import re
import subprocess
import sys

from rdflib import Graph, URIRef

DECLARED = {"extends", "supports", "criticizes", "related", "source", "derived_from"}
# mentions = body links materialised by the pipeline; concept/conceptOf = tags.
# 264 mentions edges is a hairball and is not the semantic layer — reported, not drawn.
BULK = {"mentions", "concept", "conceptOf"}
INVERSES = {"extendedBy", "supportedBy", "criticizedBy", "relatedBy", "sourceOf", "derives"}
HIER = {"up", "parent"}

SEM_C, INV_C, GHOST_C, HIER_C, INK = "#2a78d6", "#1baf7a", "#eb6834", "#cfcecb", "#0b0b0b"
GHOSTS = {"Theory-X", "Page-Name", "Parent-Page", "WIKI-INDEX", "Page"}
SPECIAL = re.compile(r'^(Home|Home_|index_|log_|SCHEMA_|Edge-Types)')


def local(uri):
    u = str(uri)
    return u.rsplit("#", 1)[-1] if "#" in u else u.rsplit("/", 1)[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    g = Graph()
    g.parse(a.ttl, format="turtle")

    edges = []          # (src, pred, dst)
    for s, p, o in g:
        if not isinstance(o, URIRef) or "/page/" not in str(s) or "/page/" not in str(o):
            continue
        pred = local(p)
        if pred in HIER or pred in DECLARED or pred in INVERSES or pred not in ("type",):
            edges.append((local(s), pred, local(o)))

    # keep semantic + hierarchy; drop rdf plumbing
    keep = [(s, p, d) for (s, p, d) in edges
            if p in DECLARED | INVERSES | HIER or p not in ("a", "type")]
    bulk = [(s, p, d) for (s, p, d) in keep if p in BULK]
    sem = [(s, p, d) for (s, p, d) in keep if p not in HIER and p not in BULK]
    hier = [(s, p, d) for (s, p, d) in keep if p in HIER]

    nodes = {n for (s, _, d) in sem for n in (s, d)}
    nodes |= {s for (s, _, d) in hier if s in nodes} | {d for (_, _, d) in hier if d in nodes}

    lines = ['digraph KG {', '  rankdir=LR; bgcolor="#ffffff";',
             '  graph [splines=true, overlap=false, nodesep=0.45, ranksep=1.9];',
             f'  node [shape=box, style="rounded,filled", fillcolor="#f4f4f2", '
             f'color="#d8d7d3", fontname="Helvetica", fontsize=10, fontcolor="{INK}"];',
             '  edge [fontname="Helvetica", fontsize=8, arrowsize=0.7];']
    if a.title:
        lines.append(f'  labelloc="t"; fontname="Helvetica"; fontsize=13; '
                     f'fontcolor="{INK}"; label="{a.title}\\n ";')
    for n in sorted(nodes):
        if n in GHOSTS:
            lines.append(f'  "{n}" [fillcolor="#fdece4", color="{GHOST_C}", '
                         f'fontcolor="{GHOST_C}", style="rounded,filled,dashed"];')
        else:
            lines.append(f'  "{n}";')
    seen = set()
    for (s, p, d) in sorted(sem):
        if (s, p, d) in seen:
            continue
        seen.add((s, p, d))
        if p in INVERSES:
            color, style = INV_C, "dashed"
        elif p in DECLARED:
            color, style = SEM_C, "solid"
        else:                                   # off-vocabulary: agent-invented
            color, style = GHOST_C, "solid"
        lines.append(f'  "{s}" -> "{d}" [label="{p}", color="{color}", '
                     f'fontcolor="{color}", penwidth=1.8, style={style}];')
    for (s, p, d) in sorted(set(hier)):
        if s in nodes and d in nodes:
            lines.append(f'  "{s}" -> "{d}" [color="{HIER_C}", penwidth=0.6, '
                         f'style=dotted, arrowsize=0.5];')
    lines += ['  subgraph cluster_legend {',
              '    label="Legend"; fontsize=9; color="#d8d7d3"; style=rounded;',
              '    node [shape=plaintext, fillcolor="#ffffff", color="#ffffff"];',
              f'    l1 [label=<<font color="{SEM_C}"><b>&#8212;&#8212;</b></font> declared predicate (SCHEMA vocabulary)>];',
              f'    l2 [label=<<font color="{INV_C}"><b>- - -</b></font> inverse, materialised by the KG build>];',
              f'    l3 [label=<<font color="{GHOST_C}"><b>&#8212;&#8212;</b></font> <b>off-vocabulary predicate / ghost node</b> (agent-invented, or a SCHEMA example ingested as an entity)>];',
              f'    l4 [label=<<font color="{HIER_C}"><b>&#183;&#183;&#183;</b></font> up: hierarchy (context)>];',
              '    l1 -> l2 -> l3 -> l4 [style=invis];', '  }', '}']

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    p = subprocess.run(["dot", "-Tpng", "-o", a.out], input="\n".join(lines), text=True)
    if p.returncode:
        sys.exit("dot failed")
    preds = {}
    for (_, pr, _) in sem:
        preds[pr] = preds.get(pr, 0) + 1
    print(f"wrote {a.out}")
    print(f"  nodes {len(nodes)} | semantic triples {len(seen)} | hierarchy {len(set(hier))}")
    print(f"  predicates: {dict(sorted(preds.items(), key=lambda x: -x[1]))}")
    print(f"  bulk layer not drawn: {len(bulk)} triples (mentions/concept — body links & tags)")
    print(f"  ghost nodes present: {sorted(nodes & GHOSTS)}")
    print(f"  off-vocabulary predicates: {sorted(set(preds) - DECLARED - INVERSES)}")


if __name__ == "__main__":
    main()
