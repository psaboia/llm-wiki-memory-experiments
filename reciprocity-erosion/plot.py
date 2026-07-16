#!/usr/bin/env python3
"""Render the reciprocity-erosion curves from the raw battery results.

Reads all results/battery-*.jsonl and writes figures/erosion-curves.png:
a two-panel typed-edge chart across five enforcement conditions
(off / natural / periodic-lint / gate-on / nudge), mean of 3 replicates.
Left panel is full scale (shows the suppressed case running away); right panel
zooms to 0-4.5 to separate the four low conditions. Regenerable: re-run after
new batteries.

Colour is categorical (validated CVD-safe) and backed by line-style + marker as
secondary encoding, so the figure survives greyscale/print and CVD.
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

# metric -> per (cond, round) list of typed-edge violation counts
data = defaultdict(lambda: defaultdict(list))

def add(cond, rnd, val):
    data[cond][rnd].append(val)

# Erosion curves only (batteries B-E). Battery A is single-ingest variance,
# a different format/purpose, and is not part of the over-time curve.
EROSION = ("battery-B-erosion.jsonl", "battery-C-natural.jsonl",
           "battery-D-periodic-lint.jsonl", "battery-E-nudge.jsonl")
for fn in EROSION:
    path = os.path.join(RES, fn)
    if not os.path.exists(path):
        continue
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        # battery D (periodic-lint): {cond, step, typed}; use only round steps
        if "step" in r:
            if r["step"].startswith("round"):
                add(r["cond"], int(r["step"][5:]), r["typed"])
            continue
        # batteries B/C/E: {chain|cond, round, viol_typed_current_gate}
        cond = r.get("cond") or ("on" if r["chain"].startswith("on")
                                 else "off" if r["chain"].startswith("off") else None)
        if cond is None:
            continue
        add(cond, r["round"], r["viol_typed_current_gate"])

# entity -> (colour, linestyle, marker, label), ordered by enforcement strength
STYLE = [
    ("off",           "#2a78d6", "-",              "o", "off (check suppressed)"),
    ("natural",       "#008300", "--",             "s", "natural (procedure only)"),
    ("periodic-lint", "#e87ba4", "-.",             "D", "periodic-lint (every 4 rounds)"),
    ("on",            "#eda100", ":",              "^", "gate-on (instruction/round)"),
    ("nudge",         "#1baf7a", (0, (1, 1)),      "v", "nudge (mechanical/write)"),
]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e2"

def curve(cond):
    xs = sorted(data[cond])
    return xs, [st.mean(data[cond][x]) for x in xs]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.4))
for ax, ymax, title in [(axL, None, "Full scale"), (axR, 4.5, "Zoom (the four low conditions)")]:
    for cond, color, ls, mk, label in STYLE:
        x, y = curve(cond)
        ax.plot(x, y, color=color, linestyle=ls, marker=mk, markersize=6,
                linewidth=2, label=label, zorder=3)
        ax.annotate(f"{y[-1]:.1f}", (x[-1], y[-1]), textcoords="offset points",
                    xytext=(6, 0), va="center", fontsize=8.5, color=color, fontweight="bold")
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")
    ax.set_xlabel("editing round", fontsize=9.5, color=MUTED)
    ax.set_xticks(range(1, 9))
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.margins(x=0.10)
    ax.set_ylim(bottom=0, top=ymax)

axL.set_ylabel("typed-edge violations (mean of 3 replicates)", fontsize=9.5, color=MUTED)
axL.legend(frameon=False, fontsize=8.5, loc="upper left")
fig.suptitle("Reciprocity vs enforcement strength — five conditions over 8 editing rounds",
             fontsize=12, color=INK, x=0.02, ha="left", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.95])
dest = os.path.join(OUT, "erosion-curves.png")
fig.savefig(dest, dpi=150, facecolor="#ffffff")
print("wrote", dest)
