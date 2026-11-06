// Run with `npm test` in frontend/ (Node's own test runner, no extra packages)
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { firstStepsTotal, importanceOf, resourceGainText, skillHoverText, sortByImportance, upToText } from './importance.js'

test('a missing or unknown importance counts as required', () => {
  assert.equal(importanceOf({}), 'required')
  assert.equal(importanceOf({ importance: null }), 'required')
  assert.equal(importanceOf({ importance: 'bonus' }), 'bonus')
})

test('required comes first and each tier keeps its order', () => {
  const items = [
    { n: 'a', importance: 'bonus' }, { n: 'b', importance: 'required' }, { n: 'c', importance: 'preferred' },
    { n: 'd', importance: 'required' }, { n: 'e' },
  ]
  assert.deepEqual(sortByImportance(items).map(i => i.n), ['b', 'd', 'e', 'c', 'a'])
  assert.equal(items[0].n, 'a')   // the input is not changed
})

test('resource gain text', () => {
  assert.equal(resourceGainText(3.5), '+3.5 points')
  assert.equal(resourceGainText(7), '+7.0 points')
  assert.equal(resourceGainText(0), 'No score change on its own')
  assert.equal(resourceGainText(undefined), '')
})

test('up to text', () => {
  assert.equal(upToText(5.8), 'up to +5.8')
  assert.equal(upToText(0), '')
  assert.equal(upToText(undefined), '')
})

test('hover text adds the gain to the reason, not on Strong skills', () => {
  assert.equal(skillHoverText({ reason: 'No match.', expected_gain: 7 }), 'No match. Up to +7.0 points if this becomes Strong.')
  assert.equal(skillHoverText({ expected_gain: 3.5 }), 'Up to +3.5 points if this becomes Strong.')
  assert.equal(skillHoverText({ reason: 'You list SQL.', expected_gain: 0 }), 'You list SQL.')
  assert.equal(skillHoverText({}), undefined)
})

test('first steps total', () => {
  const step = (gain) => ({ resource: { gain_if_completed: gain } })
  assert.equal(firstStepsTotal([step(5.8), step(5.8), step(4.9)]), '+16.5')
  assert.equal(firstStepsTotal([step(0.1), step(0.2)]), '+0.3')
})
