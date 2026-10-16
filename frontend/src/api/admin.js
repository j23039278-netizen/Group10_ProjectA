// SEAGAS — Admin API calls. Only the admin portal imports this file,
// so it is not part of the bundle students download.
import { API } from './client';

// ── Admin ─────────────────────────────────────────────────────
export const adminAPI = {
  stats:         ()           => API.get('/admin/stats'),
  users:         (params)     => API.get('/admin/users', { params }),
  createUser:    (data)       => API.post('/admin/users', data),
  updateUser:    (id, data)   => API.patch(`/admin/users/${id}`, data),
  resetPassword: (id, pw)     => API.post(`/admin/users/${id}/reset-password`, { password: pw }),
  skills:        ()           => API.get('/admin/skills'),
  createSkill:   (data)       => API.post('/admin/skills', data),
  updateSkill:   (id, data)   => API.patch(`/admin/skills/${id}`, data),
  roles:         ()           => API.get('/admin/roles'),
  roleSkills:    (id)         => API.get(`/admin/roles/${id}/skills`),
  createRole:    (data)       => API.post('/admin/roles', data),
  updateRole:    (id, data)   => API.patch(`/admin/roles/${id}`, data),
  setRoleSkills: (id, skills) => API.put(`/admin/roles/${id}/skills`, skills),
  auditLog:      (params)     => API.get('/admin/audit-log', { params }),
};
