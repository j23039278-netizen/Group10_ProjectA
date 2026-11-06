// SEAGAS — Importance of a skill and what it is worth on the Job Readiness Score, as the
// pages word it. The numbers come from the API (recommendation/engine.py, backend/readiness.py).
const IMPORTANCE_ORDER = ['required', 'preferred', 'bonus']

// A missing importance counts as required, as it does in the score
export const importanceOf = (item) => (IMPORTANCE_ORDER.includes(item.importance) ? item.importance : 'required')

// Required first. The sort is stable, so skills of one tier keep their order.
export const sortByImportance = (items) =>
  [...items].sort((a, b) => IMPORTANCE_ORDER.indexOf(importanceOf(a)) - IMPORTANCE_ORDER.indexOf(importanceOf(b)))

const points = (n) => `+${n.toFixed(1)}`

// What completing a resource adds. Empty when the API sent no number (its fallback answer).
export const resourceGainText = (gain) => {
  if (typeof gain !== 'number') return ''
  return gain > 0 ? `${points(gain)} points` : 'No score change on its own'
}

// The most a skill can add, for the skill's header
export const upToText = (gain) => (gain > 0 ? `up to ${points(gain)}` : '')

// Hover text on the Skill Gap page: why the skill is in its group, then what it can add
export const skillHoverText = (match) => {
  const worth = match.expected_gain > 0 ? `Up to ${points(match.expected_gain)} points if this becomes Strong.` : ''
  return [match.reason, worth].filter(Boolean).join(' ') || undefined
}

// Sum of what the shown first steps add, as the card says it
export const firstStepsTotal = (steps) =>
  points(steps.reduce((sum, step) => sum + (step.resource.gain_if_completed || 0), 0))
