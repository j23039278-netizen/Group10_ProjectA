// SEAGAS — Work experience types and the period text, shared by the student and advisor pages
export const EXPERIENCE_TYPES = [
  { id: 'internship', label: 'Internship' },
  { id: 'part_time',  label: 'Part-time job' },
  { id: 'full_time',  label: 'Full-time job' },
  { id: 'freelance',  label: 'Freelance' },
  { id: 'volunteer',  label: 'Volunteer' },
]
export const experienceTypeLabel = (id) => EXPERIENCE_TYPES.find(t => t.id === id)?.label || id
const fmtMonth = (d) => d ? new Date(d).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' }) : ''

// "Jan 2026 – Apr 2026 · 3 months" or "Jun 2025 – Present · 1 yr 5 months"
export function period(start, end) {
  const a = new Date(start), b = end ? new Date(end) : new Date()
  const months = Math.max(1, (b.getFullYear() - a.getFullYear()) * 12 + b.getMonth() - a.getMonth() + (b.getDate() >= a.getDate() ? 1 : 0))
  const y = Math.floor(months / 12), m = months % 12
  const length = [y && `${y} yr${y > 1 ? 's' : ''}`, m && `${m} month${m > 1 ? 's' : ''}`].filter(Boolean).join(' ')
  return `${fmtMonth(start)} – ${end ? fmtMonth(end) : 'Present'} · ${length}`
}
