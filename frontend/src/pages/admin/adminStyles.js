// SEAGAS — Shared styles and helpers for the admin pages
export const C = {
  ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
  blue: '#2d5be3', green: '#16a34a', red: '#dc2626', amber: '#d97706',
}

export const card  = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px' }
export const th    = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: `1px solid ${C.line}`, background: '#fff', whiteSpace: 'nowrap' }
export const td    = { padding: '11px 12px', fontSize: '13px', color: C.body, borderBottom: '1px solid #f0f1f5', verticalAlign: 'top' }
// IDs, emails and phone numbers stay on one line; the table scrolls sideways instead
export const tdOne = { ...td, whiteSpace: 'nowrap' }
export const input = { width: '100%', padding: '9px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', outline: 'none', boxSizing: 'border-box', color: C.ink, background: '#fff' }
export const label = { display: 'block', fontSize: '12px', fontWeight: '600', color: C.body, marginBottom: '6px' }
export const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, textTransform: 'uppercase', letterSpacing: '0.5px' }

export const btn = (variant = 'primary') => ({
  padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer',
  border: variant === 'primary' ? 'none' : `1px solid ${C.line}`,
  background: variant === 'primary' ? C.blue : '#fff',
  color: variant === 'primary' ? '#fff' : variant === 'danger' ? C.red : C.body,
})
export const smallBtn = (variant = 'secondary') => ({ ...btn(variant), padding: '5px 10px', fontSize: '12px' })

export function errorText(err, fallback) {
  if (!err.response) return 'Cannot reach the server. Please make sure the backend is running.'
  const d = err.response.data?.detail
  if (Array.isArray(d)) return 'Please check the details: ' + d.map(x => x.msg).join('; ')
  return typeof d === 'string' ? d : fallback
}
