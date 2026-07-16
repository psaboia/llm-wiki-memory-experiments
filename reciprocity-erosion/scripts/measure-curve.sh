#!/usr/bin/env bash
# measure-curve.sh — measure reciprocity violations at each round of each chain,
# reading state from the wiki's git history (NOT from any agent's self-report).
#
# For every chain and every round N, it finds the commit whose message starts
# "roundN", extracts the wiki tree at that commit with `git archive`, and runs
# measure.py on it. Output is one JSON object per (chain, round) on stdout.
#
# Usage:
#   OUT=/path/to/exp CONDITIONS="on off natural" REPLICATES=3 ROUNDS=8 \
#   ./measure-curve.sh > results/battery.jsonl
set -euo pipefail

OUT="${OUT:?set OUT to the seeded experiment dir}"
CONDITIONS="${CONDITIONS:-on off natural}"
REPLICATES="${REPLICATES:-3}"
ROUNDS="${ROUNDS:-8}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEASURE="$HERE/../measure.py"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
for cond in $CONDITIONS; do
  for rep in $(seq 1 "$REPLICATES"); do
    id="$cond-r$rep"
    W="$OUT/chain-$id/project/wiki/tidewatch-$id.wiki"
    for n in $(seq 1 "$ROUNDS"); do
      sha="$(git -C "$W" log --format='%H %s' | awk -v k="round$n:" '$2==k{print $1}' | head -1)"
      [ -z "$sha" ] && sha="$(git -C "$W" log --format='%H %s' | grep -E "round$n[: ]" | awk '{print $1}' | head -1)"
      d="$TMP/$id-r$n"; mkdir -p "$d"
      git -C "$W" archive "$sha" | tar -x -C "$d"
      line="$(python3 "$MEASURE" "$d")"
      echo "{\"chain\":\"$id\",\"cond\":\"$cond\",\"round\":$n,${line#\{}"
    done
  done
done
