// SEAGAS — The 7 dimensions of an assessment (assessments.score_* columns) and what a
// value means. A dimension can be:
//   score         a real result (0% included, when the student has information for it)
//   not_required  NULL: the job asks for no skill of this category, so there is nothing to score
//   no_data       0% because no skill of the category is listed, not because the student was
//                 assessed as lacking it. The lecturer asked us to show these differently.
// Only the four skill dimensions are part of the readiness score (assessment_service.py).
// The experience dimensions (records) show the student's records, not a percentage.

export const DIMENSIONS = [
  { key: 'score_technical',     label: 'Technical Skills',    category: 'Technical',  noun: 'technical' },
  { key: 'score_ai_digital',    label: 'AI / Digital Skills', category: 'AI_Digital', noun: 'AI or digital' },
  { key: 'score_analytical',    label: 'Analytical Skills',   category: 'Analytical', noun: 'analytical' },
  { key: 'score_communication', label: 'Communication',       category: 'Soft',       noun: 'soft' },
  { key: 'score_project_exp',   label: 'Project Experience',  records: 'projects',  empty: 'No projects added yet' },
  { key: 'score_certification', label: 'Certification',       records: 'certs',     empty: 'No certifications added yet' },
  { key: 'score_industry_exp',  label: 'Industry Experience', records: 'industry',  empty: 'No internships or work experience added yet' },
]

// One line per record behind an experience dimension.
// records: { projects, certifications, experiences } of the student
export function dimensionRecords(dim, records) {
  const { projects = [], certifications = [], experiences = [] } = records || {}
  const project = (p) => [p.project_title, p.year_completed].filter(Boolean).join(', ')
  if (dim.records === 'projects') return projects.map(project)
  if (dim.records === 'certs') return certifications.map(c => [c.cert_name, c.issuer].filter(Boolean).join(', '))
  // Same as the score: internship projects and work experience other than volunteering
  return [
    ...experiences.filter(x => x.experience_type !== 'volunteer').map(x => `${x.job_title}, ${x.company}`),
    ...projects.filter(p => p.project_type === 'internship').map(project),
  ]
}

// skills: the student's current skills (with category), to tell "no skill of this
// category listed" from a real 0%; leave it out when unknown.
export function dimensionState(dim, value, skills) {
  const v = value == null ? null : parseFloat(value)
  // Only the skill dimensions can be NULL; the experience ones are always worked out
  if (v == null) return { state: 'not_required', text: 'Not required', note: `This job asks for no ${dim.noun} skills` }
  if (v === 0 && dim.category && skills && !skills.some(s => s.category === dim.category)) {
    return { state: 'no_data', text: 'No data yet', note: `No ${dim.noun} skills listed in the profile` }
  }
  return { state: 'score', value: v, text: `${v}%` }
}
