// SEAGAS — Admin: User Management
// Admins create advisor/admin accounts, activate or deactivate accounts and reset passwords.
// Students are not created here: they register themselves on the Register page.
import { useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/client'
import { adminAPI } from '../api/admin'

const PAGE_SIZE = 50
const PASSWORD_MIN = 8
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const C = {
  ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
  blue: '#2d5be3', green: '#16a34a', red: '#dc2626', amber: '#d97706',
}

const card  = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px' }
const th    = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: `1px solid ${C.line}` }
const td    = { padding: '11px 12px', fontSize: '13px', color: C.body, borderBottom: '1px solid #f0f1f5' }
const input = { width: '100%', padding: '9px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', outline: 'none', boxSizing: 'border-box', color: C.ink, background: '#fff' }
const label = { display: 'block', fontSize: '12px', fontWeight: '600', color: C.body, marginBottom: '6px' }

const btn = (variant = 'primary') => ({
  padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer',
  border: variant === 'primary' ? 'none' : `1px solid ${C.line}`,
  background: variant === 'primary' ? C.blue : '#fff',
  color: variant === 'primary' ? '#fff' : variant === 'danger' ? C.red : C.body,
})

const ROLE_BADGE = {
  admin:   { bg: '#ede9fe', color: '#6d28d9' },
  advisor: { bg: '#dbeafe', color: '#1d4ed8' },
  student: { bg: '#f1f5f9', color: '#475569' },
}

function errorText(err, fallback) {
  if (!err.response) return 'Cannot reach the server. Please make sure the backend is running.'
  const d = err.response.data?.detail
  if (Array.isArray(d)) return 'Please check the details. The email address may be invalid.'
  return typeof d === 'string' ? d : fallback
}

function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,20,35,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }}>
      <div role="dialog" aria-modal="true" aria-label={title} onClick={e => e.stopPropagation()}
        style={{ ...card, width: '100%', maxWidth: '440px', padding: '24px', boxShadow: '0 20px 50px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ fontSize: '17px', fontWeight: '700', color: C.ink }}>{title}</div>
          <button onClick={onClose} aria-label="Close" style={{ border: 'none', background: 'none', fontSize: '20px', color: C.muted, cursor: 'pointer' }}>×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Alert({ type = 'error', children }) {
  const ok = type === 'success'
  return (
    <div role={ok ? 'status' : 'alert'} style={{ padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px', background: ok ? '#dcfce7' : '#fee2e2', color: ok ? C.green : C.red }}>
      {children}
    </div>
  )
}

function AddUserModal({ onClose, onCreated }) {
  const [form, setForm]       = useState({ full_name: '', email: '', role: 'advisor', password: '', confirm: '' })
  const [error, setError]     = useState('')
  const [saving, setSaving]   = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.full_name.trim())            return setError('Please enter the full name.')
    if (!EMAIL_RE.test(form.email.trim())) return setError('Please enter a valid email address.')
    if (form.password.length < PASSWORD_MIN) return setError(`Password must be at least ${PASSWORD_MIN} characters.`)
    if (form.password !== form.confirm)    return setError('Passwords do not match.')
    setSaving(true)
    setError('')
    try {
      const res = await adminAPI.createUser({
        full_name: form.full_name.trim(), email: form.email.trim(), role: form.role, password: form.password,
      })
      onCreated(res.data)
    } catch (err) {
      setError(errorText(err, 'Could not create the account.'))
      setSaving(false)
    }
  }

  return (
    <Modal title="Add user" onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {error && <Alert>{error}</Alert>}
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-role">Role</label>
          <select id="nu-role" style={input} value={form.role} onChange={set('role')}>
            <option value="advisor">Advisor</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-name">Full name</label>
          <input id="nu-name" style={input} value={form.full_name} onChange={set('full_name')} placeholder="e.g. Dr. Lim Mei Ling" autoFocus />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-email">Email</label>
          <input id="nu-email" type="email" style={input} value={form.email} onChange={set('email')} placeholder="name@uni.edu.my" autoComplete="off" />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-pw">Temporary password</label>
          <input id="nu-pw" type="password" style={input} value={form.password} onChange={set('password')} placeholder={`At least ${PASSWORD_MIN} characters`} autoComplete="new-password" />
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="nu-confirm">Confirm password</label>
          <input id="nu-confirm" type="password" style={input} value={form.confirm} onChange={set('confirm')} autoComplete="new-password" />
        </div>
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '18px' }}>
          Share the password with the user privately. They sign in on the normal SEAGAS login page and are taken to the {form.role} pages.
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Creating…' : 'Create account'}</button>
        </div>
      </form>
    </Modal>
  )
}

function ResetPasswordModal({ user, onClose, onDone }) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [saving, setSaving]     = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (password.length < PASSWORD_MIN) return setError(`Password must be at least ${PASSWORD_MIN} characters.`)
    if (password !== confirm)           return setError('Passwords do not match.')
    setSaving(true)
    setError('')
    try {
      await adminAPI.resetPassword(user.user_id, password)
      onDone()
    } catch (err) {
      setError(errorText(err, 'Could not reset the password.'))
      setSaving(false)
    }
  }

  return (
    <Modal title="Reset password" onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div style={{ fontSize: '13px', color: C.body, marginBottom: '14px' }}>
          New password for <b style={{ color: C.ink }}>{user.full_name}</b> ({user.email})
        </div>
        {error && <Alert>{error}</Alert>}
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="rp-pw">New password</label>
          <input id="rp-pw" type="password" style={input} value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" autoFocus />
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="rp-confirm">Confirm password</label>
          <input id="rp-confirm" type="password" style={input} value={confirm} onChange={e => setConfirm(e.target.value)} autoComplete="new-password" />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Saving…' : 'Set password'}</button>
        </div>
      </form>
    </Modal>
  )
}

export default function AdminUsers() {
  const [stats, setStats]       = useState(null)
  const [users, setUsers]       = useState([])
  const [total, setTotal]       = useState(0)
  const [search, setSearch]     = useState('')
  const [query, setQuery]       = useState('')
  const [roleFilter, setRole]   = useState('')
  const [page, setPage]         = useState(0)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [notice, setNotice]     = useState('')
  const [adding, setAdding]     = useState(false)
  const [resetting, setResetting] = useState(null)
  const [busyId, setBusyId]     = useState(null)

  const [meId, setMeId]         = useState(null)

  const loadStats = () => adminAPI.stats().then(r => setStats(r.data)).catch(() => {})

  const loadUsers = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminAPI.users({
        search: query || undefined, role: roleFilter || undefined,
        limit: PAGE_SIZE, offset: page * PAGE_SIZE,
      })
      setUsers(res.data.users)
      setTotal(res.data.total)
      setError('')
    } catch (err) {
      setError(errorText(err, 'Could not load users.'))
    } finally {
      setLoading(false)
    }
  }, [query, roleFilter, page])

  useEffect(() => {
    loadStats()
    authAPI.me().then(r => setMeId(r.data.user_id)).catch(() => {})
  }, [])
  useEffect(() => { loadUsers() }, [loadUsers])

  // Search after the admin stops typing
  useEffect(() => {
    const t = setTimeout(() => { setPage(0); setQuery(search.trim()) }, 300)
    return () => clearTimeout(t)
  }, [search])

  const toggleActive = async (u) => {
    setBusyId(u.user_id)
    setNotice('')
    try {
      const res = await adminAPI.updateUser(u.user_id, { is_active: !u.is_active })
      setUsers(list => list.map(x => x.user_id === u.user_id ? res.data : x))
      setNotice(`${u.full_name} is now ${res.data.is_active ? 'active and can sign in' : 'deactivated and can no longer sign in'}.`)
      loadStats()
    } catch (err) {
      setError(errorText(err, 'Could not update the account.'))
    } finally {
      setBusyId(null)
    }
  }

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const statCards = [
    { label: 'Students', value: stats?.student, color: C.ink },
    { label: 'Advisors', value: stats?.advisor, color: C.blue },
    { label: 'Admins',   value: stats?.admin,   color: '#6d28d9' },
  ]

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>User Management</div>
          <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
            Create advisor and admin accounts. Students register themselves.
          </div>
        </div>
        <button style={btn('primary')} onClick={() => { setNotice(''); setAdding(true) }}>+ Add user</button>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {statCards.map(s => (
          <div key={s.label} style={{ ...card, padding: '20px' }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: s.color, margin: '4px 0', lineHeight: 1 }}>
              {s.value ? s.value.total : '—'}
            </div>
            {s.value && s.value.total !== s.value.active && (
              <div style={{ fontSize: '12px', color: C.muted }}>{s.value.total - s.value.active} deactivated</div>
            )}
          </div>
        ))}
      </div>

      {/* Table */}
      <div style={{ ...card, padding: '20px 24px' }}>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
          <input
            type="search" aria-label="Search users" placeholder="Search by name or email"
            style={{ ...input, flex: '1 1 240px', width: 'auto' }}
            value={search} onChange={e => setSearch(e.target.value)}
          />
          <select aria-label="Filter by role" style={{ ...input, flex: '0 0 160px', width: 'auto' }}
            value={roleFilter} onChange={e => { setPage(0); setRole(e.target.value) }}>
            <option value="">All roles</option>
            <option value="admin">Admins</option>
            <option value="advisor">Advisors</option>
            <option value="student">Students</option>
          </select>
        </div>

        {notice && <Alert type="success">{notice}</Alert>}
        {error && <Alert>{error}</Alert>}

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
            <thead>
              <tr>{['Name', 'Email', 'Role', 'Status', 'Created', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>Loading…</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={6} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No users match.</td></tr>
              ) : users.map(u => {
                const badge = ROLE_BADGE[u.role] || ROLE_BADGE.student
                const isMe  = u.user_id === meId
                return (
                  <tr key={u.user_id} style={{ opacity: u.is_active ? 1 : 0.6 }}>
                    <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{u.full_name}{isMe && <span style={{ color: C.muted, fontWeight: '500' }}> (you)</span>}</td>
                    <td style={td}>{u.email}</td>
                    <td style={td}>
                      <span style={{ padding: '3px 9px', borderRadius: '999px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize', background: badge.bg, color: badge.color }}>{u.role}</span>
                    </td>
                    <td style={{ ...td, color: u.is_active ? C.green : C.red, fontWeight: '600' }}>{u.is_active ? 'Active' : 'Deactivated'}</td>
                    <td style={td}>{u.created_at ? new Date(u.created_at).toLocaleDateString('en-GB') : '—'}</td>
                    <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button style={{ ...btn('secondary'), padding: '6px 10px', fontSize: '12px', marginRight: '6px' }}
                        onClick={() => { setNotice(''); setResetting(u) }}>Reset password</button>
                      {!isMe && (
                        <button style={{ ...btn(u.is_active ? 'danger' : 'secondary'), padding: '6px 10px', fontSize: '12px' }}
                          disabled={busyId === u.user_id} onClick={() => toggleActive(u)}>
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', fontSize: '12px', color: C.muted, flexWrap: 'wrap', gap: '8px' }}>
          <span>{total} account{total === 1 ? '' : 's'}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button style={{ ...btn('secondary'), padding: '5px 10px', fontSize: '12px' }} disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Prev</button>
            <span>Page {page + 1} of {pages}</span>
            <button style={{ ...btn('secondary'), padding: '5px 10px', fontSize: '12px' }} disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        </div>
      </div>

      {adding && (
        <AddUserModal
          onClose={() => setAdding(false)}
          onCreated={(u) => {
            setAdding(false)
            setNotice(`${u.full_name} (${u.role}) can now sign in with ${u.email}.`)
            loadStats()
            loadUsers()
          }}
        />
      )}
      {resetting && (
        <ResetPasswordModal
          user={resetting}
          onClose={() => setResetting(null)}
          onDone={() => { setNotice(`Password updated for ${resetting.full_name}.`); setResetting(null) }}
        />
      )}
    </div>
  )
}
