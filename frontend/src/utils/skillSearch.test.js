// Run with `npm test` in frontend/ (Node's own test runner, no extra packages)
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { isExactMatch, searchSkills } from './skillSearch.js'

const skill = (skill_name, aliases = [], description = '') => ({ skill_id: skill_name, skill_name, aliases, description })
const LIBRARY = [
  skill('Python', ['Python 3'], 'General-purpose programming language.'),
  skill('PyTorch', [], 'Deep learning framework.'),
  skill('Pandas', ['Python Pandas'], 'Data analysis library.'),
  skill('JavaScript', ['JS', 'ES6']),
  skill('Node.js', [], 'JavaScript runtime.'),
  skill('SQL', ['Relational databases']),
  skill('MySQL'),
  skill('Digital Marketing'),
  skill('Git', ['GitHub']),
  skill('REST API'),
  skill('React', ['React.js']),
  skill('Power BI', ['PowerBI']),
  skill('Machine Learning', ['ML']),
  skill('Data Visualisation', ['Data viz']),
  skill('Tableau', [], 'Dashboard and reporting tool.'),
  skill('C++'),
  skill('No aliases', null),
]
const names = (query) => searchSkills(LIBRARY, query).map(m => m.skill.skill_name)

test('an empty query keeps the whole list in its own order', () => {
  const all = LIBRARY.map(s => s.skill_name)
  assert.deepEqual(names(''), all)
  assert.deepEqual(names('   '), all)
})

test('the exact name comes first, then names that start with the query', () => {
  assert.deepEqual(names('python').slice(0, 2), ['Python', 'Pandas'])
  assert.deepEqual(names('py').slice(0, 2), ['Python', 'PyTorch'])
})

test('case, spaces and punctuation do not matter', () => {
  for (const query of ['POWER BI', 'powerbi', 'power-bi']) assert.equal(names(query)[0], 'Power BI')
  assert.equal(names('nodejs')[0], 'Node.js')
  assert.equal(names('c++')[0], 'C++')
})

test('words can come in any order', () => {
  assert.deepEqual(names('learning machine'), ['Machine Learning'])
})

test('an alias finds its skill and says which alias matched', () => {
  const [match] = searchSkills(LIBRARY, 'js')
  assert.equal(match.skill.skill_name, 'JavaScript')
  assert.equal(match.alias, 'JS')
})

test('the same kind of match on a name ranks above one on an alias', () => {
  assert.deepEqual(names('git'), ['Git'])
  assert.deepEqual(names('github'), ['Git'])
  assert.deepEqual(names('rel').slice(0, 1), ['SQL'])
})

test('three letters inside a word must end it', () => {
  assert.ok(names('sql').includes('MySQL'))
  assert.ok(!names('git').includes('Digital Marketing'))
})

test('typos still find the skill', () => {
  assert.equal(names('pyhton')[0], 'Python')
  assert.equal(names('phyton')[0], 'Python')
  assert.equal(names('recat')[0], 'React')
  assert.equal(names('rect')[0], 'React')
  assert.equal(names('slq')[0], 'SQL')
  assert.equal(names('powrbi')[0], 'Power BI')
  assert.equal(names('machin lerning')[0], 'Machine Learning')
  assert.equal(names('data visualization')[0], 'Data Visualisation')
})

test('a typo in a word still being typed finds the skill', () => {
  assert.deepEqual(names('pyht').slice(0, 2), ['Python', 'PyTorch'])
})

test('close spellings do not appear beside a direct match', () => {
  assert.deepEqual(names('react'), ['React'])
  assert.deepEqual(names('rest'), ['REST API'])
})

test('a different first letter is not treated as a typo', () => {
  assert.ok(!names('test').includes('REST API'))
})

test('short queries are not treated as typos', () => {
  assert.deepEqual(names('ab'), [])
})

test('description words find related skills after direct matches, marked as related', () => {
  const [match] = searchSkills(LIBRARY, 'dashboard')
  assert.equal(match.skill.skill_name, 'Tableau')
  assert.equal(match.related, true)
  const javascript = searchSkills(LIBRARY, 'javascript')
  assert.deepEqual(javascript.map(m => m.skill.skill_name), ['JavaScript', 'Node.js'])
  assert.equal(javascript[1].related, true)
})

test('short words do not match descriptions', () => {
  assert.deepEqual(names('and'), [])
})

test('nothing close gives no results', () => {
  assert.deepEqual(names('xyzzy'), [])
  assert.deepEqual(names('数据'), [])
})

test('a missing aliases list or description is fine', () => {
  assert.deepEqual(names('no aliases'), ['No aliases'])
  const plain = { skill_id: '1', skill_name: 'Plain' }
  assert.deepEqual(searchSkills([plain], 'plainly').map(m => m.skill), [plain])
})

test('isExactMatch is true only for a whole name or alias', () => {
  const first = (query) => searchSkills(LIBRARY, query)[0]
  assert.equal(isExactMatch(first('python')), true)
  assert.equal(isExactMatch(first('JS')), true)
  assert.equal(isExactMatch(first('pyth')), false)
  assert.equal(isExactMatch(first('pyhton')), false)
  assert.equal(isExactMatch(first('')), false)
  assert.equal(isExactMatch(undefined), false)
})
