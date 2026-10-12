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
  roles:         ()           => API.get('/admin/roles'),
};
