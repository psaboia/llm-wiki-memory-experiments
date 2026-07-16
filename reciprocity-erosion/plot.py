#!/usr/bin/env python3
"""Render the reciprocity-erosion curves from the raw battery results.

Reads results/battery-B-erosion.jsonl (gate-off + gate-on) and
results/battery-C-natural.jsonl (natural), and writes
figures/erosion-curves.png. Regenerable: re-run after new batteries.

Two panels (typed-edge = today's gate; any-means = proposed criterion). Three
conditions per panel, mean of 3 replicates, with a min–max ribbon across the
replicates so the spread is visible. Colour is categorical (validated CVD-safe:
blue/green/magenta) and is backed by line-style + marker as secondary encoding,
so the figure survives greyscale/print and colour-vision deficiency.
"""
import json, os, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

def cond_of(row):
    c = row.get("cond")
    if c:
        return c
    ch = row["chain"]
    return "on" if ch.startswith("on") else "off" if ch.startswith("off") else "natural"

rows = []
for fn in ("battery-B-erosion.jsonl", "battery-C-natural.jsonl"):
    p = os.path.join(RES, fn)
    if os.path.exists(p):
        rows += [json.loads(l) for l in open(p)]

def series(metric, cond):
    g = defaultdict(list)
    for r in rows:
        if cond_of(r) == cond:
            g[r["round"]].append(r[metric])
    rounds = sorted(g)
    mean = [st.mean(g[n]) for n in rounds]
    lo = [min(g[n]) for n in rounds]
    hi = [max(g[n]) for n in rounds]
    return rounds, mean, lo, hi

# entity -> (colour, linestyle, marker, label). Order/hues are the validated
# categorical slots; style+marker are the secondary encoding.
STYLE = {
    "off":     ("#2a78d6", "-",  "o", "gate-off (suppressed)"),
    "natural": ("#008300", "--", "s", "natural (documented)"),
    "on":      ("#e87ba4", ":",  "^", "gate-on (enforced)"),
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e2"
PANELS = [
    ("viol_typed_current_gate", "Typed-edge violations\n(what the gate checks today)"),
    ("viol_body_anymeans",      "Any-means violations\n(proposed criterion)"),
]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True)
for ax, (metric, title) in zip(axes, PANELS):
    for cond in ("off", "natural", "on"):
        color, ls, mk, label = STYLE[cond]
        x, mean, lo, hi = series(metric, cond)
        ax.fill_between(x, lo, hi, color=color, alpha=0.12, linewidth=0)
        ax.plot(x, mean, color=color, linestyle=ls, marker=mk, markersize=6,
                linewidth=2, label=label, zorder=3)
        # direct label at the last round (relief for the low-contrast slot + no hover)
        ax.annotate(f"{mean[-1]:.1f}", (x[-1], mean[-1]),
                    textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=9, color=color, fontweight="bold")
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")
    ax.set_xlabel("editing round", fontsize=9.5, color=MUTED)
    ax.set_xticks(range(1, 9))
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.margins(x=0.08)
    ax.set_ylim(bottom=0)

axes[0].set_ylabel("violations (mean of 3 replicates)", fontsize=9.5, color=MUTED)
axes[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Reciprocity erosion over editing rounds — gate-off vs natural vs gate-on",
             fontsize=12, color=INK, x=0.02, ha="left", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.96])
dest = os.path.join(OUT, "erosion-curves.png")
fig.savefig(dest, dpi=150, facecolor="#ffffff")
print("wrote", dest)
