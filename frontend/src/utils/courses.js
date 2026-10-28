// SEAGAS — The three courses a student can belong to (users.course in the database)
// Computing courses first (same office), then Business
export const COURSES = [
  { id: 'CS',       label: 'Computer Science' },
  { id: 'ICT',      label: 'Information and Communications Technology' },
  { id: 'BUSINESS', label: 'Business' },
]

export const courseLabel = (id) => COURSES.find(c => c.id === id)?.label || '—'

// A list of course codes as text; every course -> "All courses"
export const coursesText = (ids) =>
  !ids?.length ? '—' : ids.length === COURSES.length ? 'All courses'
    : COURSES.filter(c => ids.includes(c.id)).map(c => c.label).join(', ')

// Advisor positions (users.advisor_position + advisor_courses). The staff ID starts with
// the prefix; must match STAFF_PREFIX in backend/advisor_scope.py.
export const ADVISOR_POSITIONS = [
  { id: 'dean-computing', label: 'Dean, Computing (Computer Science and Information and Communications Technology)', position: 'dean', courses: ['CS', 'ICT'], prefix: '10' },
  { id: 'hop-cs',         label: 'Head of Programme, Computer Science', position: 'hop',  courses: ['CS'],        prefix: '11' },
  { id: 'hop-ict',        label: 'Head of Programme, Information and Communications Technology', position: 'hop',  courses: ['ICT'],       prefix: '12' },
  { id: 'dean-business',  label: 'Dean, Business',                      position: 'dean', courses: ['BUSINESS'],  prefix: '20' },
  { id: 'hop-business',   label: 'Head of Programme, Business',         position: 'hop',  courses: ['BUSINESS'],  prefix: '21' },
]

export const advisorPositionOf = (position, courses) =>
  ADVISOR_POSITIONS.find(p => p.position === position &&
    [...p.courses].sort().join() === [...(courses || [])].sort().join())
