export const meta = {
  name: 'reciprocity-erosion-periodic-lint',
  description: '4th condition: natural editing with a mechanical wiki-reciprocity lint+fix sweep after rounds 4 and 8 (3 replicates)',
  phases: [{ title: 'Rounds', detail: '3 chains x (8 natural rounds + lint sweeps at 4 and 8)' }],
}

const base = '/tmp/claude-1003/-home-pmoreira-llm-wiki-memory-template/555e531b-aa24-4d30-983a-c0279aab24e5/scratchpad/reciprocity-exp'
const chains = [{ id: 'lint-r1' }, { id: 'lint-r2' }, { id: 'lint-r3' }]

function wikiPath(id)    { return `${base}/chain-${id}/project/wiki/tidewatch-${id}.wiki` }
function projectPath(id) { return `${base}/chain-${id}/project` }

function roundPrompt(id, n) {
  const proj = projectPath(id)
  const wiki = wikiPath(id)
  const content = `${base}/rounds/round${n}.md`
  const cond = "Follow the wiki's normal documented Ingest procedure as described in CLAUDE.md and SCHEMA_*.md — do what the procedure says, no more and no less. Cross-reference related pages as that procedure describes. Do not add any extra reciprocity-enforcement beyond the documented procedure, and do not deliberately skip steps it calls for."
  return `You are ONE editing session on an existing llm-wiki. Work ONLY inside ${proj}. The wiki sub-repo is at ${wiki}. NEVER touch any path outside ${proj}.

This is round ${n} of an ongoing project. Earlier sessions already created pages, but you have NO memory of them — discover the current state yourself by listing and reading the wiki directory (${wiki}).

Read ${wiki}/SCHEMA_*.md for the conventions: page format, frontmatter (required type: and up:, optional typed edges extends:/supports:/criticizes:/related:), and cross-reference styles ([[Page]] in frontmatter, [Display](Page-Name) in body).

Ingest the new source document at ${content}: create pages for genuinely new entities/concepts it introduces, and connect them to the related existing pages it mentions (with body links and/or typed edges). Update index_*.md and append a one-line entry to log_*.md.

${cond}

Then make EXACTLY ONE commit in the wiki sub-repo (stage everything, one commit):
  git -C ${wiki} add -A && git -C ${wiki} commit -m "round${n}: <short description>"
Do not push. Return a single line naming the pages you created or edited.`
}

function lintPrompt(id, n) {
  const proj = projectPath(id)
  const wiki = wikiPath(id)
  return `You are running a reciprocity lint pass on an llm-wiki. Work ONLY inside ${proj}. NEVER touch any path outside it.

Run the mechanical reciprocity checker on the wiki:
  python3 ${proj}/scripts/wiki-reciprocity.py ${wiki}
It prints every one-way link as "A -> B (B does not reference A back)".

For EACH violation it lists, fix it:
  - Open the TARGET page B and add a back-reference to A — a "See also" entry or an explicit body mention of A ([A](A) in the body, or [[A]] in frontmatter if a typed relationship fits).
  - EXCEPTION: if B is a genuine hub-and-spoke page that legitimately lists many children (an overview/index-like content page), do NOT force a back-reference — instead add \`hub: true\` to B's frontmatter.

Re-run the checker until it reports 0 violations (genuine hubs, now marked \`hub: true\`, are exempt and will drop out). Do not invent links that the content does not support; a "See also" pointing back is enough.

Then make EXACTLY ONE commit in the wiki sub-repo:
  git -C ${wiki} add -A && git -C ${wiki} commit -m "lint${n}: reciprocity sweep"
Do not push. Return a single line: how many violations the checker reported before you started, and after.`
}

const results = await parallel(chains.map(chain => async () => {
  const steps = []
  for (const n of [1, 2, 3, 4]) {
    const o = await agent(roundPrompt(chain.id, n), { label: `${chain.id}:r${n}`, phase: 'Rounds' })
    steps.push({ step: `r${n}`, ok: o != null })
  }
  const l4 = await agent(lintPrompt(chain.id, 4), { label: `${chain.id}:lint4`, phase: 'Rounds' })
  steps.push({ step: 'lint4', ok: l4 != null })
  for (const n of [5, 6, 7, 8]) {
    const o = await agent(roundPrompt(chain.id, n), { label: `${chain.id}:r${n}`, phase: 'Rounds' })
    steps.push({ step: `r${n}`, ok: o != null })
  }
  const l8 = await agent(lintPrompt(chain.id, 8), { label: `${chain.id}:lint8`, phase: 'Rounds' })
  steps.push({ step: 'lint8', ok: l8 != null })
  return { id: chain.id, steps }
}))

return { chains: results.filter(Boolean) }
