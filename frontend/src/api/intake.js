// SEAGAS — New student intake (advisor uploads a list; admin creates the accounts).
// Imported only by the advisor and admin portals.
import { API } from './client';

export const intakeAPI = {
  upload: (file) => {
    const form = new FormData();
    form.append('file', file);
    return API.post('/intake/batches', form);
  },
  template:       ()               => API.get('/intake/template', { responseType: 'blob' }),
  batches:        ()               => API.get('/intake/batches'),
  batch:          (id)             => API.get(`/intake/batches/${id}`),
  // admin only
  assign:         (id)             => API.post(`/intake/batches/${id}/assign`),
  updateRow:      (rowId, data)    => API.patch(`/intake/rows/${rowId}`, data),
  createAccounts: (id, rowIds = null) => API.post(`/intake/batches/${id}/create-accounts`, { row_ids: rowIds }),
  reject:         (rowId, note)    => API.post(`/intake/rows/${rowId}/reject`, { note }),
  outbox:         ()               => API.get('/intake/outbox'),
};
