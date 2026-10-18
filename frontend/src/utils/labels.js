// SEAGAS — Display text for values stored in lowercase / code form.
// 'personal' -> 'Personal', 'in_progress' -> 'In progress', 'AI_Digital' -> 'AI / Digital'.
// Use it for <option> text too: CSS text-transform does not reach an opened dropdown list.
export const label = (v) => {
  if (!v) return ''
  if (v === 'AI_Digital') return 'AI / Digital'
  const s = String(v).replace(/_/g, ' ')
  return s.charAt(0).toUpperCase() + s.slice(1)
}
