// SEAGAS — New student intake (advisors do it; admins can only look).
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
  // advisors only
  updateRow:      (rowId, data)    => API.patch(`/intake/rows/${rowId}`, data),
  createAccounts: (id, rowIds = null) => API.post(`/intake/batches/${id}/create-accounts`, { row_ids: rowIds }),
  reject:         (rowId, note)    => API.post(`/intake/rows/${rowId}/reject`, { note }),
  // advisors and admins; resend where the row's can_resend says so
  outbox:         ()               => API.get('/intake/outbox'),
  resend:         (emailId)        => API.post(`/intake/outbox/${emailId}/resend`),
};
