// SEAGAS — Advisor API calls. Only the advisor portal imports this file,
// so it is not part of the bundle students download.
import { API } from './client';

// ── Advisor ───────────────────────────────────────────────────
export const advisorAPI = {
  // course: 'CS' | 'BUSINESS' | 'ICT', or empty for every student
  overview:  (course) => API.get('/advisor/cohort/overview',   { params: course ? { course } : {} }),
  skillGaps: (course) => API.get('/advisor/cohort/skill-gaps', { params: course ? { course } : {} }),
  students:  ()    => API.get('/advisor/students'),
  getStudent:(id)  => API.get(`/advisor/students/${id}`),
  progress:  ()    => API.get('/advisor/cohort/progress'),
};
