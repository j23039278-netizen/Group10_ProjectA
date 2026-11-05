// SEAGAS — Search the skills library while a student types, best match first: the name or an
// alias ("JS" finds JavaScript), then close spellings if nothing matched ("pyhton" finds Python),
// then skills whose description uses the words ("dashboard" finds Tableau).
// No React here, so `npm test` can run it on its own.

const RANK = { exact: 0, start: 1, word: 2, inside: 3, close: 4, related: 5 }
const ON_ALIAS = 0.5   // the same kind of match on the name ranks above one on an alias

const clean = (text) => (text || '').toLowerCase().replace(/[^\p{L}\p{N}+#]+/gu, ' ').trim()
const squeeze = (text) => text.replace(/ /g, '')
const startsSomeWord = (word, words) => words.some(w => w.startsWith(word))

function directRank(query, text, onAlias) {
  const target = clean(text)
  const words = target.split(' ')
  if (squeeze(target) === squeeze(query)) return RANK.exact
  if (squeeze(target).startsWith(squeeze(query))) return RANK.start
  if (query.split(' ').every(w => startsSomeWord(w, words))) return RANK.word
  if (onAlias || query.length < 3) return null
  // Inside a word, names only. Three letters must end the word: "sql" finds MySQL, "git" not Digital
  const inside = query.length > 3 ? words.some(w => w.includes(query)) : words.some(w => w.endsWith(query))
  return inside ? RANK.inside : null
}

// Edits (insert, delete, replace, swap two neighbours) that turn word into text; with asStart,
// into the best start of text, so "pyht" is one edit from "python".
function editDistance(word, text, asStart = false) {
  let twoBack = []
  let previous = Array.from({ length: text.length + 1 }, (_, j) => j)
  for (let i = 1; i <= word.length; i++) {
    const row = [i]
    for (let j = 1; j <= text.length; j++) {
      const replace = previous[j - 1] + (word[i - 1] === text[j - 1] ? 0 : 1)
      row[j] = Math.min(previous[j] + 1, row[j - 1] + 1, replace)
      if (i > 1 && j > 1 && word[i - 1] === text[j - 2] && word[i - 2] === text[j - 1]) {
        row[j] = Math.min(row[j], twoBack[j - 2] + 1)
      }
    }
    twoBack = previous
    previous = row
  }
  return asStart ? Math.min(...previous) : previous[text.length]
}

// Typos between a typed word and a word of the library, or null if too far apart. Short words get
// less room, or "sql" would find half the library. The first letter must match: people rarely
// mistype it, and it stops "test" from finding "REST". A match on only the start of a word (the
// student is still typing) counts as half a typo more than the same match on the whole word.
function wordTypos(word, target) {
  if (word.length < 3 || target.length < 3 || word[0] !== target[0]) return null
  const allowed = word.length < 6 ? 1 : 2
  const whole = editDistance(word, target)
  if (whole <= allowed) return whole
  const start = word.length > 3 ? editDistance(word, target, true) : Infinity
  return start <= allowed ? start + 0.5 : null
}

function typosIn(query, text) {
  const target = clean(text)
  const words = target.split(' ')
  let total = 0
  for (const word of query.split(' ')) {
    if (startsSomeWord(word, words)) continue
    const typos = words.map(w => wordTypos(word, w)).filter(n => n !== null)
    if (!typos.length) { total = null; break }
    total += Math.min(...typos)
  }
  // Also as one word, so "powrbi" finds Power BI
  const joined = wordTypos(squeeze(query), squeeze(target))
  if (total === null) return joined
  return joined === null ? total : Math.min(total, joined)
}

// The best score of a skill's name and aliases; score(text, onAlias) returns null for no match
function bestOf(skill, score) {
  let best = null
  const consider = (value, alias) => {
    if (value !== null && (!best || value < best.value)) best = { value, alias }
  }
  consider(score(skill.skill_name, false))
  for (const alias of skill.aliases || []) consider(score(alias, true), alias)
  return best
}

const byRankThenName = (a, b) => a.rank - b.rank || a.skill.skill_name.localeCompare(b.skill.skill_name)

// Only the closest spellings, so a typo does not bring in everything one edit further away
function closestSpellings(skills, query) {
  const found = skills.flatMap(skill => {
    const best = bestOf(skill, text => typosIn(query, text))
    return best ? [{ skill, ...best }] : []
  })
  const closest = Math.min(...found.map(f => f.value))
  return found.filter(f => f.value === closest).map(({ skill, alias }) => (
    { skill, alias, rank: RANK.close + (alias ? ON_ALIAS : 0) }
  ))
}

// Returns [{ skill, rank, alias, related }], best first. An empty query keeps the list's own order.
export function searchSkills(skills, text) {
  const query = clean(text)
  if (!query) return skills.map(skill => ({ skill }))

  const direct = skills.flatMap(skill => {
    const best = bestOf(skill, (t, onAlias) => directRank(query, t, onAlias))
    return best ? [{ skill, alias: best.alias, rank: best.value + (best.alias ? ON_ALIAS : 0) }] : []
  })
  const others = (found) => skills.filter(s => !found.some(m => m.skill === s))

  // A typo is only suspected when no name or alias starts with what was typed
  const close = direct.some(m => m.rank < RANK.inside) ? [] : closestSpellings(others(direct), query)
  const matches = [...direct, ...close]

  // Short words such as "and" or "for" are in every description, so they do not count
  const related = squeeze(query).length < 4 ? [] : others(matches)
    .filter(s => query.split(' ').every(w => startsSomeWord(w, clean(s.description).split(' '))))
    .map(skill => ({ skill, rank: RANK.related, related: true }))

  return [...matches, ...related].sort(byRankThenName)
}

// The whole name or an alias was typed, so there is nothing left to choose between
export const isExactMatch = (match) => match?.rank < RANK.start
