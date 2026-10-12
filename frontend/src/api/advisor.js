// SEAGAS — Advisor API calls. Only the advisor portal imports this file,
// so it is not part of the bundle students download.
import { API } from './client';

// ── Advisor ───────────────────────────────────────────────────
export const advisorAPI = {
  overview:  ()    => API.get('/advisor/cohort/overview'),
  skillGaps: ()    => API.get('/advisor/cohort/skill-gaps'),
  students:  ()    => API.get('/advisor/students'),
  getStudent:(id)  => API.get(`/advisor/students/${id}`),
  progress:  ()    => API.get('/advisor/cohort/progress'),
};
