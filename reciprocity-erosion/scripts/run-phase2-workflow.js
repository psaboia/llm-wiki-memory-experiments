export const meta = {
  name: 'reciprocity-phase2',
  description: 'Phase 2 pre-registered: natural / periodic-lint / nudge, n=5 each, 8 rounds, single seed source — tests H1 (nudge suppresses typed edges) and H2 (periodic-lint does not)',
  phases: [{ title: 'Rounds', detail: '15 chains x 8 rounds (periodic-lint also sweeps at 4 and 8)' }],
}

const base = '/tmp/claude-1003/-home-pmoreira-llm-wiki-memory-template/555e531b-aa24-4d30-983a-c0279aab24e5/scratchpad/reciprocity-exp'
const REPS = [1, 2, 3, 4, 5]
const chains = [
  ...REPS.map(r => ({ id: `p2nat-r${r}`, cond: 'natural' })),
  ...REPS.map(r => ({ id: `p2lint-r${r}`, cond: 'periodic-lint' })),
  ...REPS.map(r => ({ id: `p2nudge-r${r}`, cond: 'nudge' })),
]

function wikiPath(id)    { return `${base}/chain-${id}/project/wiki/tidewatch-${id}.wiki` }
function projectPath(id) { return `${base}/chain-${id}/project` }

const NATURAL_STEP = "Follow the wiki's normal documented Ingest procedure as described in CLAUDE.md and SCHEMA_*.md — do what the procedure says, no more and no less. Cross-reference related pages as that procedure describes. Do not add any extra reciprocity-enforcement beyond the documented procedure, and do not deliberately skip steps it calls for."

function nudgeStep(proj, wiki) {
  return `Before committing, run the mechanical reciprocity checker on your work (this simulates a post-write hook surfacing one-way links):
  python3 ${proj}/scripts/wiki-reciprocity.py ${wiki}
For EACH violation "A -> B" it reports, fix it: open the TARGET page B and add a back-reference to A (a See also entry or a body mention), UNLESS B is a genuine hub-and-spoke page that legitimately lists many children — then add \`hub: true\` to B's frontmatter instead. Re-run the checker until it reports 0 violations. Do not invent links the content does not support; a See also pointing back suffices.`
}

function roundPrompt(chain, n) {
  const proj = projectPath(chain.id)
  const wiki = wikiPath(chain.id)
  const content = `${base}/rounds/round${n}.md`
  const extra = chain.cond === 'nudge' ? `\n\n${nudgeStep(proj, wiki)}` : ''
  return `You are ONE editing session on an existing llm-wiki. Work ONLY inside ${proj}. The wiki sub-repo is at ${wiki}. NEVER touch any path outside ${proj}.

This is round ${n} of an ongoing project. Earlier sessions already created pages, but you have NO memory of them — discover the current state yourself by listing and reading the wiki directory (${wiki}).

Read ${wiki}/SCHEMA_*.md for the conventions: page format, frontmatter (required type: and up:, optional typed edges extends:/supports:/criticizes:/related:), and cross-reference styles ([[Page]] in frontmatter, [Display](Page-Name) in body).

Ingest the new source document at ${content}: create pages for genuinely new entities/concepts it introduces, and connect them to the related existing pages it mentions (with body links and/or typed edges). Update index_*.md and append a one-line entry to log_*.md.

${NATURAL_STEP}${extra}

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
  - Open the TARGET page B and add a back-reference to A — a "See also" entry or an explicit body mention of A.
  - EXCEPTION: if B is a genuine hub-and-spoke page that legitimately lists many children, add \`hub: true\` to B's frontmatter instead.

Re-run the checker until it reports 0 violations. Do not invent links the content does not support.

Then make EXACTLY ONE commit in the wiki sub-repo:
  git -C ${wiki} add -A && git -C ${wiki} commit -m "lint${n}: reciprocity sweep"
Do not push. Return a single line: violations before and after.`
}

const results = await parallel(chains.map(chain => async () => {
  const steps = []
  for (const n of [1, 2, 3, 4, 5, 6, 7, 8]) {
    const o = await agent(roundPrompt(chain, n), { label: `${chain.id}:r${n}`, phase: 'Rounds' })
    steps.push({ step: `r${n}`, ok: o != null })
    if (chain.cond === 'periodic-lint' && (n === 4 || n === 8)) {
      const l = await agent(lintPrompt(chain.id, n), { label: `${chain.id}:lint${n}`, phase: 'Rounds' })
      steps.push({ step: `lint${n}`, ok: l != null })
    }
  }
  return { id: chain.id, cond: chain.cond, steps }
}))

return { chains: results.filter(Boolean) }
