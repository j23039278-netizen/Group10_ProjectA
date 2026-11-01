// SEAGAS — Skills library, job roles and learning resources (routers/library.py).
// Admins manage every entry; advisors the entries of their own courses. Each list
// row has can_edit for the signed-in user. Only the staff portals import this file.
import { API } from './client';

export const libraryAPI = {
  skills:        ()           => API.get('/library/skills'),
  createSkill:   (data)       => API.post('/library/skills', data),
  updateSkill:   (id, data)   => API.patch(`/library/skills/${id}`, data),
  roles:         ()           => API.get('/library/roles'),
  roleSkills:    (id)         => API.get(`/library/roles/${id}/skills`),
  createRole:    (data)       => API.post('/library/roles', data),
  updateRole:    (id, data)   => API.patch(`/library/roles/${id}`, data),
  setRoleSkills: (id, skills) => API.put(`/library/roles/${id}/skills`, skills),
  resources:      ()          => API.get('/library/resources'),
  createResource: (data)      => API.post('/library/resources', data),
  updateResource: (id, data)  => API.patch(`/library/resources/${id}`, data),
};
