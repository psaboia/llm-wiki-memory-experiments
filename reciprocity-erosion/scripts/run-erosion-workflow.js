export const meta = {
  name: 'reciprocity-erosion',
  description: 'Measure reciprocity-violation accumulation over 8 editing rounds, gate-on vs gate-off, 3 replicates each',
  phases: [{ title: 'Rounds', detail: '6 chains x 8 sequential rounds, fresh agent per round' }],
}

const base = '/tmp/claude-1003/-home-pmoreira-llm-wiki-memory-template/555e531b-aa24-4d30-983a-c0279aab24e5/scratchpad/reciprocity-exp'
const rounds = [1, 2, 3, 4, 5, 6, 7, 8]
const chains = [
  { id: 'on-r1', cond: 'on' }, { id: 'on-r2', cond: 'on' }, { id: 'on-r3', cond: 'on' },
  { id: 'off-r1', cond: 'off' }, { id: 'off-r2', cond: 'off' }, { id: 'off-r3', cond: 'off' },
]

function wikiPath(id)    { return `${base}/chain-${id}/project/wiki/tidewatch-${id}.wiki` }
function projectPath(id) { return `${base}/chain-${id}/project` }

function roundPrompt(chain, n) {
  const proj = projectPath(chain.id)
  const wiki = wikiPath(chain.id)
  const content = `${base}/rounds/round${n}.md`
  const gateOn =
    "Follow the Verification Gate at wiki/agents/verification-gate.md before committing. In particular: for EVERY cross-reference you add from one page to another, make sure the TARGET page references back (a See also entry or an explicit body mention) — edit the target pages as needed so every link is bidirectional. Reciprocity in both directions is required."
  const gateOff =
    "Do NOT run the verification-gate procedure. Create the new page(s) and their forward links to the existing pages they mention, then move on — do not make a point of going back to edit the older target pages to add back-references. Ingest the new material as a quick, single-purpose session would."
  const cond = chain.cond === 'on' ? gateOn : gateOff
  return `You are ONE editing session on an existing llm-wiki. Work ONLY inside ${proj}. The wiki sub-repo is at ${wiki}. NEVER touch any path outside ${proj}.

This is round ${n} of an ongoing project. Earlier sessions already created pages, but you have NO memory of them — discover the current state yourself by listing and reading the wiki directory (${wiki}).

Read ${wiki}/SCHEMA_*.md for the conventions: page format, frontmatter (required type: and up:, optional typed edges extends:/supports:/criticizes:/related:), and cross-reference styles ([[Page]] in frontmatter, [Display](Page-Name) in body).

Ingest the new source document at ${content}: create pages for genuinely new entities/concepts it introduces, and connect them to the related existing pages it mentions (with body links and/or typed edges). Update index_*.md and append a one-line entry to log_*.md.

${cond}

Then make EXACTLY ONE commit in the wiki sub-repo (stage everything, one commit):
  git -C ${wiki} add -A && git -C ${wiki} commit -m "round${n}: <short description>"
Do not push. Return a single line naming the pages you created or edited.`
}

const results = await parallel(chains.map(chain => async () => {
  const perRound = []
  for (const n of rounds) {
    const out = await agent(roundPrompt(chain, n), { label: `${chain.id}:r${n}`, phase: 'Rounds' })
    perRound.push({ n, ok: out != null })
  }
  return { id: chain.id, cond: chain.cond, rounds: perRound }
}))

return { chains: results.filter(Boolean) }
