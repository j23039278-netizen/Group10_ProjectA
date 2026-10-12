// SEAGAS — API Client
// Connects React frontend to FastAPI backend
// Author: Tee Ren Hang (Frontend Developer)
 
import axios from 'axios';
 
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});
 
// Auto-attach JWT token to every request
API.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
 
// Auto-handle 401 (token expired).
// A failed login also returns 401 — skip the redirect there so the Login page can show its error.
API.interceptors.response.use(
  response => response,
  error => {
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);
 
// ── Auth ──────────────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return API.post('/auth/login', form);
  },
  register: (data) => API.post('/auth/register', data),
  me: () => API.get('/auth/me'),
};
 
// ── Students ──────────────────────────────────────────────────
export const studentAPI = {
  getProfile:      ()     => API.get('/students/profile'),
  createProfile:   (data) => API.post('/students/profile', data),
  updateProfile:   (data) => API.put('/students/profile', data),
  getSkills:       ()     => API.get('/students/skills'),
  addSkill:        (data) => API.post('/students/skills', data),
  removeSkill:     (id)   => API.delete(`/students/skills/${id}`),
  getSkillLibrary: (cat)  => API.get('/students/skills-library', { params: { category: cat } }),
  getProjects:     ()     => API.get('/students/projects'),
  addProject:      (data) => API.post('/students/projects', data),
  getCerts:        ()     => API.get('/students/certifications'),
  addCert:         (data) => API.post('/students/certifications', data),
};
 
// ── Jobs ──────────────────────────────────────────────────────
export const jobsAPI = {
  getRoles:    ()      => API.get('/jobs/roles'),
  getRoleSkills: (id)  => API.get(`/jobs/roles/${id}/skills`),
  submitJD:    (data)  => API.post('/jobs/descriptions', data),
  getMyJDs:    ()      => API.get('/jobs/descriptions'),
  getJD:       (id)    => API.get(`/jobs/descriptions/${id}`),
  analyseJD:   (id)    => API.post(`/jobs/descriptions/${id}/analyse`),
};
 
// ── Assessments ───────────────────────────────────────────────
export const assessAPI = {
  run:     (data) => API.post('/assessments/run', data),
  get:     (id)   => API.get(`/assessments/${id}`),
  history: ()     => API.get('/assessments/my/history'),
  getRecs: (id)   => API.get(`/assessments/${id}/recommendations`),
};
 
// ── Progress (FR-11: Development Tracking) ────────────────────
export const progressAPI = {
  // Get progress status for all resources in an assessment
  getAssessmentProgress: (assessmentId) =>
    API.get(`/progress/assessment/${assessmentId}`),
 
  // Mark a resource as started
  start: (resourceId, assessmentId) =>
    API.post(`/progress/${resourceId}/start`, null, {
      params: { assessment_id: assessmentId }
    }),
 
  // Mark a resource as completed
  complete: (resourceId) =>
    API.post(`/progress/${resourceId}/complete`, { status: 'completed', skill_added: false }),
 
  // Confirm skill was added to profile after completing
  markSkillAdded: (resourceId) =>
    API.patch(`/progress/${resourceId}/skill-added`),
 
  // Get all progress records for this student
  getMy: (status = null) =>
    API.get('/progress/my', { params: status ? { status } : {} }),
 
  // Get summary counts (for dashboard)
  getSummary: () =>
    API.get('/progress/my/summary'),
};
 
// ── Advisor ───────────────────────────────────────────────────
export const advisorAPI = {
  overview:  ()    => API.get('/advisor/cohort/overview'),
  skillGaps: ()    => API.get('/advisor/cohort/skill-gaps'),
  students:  ()    => API.get('/advisor/students'),
  getStudent:(id)  => API.get(`/advisor/students/${id}`),
  progress:  ()    => API.get('/advisor/cohort/progress'),
};