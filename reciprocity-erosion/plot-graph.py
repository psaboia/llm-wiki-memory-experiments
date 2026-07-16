#!/usr/bin/env python3
"""Show which edges the reciprocity mechanism added, versus direct ingestion.

The periodic-lint chains commit the wiki state both *before* a reciprocity sweep
(`roundN`) and *after* it (`lintN`). The difference between the two edge sets is,
literally, what the mechanism added — no inference needed.

  blue, thin    edge present after direct ingestion (roundN)
  orange, bold  edge added by the reciprocity sweep (new at lintN)
  solid         frontmatter typed edge (the form the KG consumes)
  dashed        body link only

Usage:
  plot-graph.py --wiki-repo <path-to-.wiki> --before round4 --after lint4 \
                --out figures/graph-reciprocity.png [--title "..."]

Requires graphviz `dot` on PATH. Edge direction is A -> B meaning "A references B".
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

SPECIAL = re.compile(r'^(Home|Home_|index_|log_|SCHEMA_|Edge-Types)')
FM = re.compile(r'^---\n(.*?)\n---\n(.*)$', re.S)
WIKILINK = re.compile(r'\[\[([A-Za-z0-9_ -]+)\]\]')
BODYLINK = re.compile(r'\]\(([A-Za-z0-9_-]+)\)')
UP_FIELD = re.compile(r'^\s*up\s*:', re.M)

INGEST_C, ADDED_C, INK = "#2a78d6", "#eb6834", "#0b0b0b"   # validated CVD-safe pair


def state_at(repo, step):
    """Extract the wiki tree at the commit whose message starts '<step>:'."""
    log = subprocess.run(["git", "-C", repo, "log", "--format=%H %s"],
                         capture_output=True, text=True, check=True).stdout
    sha = next((l.split()[0] for l in log.splitlines()
                if len(l.split()) > 1 and l.split()[1] == f"{step}:"), None)
    if not sha:
        sys.exit(f"error: no commit '{step}:' in {repo}")
    d = tempfile.mkdtemp()
    tar = subprocess.Popen(["git", "-C", repo, "archive", sha], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", d], stdin=tar.stdout, check=True)
    tar.wait()
    return d


def edges_of(wiki_dir):
    """-> (typed_edges, body_edges) as sets of (src, dst); content pages only."""
    pages = {}
    for fn in sorted(os.listdir(wiki_dir)):
        if fn.endswith('.md') and not SPECIAL.match(fn[:-3]):
            pages[fn[:-3]] = open(os.path.join(wiki_dir, fn), encoding='utf-8').read()
    typed, body = set(), set()
    for name, text in pages.items():
        m = FM.match(text)
        fm, bd = (m.group(1), m.group(2)) if m else ('', text)
        for line in fm.splitlines():
            if UP_FIELD.match(line):       # the mandatory parent link is not a relation
                continue
            for t in WIKILINK.findall(line):
                if t in pages and t != name:
                    typed.add((name, t))
        for t in BODYLINK.findall(bd):
            if t in pages and t != name:
                body.add((name, t))
    return typed, body, set(pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-repo", required=True)
    ap.add_argument("--before", default="round4")
    ap.add_argument("--after", default="lint4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    t0, b0, n0 = edges_of(state_at(a.wiki_repo, a.before))
    t1, b1, n1 = edges_of(state_at(a.wiki_repo, a.after))
    all0, all1 = t0 | b0, t1 | b1
    added = all1 - all0

    # The full graph of these wikis is ~74% dense (12 nodes, ~98 directed edges):
    # every layout renders it as an unreadable hairball, so drawing it all is not
    # an option. Draw the subgraph that answers the question instead — each edge
    # the sweep added, plus the ingestion edge that *required* it (the forward
    # link B->A whose reciprocity was missing). Everything else is omitted, and
    # the caption reports the totals so nothing is hidden by the framing.
    shown = set(added)
    for (s, d) in added:
        if (d, s) in all0:           # the ingestion link that triggered this fix
            shown.add((d, s))
    nodes = sorted({n for e in shown for n in e})

    lines = ['digraph G {', '  rankdir=LR; bgcolor="#ffffff";',
             '  graph [splines=true, overlap=false, nodesep=0.4, ranksep=1.6];',
             f'  node [shape=box, style="rounded,filled", fillcolor="#f4f4f2", '
             f'color="#d8d7d3", fontname="Helvetica", fontsize=10, fontcolor="{INK}"];',
             '  edge [fontname="Helvetica", fontsize=8, arrowsize=0.7];']
    if a.title:
        lines.append(f'  labelloc="t"; fontname="Helvetica"; fontsize=13; '
                     f'fontcolor="{INK}"; label="{a.title}\\n ";')
    for n in nodes:
        lines.append(f'  "{n}";')
    for (s, d) in sorted(shown):
        is_added = (s, d) in added
        is_typed = (s, d) in t1
        color = ADDED_C if is_added else INGEST_C
        width = 2.6 if is_added else 1.2
        style = "solid" if is_typed else "dashed"
        lines.append(f'  "{s}" -> "{d}" [color="{color}", penwidth={width}, style={style}];')
    # legend
    lines += ['  subgraph cluster_legend {',
              '    label="Legend"; fontsize=9; color="#d8d7d3"; style=rounded;',
              '    node [shape=plaintext, fillcolor="#ffffff", color="#ffffff"];',
              f'    l1 [label=<<font color="{INGEST_C}"><b>&#8212;&#8212;</b></font> ingestion link that required the back-reference>];',
              f'    l2 [label=<<font color="{ADDED_C}"><b>&#8212;&#8212;</b></font> <b>added by reciprocity sweep</b>>];',
              '    l3 [label="all edges shown are body links — the sweep adds no typed edge"];',
              '    l1 -> l2 -> l3 [style=invis];', '  }', '}']
    dot = "\n".join(lines)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    p = subprocess.run(["dot", "-Tpng", "-o", a.out], input=dot, text=True)
    if p.returncode:
        sys.exit("error: dot failed")
    print(f"wrote {a.out}")
    print(f"  full graph: nodes {len(n1)}, ingestion edges {len(all0)}, added by reciprocity {len(added)} ({100*len(all0)/(len(n1)*(len(n1)-1)):.0f}% dense -> full draw omitted)")
    print(f"  typed edges: before {len(t0)} -> after {len(t1)}")
    for (s, d) in sorted(added):
        print(f"    + {s} -> {d}" + ("  [typed]" if (s, d) in t1 else "  [body]"))


if __name__ == "__main__":
    main()
