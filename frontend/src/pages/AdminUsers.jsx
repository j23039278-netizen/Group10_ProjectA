// SEAGAS — Admin: User Management
// Admins create advisor/admin accounts, rename, activate or deactivate accounts and reset passwords.
// Students are not created here: their accounts come from the new-student lists (Student Intake).
import { useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/client'
import { adminAPI } from '../api/admin'
import { passwordProblem } from '../utils/passwordRules'
import { C, card, th, td, input, label, btn, errorText } from './admin/adminStyles'
import { Modal, Alert } from './admin/AdminUi'

const PAGE_SIZE = 50
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// Must match ROLE_EMAIL_DOMAINS in backend/routers/auth.py
const EMAIL_DOMAINS = { advisor: 'advisor.newinti.edu.my', admin: 'admin.newinti.edu.my' }

const ROLE_BADGE = {
  admin:   { bg: '#ede9fe', color: '#6d28d9' },
  advisor: { bg: '#dbeafe', color: '#1d4ed8' },
  student: { bg: '#f1f5f9', color: '#475569' },
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
    if (!form.email.trim().toLowerCase().endsWith(`@${EMAIL_DOMAINS[form.role]}`))
      return setError(`${form.role === 'admin' ? 'Admin' : 'Advisor'} emails must end with @${EMAIL_DOMAINS[form.role]}.`)
    if (passwordProblem(form.password)) return setError(passwordProblem(form.password))
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
          <input id="nu-email" type="email" style={input} value={form.email} onChange={set('email')} placeholder={`name@${EMAIL_DOMAINS[form.role]}`} autoComplete="off" />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-pw">Temporary password</label>
          <input id="nu-pw" type="password" style={input} value={form.password} onChange={set('password')} placeholder="8+ characters: A-Z, a-z, 0-9 and a symbol" autoComplete="new-password" />
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="nu-confirm">Confirm password</label>
          <input id="nu-confirm" type="password" style={input} value={form.confirm} onChange={set('confirm')} autoComplete="new-password" />
        </div>
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '18px' }}>
          Share the password with the user privately. It is temporary: at their first sign-in they must choose their own password.
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Creating…' : 'Create account'}</button>
        </div>
      </form>
    </Modal>
  )
}

function EditUserModal({ user, onClose, onSaved }) {
  const [name, setName]     = useState(user.full_name)
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return setError('Please enter the full name.')
    setSaving(true)
    setError('')
    try {
      const res = await adminAPI.updateUser(user.user_id, { full_name: name.trim() })
      onSaved(res.data)
    } catch (err) {
      setError(errorText(err, 'Could not save the change.'))
      setSaving(false)
    }
  }

  return (
    <Modal title="Edit user" onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {error && <Alert>{error}</Alert>}
        <div style={{ fontSize: '13px', color: C.body, marginBottom: '14px' }}>
          {user.email} · <span style={{ textTransform: 'capitalize' }}>{user.role}</span>
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="eu-name">Full name</label>
          <input id="eu-name" style={input} value={name} onChange={e => setName(e.target.value)} autoFocus />
        </div>
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '18px' }}>
          The email and role cannot be changed, because the email domain matches the role.
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
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
    if (passwordProblem(password)) return setError(passwordProblem(password))
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
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '14px' }}>
          This password is temporary: at the next sign-in the user must choose a new one.
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
  const [editing, setEditing]   = useState(null)
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
            Create advisor and admin accounts. Student accounts are created on the Student Intake page.
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
            type="search" aria-label="Search users" placeholder="Search by name, email or student ID"
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
              <tr>{['Name', 'Email', 'Student ID', 'Role', 'Status', 'Created', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>Loading…</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={7} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No users match.</td></tr>
              ) : users.map(u => {
                const badge = ROLE_BADGE[u.role] || ROLE_BADGE.student
                const isMe  = u.user_id === meId
                return (
                  <tr key={u.user_id} style={{ opacity: u.is_active ? 1 : 0.6 }}>
                    <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{u.full_name}{isMe && <span style={{ color: C.muted, fontWeight: '500' }}> (you)</span>}</td>
                    <td style={td}>{u.email}</td>
                    <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{u.student_number || '—'}</td>
                    <td style={td}>
                      <span style={{ padding: '3px 9px', borderRadius: '999px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize', background: badge.bg, color: badge.color }}>{u.role}</span>
                    </td>
                    <td style={{ ...td, color: u.is_active ? C.green : C.red, fontWeight: '600' }}>{u.is_active ? 'Active' : 'Deactivated'}</td>
                    <td style={td}>{u.created_at ? new Date(u.created_at).toLocaleDateString('en-GB') : '—'}</td>
                    <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button style={{ ...btn('secondary'), padding: '6px 10px', fontSize: '12px', marginRight: '6px' }}
                        onClick={() => { setNotice(''); setEditing(u) }}>Edit</button>
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
      {editing && (
        <EditUserModal
          user={editing}
          onClose={() => setEditing(null)}
          onSaved={(saved) => {
            setUsers(list => list.map(x => x.user_id === saved.user_id ? saved : x))
            setNotice(`Saved: ${saved.full_name}.`)
            setEditing(null)
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
