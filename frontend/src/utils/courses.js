// SEAGAS — The three courses a student can belong to (users.course in the database)
export const COURSES = [
  { id: 'CS',       label: 'Computer Science' },
  { id: 'BUSINESS', label: 'Business' },
  { id: 'ICT',      label: 'ICT' },
]

export const courseLabel = (id) => COURSES.find(c => c.id === id)?.label || '—'
