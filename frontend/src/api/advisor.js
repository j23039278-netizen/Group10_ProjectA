// SEAGAS — Advisor API calls. Only the advisor portal imports this file,
// so it is not part of the bundle students download.
import { API } from './client';

// Query parameters without the empty ones
const params = (obj) => ({ params: Object.fromEntries(Object.entries(obj).filter(([, v]) => v)) });

// ── Advisor ───────────────────────────────────────────────────
export const advisorAPI = {
  // course: 'CS' | 'BUSINESS' | 'ICT', or empty for all of the advisor's courses
  overview:  (course)         => API.get('/advisor/cohort/overview',   params({ course })),
  // Optional filters: assessed job role, programme (major), skill category ('Soft' = soft skills)
  skillGaps: (course, roleId, programme, category) =>
    API.get('/advisor/cohort/skill-gaps', params({ course, role_id: roleId, programme, category })),
  // Strong / Developing / Gap share per skill category, same filters (no category)
  skillCategories: (course, roleId, programme) =>
    API.get('/advisor/cohort/skill-categories', params({ course, role_id: roleId, programme })),
  progress:  (course)         => API.get('/advisor/cohort/progress',   params({ course })),
  students:  ()               => API.get('/advisor/students'),
  getStudent:(id)             => API.get(`/advisor/students/${id}`),
  downloadCv:(id)             => API.get(`/advisor/students/${id}/cv`, { responseType: 'blob' }),

  // Notes on a student (never shown to the student); ai_review = agree / disagree with an AI result
  notes:      (id)           => API.get(`/advisor/students/${id}/notes`),
  addNote:    (id, note)     => API.post(`/advisor/students/${id}/notes`, note),
  updateNote: (noteId, data) => API.patch(`/advisor/notes/${noteId}`, data),
  deleteNote: (noteId)       => API.delete(`/advisor/notes/${noteId}`),
};
