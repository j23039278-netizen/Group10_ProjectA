// SEAGAS — Admin API calls. Only the admin portal imports this file,
// so it is not part of the bundle students download.
import { API } from './client';

// ── Admin ─────────────────────────────────────────────────────
export const adminAPI = {
  // System settings (FR-16) and the mail server check
  settings:       ()       => API.get('/admin/settings'),
  saveSettings:   (values) => API.put('/admin/settings', { values }),
  testEmail:      (to)     => API.post('/admin/settings/test-email', { to }),
  stats:         ()           => API.get('/admin/stats'),
  users:         (params)     => API.get('/admin/users', { params }),
  createUser:    (data)       => API.post('/admin/users', data),
  updateUser:    (id, data)   => API.patch(`/admin/users/${id}`, data),
  // Next free 5-digit staff ID for an advisor position (courses repeated: ?courses=CS&courses=ICT)
  staffNumber:   (position, courses) =>
    API.get(`/admin/staff-number?position=${position}&${courses.map(c => `courses=${c}`).join('&')}`),
  resetPassword: (id, pw)     => API.post(`/admin/users/${id}/reset-password`, { password: pw }),
  // Skills, roles and learning resources: api/library.js (advisors manage them too)
  auditLog:      (params)     => API.get('/admin/audit-log', { params }),
};
