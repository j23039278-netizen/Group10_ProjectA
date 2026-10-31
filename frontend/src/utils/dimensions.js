// SEAGAS — The 7 dimensions of an assessment (assessments.score_* columns) and what a
// value means. A dimension can be:
//   score         a real result (0% included, when the student has information for it)
//   not_required  NULL: the job asks for no skill of this category, so there is nothing to score
//   no_data       0% because nothing is recorded yet (no projects, certifications or work
//                 experience; no skill of the category listed), not because the student was
//                 assessed as lacking it. The lecturer asked us to show these differently.
// Only the four skill dimensions are part of the readiness score (assessment_service.py).

export const DIMENSIONS = [
  { key: 'score_technical',     label: 'Technical Skills',    category: 'Technical',  noun: 'technical' },
  { key: 'score_ai_digital',    label: 'AI / Digital Skills', category: 'AI_Digital', noun: 'AI or digital' },
  { key: 'score_analytical',    label: 'Analytical Skills',   category: 'Analytical', noun: 'analytical' },
  { key: 'score_communication', label: 'Communication',       category: 'Soft',       noun: 'soft' },
  { key: 'score_project_exp',   label: 'Project Experience',  empty: 'No projects added yet' },
  { key: 'score_certification', label: 'Certification',       empty: 'No certifications added yet' },
  { key: 'score_industry_exp',  label: 'Industry Experience', empty: 'No internships or work experience added yet' },
]

// skills: the student's current skills (with category), to tell "no skill of this
// category listed" from a real 0%; leave it out when unknown.
export function dimensionState(dim, value, skills) {
  const v = value == null ? null : parseFloat(value)
  // Only the skill dimensions can be NULL; the experience ones are always worked out
  if (v == null) return { state: 'not_required', text: 'Not required', note: `This job asks for no ${dim.noun} skills` }
  if (v === 0 && dim.empty) return { state: 'no_data', text: 'No data yet', note: dim.empty }
  if (v === 0 && dim.category && skills && !skills.some(s => s.category === dim.category)) {
    return { state: 'no_data', text: 'No data yet', note: `No ${dim.noun} skills listed in the profile` }
  }
  return { state: 'score', value: v, text: `${v}%` }
}
