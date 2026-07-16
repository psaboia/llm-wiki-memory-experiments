#!/usr/bin/env bash
# seed-chains.sh — create N isolated, freshly-instantiated wiki projects to run
# an erosion battery against. Each "chain" is one derived project with its own
# wiki sub-repo, seeded identically from a pinned template snapshot.
#
# Hermetic snapshot: `git archive HEAD` from the template gives ONLY tracked
# files at that commit — it excludes the template's own wiki sub-repo, its
# dev-self CLAUDE.md/settings/hooks, and any untracked artifacts. This is what
# keeps a real template clone from leaking into the experiment.
#
# Usage:
#   TEMPLATE=/path/to/llm-wiki-memory-template \
#   OUT=/path/to/exp \
#   CONDITIONS="on off natural" REPLICATES=3 \
#   ./seed-chains.sh
#
# Produces: $OUT/chain-<cond>-r<rep>/project/  (each with wiki/tidewatch-<cond>-r<rep>.wiki/)
set -euo pipefail

TEMPLATE="${TEMPLATE:?set TEMPLATE to a clone of llm-wiki-memory-template}"
OUT="${OUT:?set OUT to an output directory}"
CONDITIONS="${CONDITIONS:-on off natural}"
REPLICATES="${REPLICATES:-3}"

SHA="$(git -C "$TEMPLATE" rev-parse HEAD)"
echo "seeding from template $TEMPLATE @ $SHA"

mkdir -p "$OUT/template-snapshot"
git -C "$TEMPLATE" archive HEAD | tar -x -C "$OUT/template-snapshot"
echo "$SHA" > "$OUT/template-snapshot.sha"

for cond in $CONDITIONS; do
  for rep in $(seq 1 "$REPLICATES"); do
    id="$cond-r$rep"; P="$OUT/chain-$id/project"
    rm -rf "$OUT/chain-$id"; mkdir -p "$P"
    cp -r "$OUT/template-snapshot/." "$P/"
    (
      cd "$P"
      git init -q; git add -A; git -c user.email=t@t -c user.name=t commit -qm base
      git remote add origin "git@github.com:testorg/tidewatch-$id.git"   # fake origin: instantiate derives the wiki name from it
      ./scripts/instantiate.sh "Tidewatch $id" --agent=claude-code >/dev/null 2>&1
      w="wiki/tidewatch-$id.wiki"
      git -C "$w" config user.email "$id@test"
      git -C "$w" config user.name  "Chain $id"
    )
    echo "  chain-$id ready"
  done
done
