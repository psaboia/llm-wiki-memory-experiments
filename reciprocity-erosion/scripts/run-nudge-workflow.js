export const meta = {
  name: 'reciprocity-erosion-nudge',
  description: '5th condition: per-write mechanical nudge — each round ingests, runs wiki-reciprocity.py on its own writes, fixes, then commits (faithful PostToolUse-hook proxy, 3 replicates)',
  phases: [{ title: 'Rounds', detail: '3 chains x 8 rounds, mechanical check + fix every round before commit' }],
}

const base = '/tmp/claude-1003/-home-pmoreira-llm-wiki-memory-template/555e531b-aa24-4d30-983a-c0279aab24e5/scratchpad/reciprocity-exp'
const rounds = [1, 2, 3, 4, 5, 6, 7, 8]
const chains = [{ id: 'nudge-r1' }, { id: 'nudge-r2' }, { id: 'nudge-r3' }]

function wikiPath(id)    { return `${base}/chain-${id}/project/wiki/tidewatch-${id}.wiki` }
function projectPath(id) { return `${base}/chain-${id}/project` }

function roundPrompt(id, n) {
  const proj = projectPath(id)
  const wiki = wikiPath(id)
  const content = `${base}/rounds/round${n}.md`
  return `You are ONE editing session on an existing llm-wiki. Work ONLY inside ${proj}. The wiki sub-repo is at ${wiki}. NEVER touch any path outside ${proj}.

This is round ${n} of an ongoing project. Earlier sessions already created pages, but you have NO memory of them — discover the current state yourself by listing and reading the wiki directory (${wiki}).

Read ${wiki}/SCHEMA_*.md for the conventions: page format, frontmatter (required type: and up:, optional typed edges), and cross-reference styles ([[Page]] in frontmatter, [Display](Page-Name) in body).

STEP 1 — Ingest the new source at ${content}: follow the wiki's normal documented Ingest procedure (create pages for genuinely new entities/concepts, connect them to related existing pages, update index_*.md, append a one-line log entry). No more and no less than the procedure says.

STEP 2 — Before committing, run the mechanical reciprocity checker on your work (this simulates a post-write hook surfacing one-way links):
  python3 ${proj}/scripts/wiki-reciprocity.py ${wiki}
For EACH violation "A -> B" it reports, fix it: open the TARGET page B and add a back-reference to A (a See also entry or a body mention), UNLESS B is a genuine hub-and-spoke page that legitimately lists many children — then add \`hub: true\` to B's frontmatter instead. Re-run the checker until it reports 0 violations (marked hubs are exempt and drop out). Do not invent links the content does not support; a See also pointing back suffices.

STEP 3 — Make EXACTLY ONE commit in the wiki sub-repo:
  git -C ${wiki} add -A && git -C ${wiki} commit -m "round${n}: <short description>"
Do not push. Return a single line: the pages you created/edited, and how many violations the checker reported before you fixed them.`
}

const results = await parallel(chains.map(chain => async () => {
  const perRound = []
  for (const n of rounds) {
    const o = await agent(roundPrompt(chain.id, n), { label: `${chain.id}:r${n}`, phase: 'Rounds' })
    perRound.push({ n, ok: o != null })
  }
  return { id: chain.id, rounds: perRound }
}))

return { chains: results.filter(Boolean) }
