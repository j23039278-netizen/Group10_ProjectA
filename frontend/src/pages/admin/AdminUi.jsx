// SEAGAS — Shared building blocks for the admin pages
import { C, card } from './adminStyles'

export function Modal({ title, onClose, children, width = '440px' }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,20,35,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }}>
      <div role="dialog" aria-modal="true" aria-label={title} onClick={e => e.stopPropagation()}
        style={{ ...card, width: '100%', maxWidth: width, maxHeight: 'calc(100vh - 32px)', overflowY: 'auto', padding: '24px', boxShadow: '0 20px 50px rgba(0,0,0,0.2)', boxSizing: 'border-box' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ fontSize: '17px', fontWeight: '700', color: C.ink }}>{title}</div>
          <button onClick={onClose} aria-label="Close" style={{ border: 'none', background: 'none', fontSize: '20px', color: C.muted, cursor: 'pointer' }}>×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Alert({ type = 'error', children }) {
  const ok = type === 'success'
  return (
    <div role={ok ? 'status' : 'alert'} style={{ padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px', background: ok ? '#dcfce7' : '#fee2e2', color: ok ? C.green : C.red }}>
      {children}
    </div>
  )
}

// "Active" / "Inactive" pill used in the library tables
export function StatusPill({ active }) {
  return (
    <span style={{ padding: '2px 8px', borderRadius: '999px', fontSize: '11px', fontWeight: '600',
      background: active ? '#dcfce7' : '#f1f5f9', color: active ? C.green : C.muted }}>
      {active ? 'Active' : 'Inactive'}
    </span>
  )
}

// Where a library entry comes from: the seed files or the Admin page
export function SourcePill({ source }) {
  const admin = source === 'admin'
  return (
    <span title={admin ? 'Added in the Admin page; editable here' : 'From the seed files (skills_library.csv); edit it there'}
      style={{ padding: '2px 8px', borderRadius: '999px', fontSize: '11px', fontWeight: '600',
        background: admin ? '#ede9fe' : '#f1f5f9', color: admin ? '#6d28d9' : '#475569' }}>
      {admin ? 'admin' : source || 'seed'}
    </span>
  )
}
