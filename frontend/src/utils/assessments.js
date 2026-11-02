// SEAGAS — How an assessment is named on the student pages (rows of /assessments/my/history).
// A pasted job description has no role: it goes by its title or the start of its text.
const snippet = (text) => {
  const t = (text || '').replace(/\s+/g, ' ').trim()
  return t.length > 45 ? `${t.slice(0, 45)}…` : t
}

export const assessmentName = (h) =>
  h.role_name || h.jd_title || snippet(h.jd_text) || 'Pasted job description'

export const assessmentDate = (h) =>
  new Date(h.created_at).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '')

// One line for a drop-down list
export const assessmentLabel = (h) =>
  `${assessmentName(h)}${h.role_id ? '' : ' (pasted JD)'} — ${h.readiness_score}% — ${assessmentDate(h)} — ${cap(h.matching_method)} — ` +
  `${h.strong_count} strong, ${h.developing_count} developing, ${h.gap_count} gaps`
