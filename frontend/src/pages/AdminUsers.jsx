// SEAGAS — Admin: User Management
// Admins create advisor/admin accounts, rename, activate or deactivate accounts and reset passwords.
// Each advisor has a position (Dean / Head of Programme), which sets the courses they see, and a
// 5-digit staff ID that starts with the position's prefix (backend/advisor_scope.py).
// Students are not created here: their accounts come from the new-student lists (Student Intake).
import { useState, useEffect, useCallback, useRef } from 'react'
import { authAPI, studentAPI } from '../api/client'
import { adminAPI } from '../api/admin'
import { passwordProblem } from '../utils/passwordRules'
import { COURSES, courseLabel, ADVISOR_POSITIONS, advisorPositionOf } from '../utils/courses'
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

// Position drop-down and staff ID. The ID is suggested for the chosen position until the
// admin types their own; changing the position suggests a new one.
// Each office has one Dean: the form says who holds a Dean post now.
function AdvisorFields({ positionId, staffNumber, onChange, keepNumber, userId }) {
  const typed = useRef(false)
  const pos = ADVISOR_POSITIONS.find(p => p.id === positionId)
  const [dean, setDean] = useState(null)     // current Dean of the chosen office (someone else)

  useEffect(() => {
    setDean(null)
    if (!pos) return
    let current = true
    adminAPI.staffNumber(pos.position, pos.courses)
      .then(r => {
        if (!current) return
        const d = r.data.current_dean
        setDean(d && d.user_id !== userId ? d : null)
        if (typed.current) return
        if (keepNumber && staffNumber.startsWith(pos.prefix)) return   // editing: the current ID still fits
        onChange({ staffNumber: r.data.staff_number })
      })
      .catch(() => {})
    return () => { current = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positionId])

  return (
    <>
      <div style={{ marginBottom: '12px' }}>
        <label style={label} htmlFor="adv-pos">Position</label>
        <select id="adv-pos" style={input} value={positionId}
          onChange={e => { typed.current = false; onChange({ positionId: e.target.value }) }}>
          <option value="">Choose the position</option>
          {ADVISOR_POSITIONS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
        </select>
        {pos && (
          <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>
            Sees and adds {pos.courses.map(courseLabel).join(' and ')} students only.
          </div>
        )}
        {dean && (
          <div role="alert" style={{ fontSize: '12px', color: C.red, marginTop: '4px' }}>
            {dean.full_name} is already the {pos.label}. There is only one Dean per office: change their position or
            deactivate their account first.
          </div>
        )}
      </div>
      <div style={{ marginBottom: '12px' }}>
        <label style={label} htmlFor="adv-staff">Staff ID</label>
        <input id="adv-staff" style={{ ...input, fontFamily: 'Consolas, monospace' }} value={staffNumber} maxLength={5}
          inputMode="numeric" placeholder={pos ? `${pos.prefix}xxx` : '5 digits'}
          onChange={e => { typed.current = true; onChange({ staffNumber: e.target.value.replace(/\D/g, '') }) }} />
        <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>
          5 digits{pos ? `, starting with ${pos.prefix} for this position` : ''}. A free ID is suggested; you can change it.
        </div>
      </div>
    </>
  )
}

// Problem with the advisor fields, or '' when they are fine
function advisorProblem(positionId, staffNumber) {
  const pos = ADVISOR_POSITIONS.find(p => p.id === positionId)
  if (!pos) return 'Please choose the advisor\'s position.'
  if (!/^[0-9]{5}$/.test(staffNumber)) return 'The staff ID must be 5 digits.'
  if (!staffNumber.startsWith(pos.prefix)) return `Staff IDs for ${pos.label} start with ${pos.prefix}.`
  return ''
}

// Advisors: like new students, the system makes a temporary password and emails the staff ID,
// school email and password to the advisor's personal email. Admins: the admin types them.
function AddUserModal({ onClose, onCreated }) {
  const [form, setForm]       = useState({ full_name: '', email: '', role: 'advisor', password: '', confirm: '',
                                           personal_email: '', positionId: '', staffNumber: '' })
  const [emailTyped, setEmailTyped] = useState(false)   // advisor school email changed by hand
  const [error, setError]     = useState('')
  const [saving, setSaving]   = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))
  const isAdvisor = form.role === 'advisor'
  // Advisor school email: <staff ID>@advisor.newinti.edu.my unless the admin types another one
  const email = isAdvisor && !emailTyped
    ? (form.staffNumber ? `${form.staffNumber}@${EMAIL_DOMAINS.advisor}` : '')
    : form.email

  const submit = async (e) => {
    e.preventDefault()
    if (!form.full_name.trim())            return setError('Please enter the full name.')
    if (isAdvisor && !EMAIL_RE.test(form.personal_email.trim()))
      return setError('Please enter the advisor\'s personal email: the login details are sent there.')
    if (isAdvisor && advisorProblem(form.positionId, form.staffNumber)) return setError(advisorProblem(form.positionId, form.staffNumber))
    if (!EMAIL_RE.test(email.trim())) return setError('Please enter a valid school email address.')
    if (!email.trim().toLowerCase().endsWith(`@${EMAIL_DOMAINS[form.role]}`))
      return setError(`${isAdvisor ? 'Advisor' : 'Admin'} school emails must end with @${EMAIL_DOMAINS[form.role]}.`)
    if (!isAdvisor && passwordProblem(form.password)) return setError(passwordProblem(form.password))
    if (!isAdvisor && form.password !== form.confirm) return setError('Passwords do not match.')
    const pos = ADVISOR_POSITIONS.find(p => p.id === form.positionId)
    setSaving(true)
    setError('')
    try {
      const res = await adminAPI.createUser({
        full_name: form.full_name.trim(), email: email.trim(), role: form.role,
        ...(isAdvisor
          ? { personal_email: form.personal_email.trim(), advisor_position: pos.position,
              advisor_courses: pos.courses, staff_number: form.staffNumber }
          : { password: form.password }),
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
        {isAdvisor && (
          <>
            <div style={{ marginBottom: '12px' }}>
              <label style={label} htmlFor="nu-personal">Personal email</label>
              <input id="nu-personal" type="email" style={input} value={form.personal_email} onChange={set('personal_email')}
                placeholder="e.g. lim.meiling@gmail.com" autoComplete="off" />
              <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>The login details are sent here.</div>
            </div>
            <AdvisorFields positionId={form.positionId} staffNumber={form.staffNumber}
              onChange={(v) => setForm(f => ({ ...f, ...v }))} />
          </>
        )}
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="nu-email">School email</label>
          <input id="nu-email" type="email" style={input} value={email} autoComplete="off"
            onChange={e => { setEmailTyped(true); setForm(f => ({ ...f, email: e.target.value })) }}
            placeholder={isAdvisor ? `staff ID@${EMAIL_DOMAINS.advisor}` : `name@${EMAIL_DOMAINS.admin}`} />
          {isAdvisor && (
            <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>
              Made from the staff ID; you can change it.
              {emailTyped && <> <button type="button" onClick={() => setEmailTyped(false)}
                style={{ border: 'none', background: 'none', color: C.blue, cursor: 'pointer', padding: 0, fontSize: '12px', fontWeight: '600' }}>
                Use the staff ID again</button></>}
            </div>
          )}
        </div>
        {isAdvisor ? (
          <div style={{ fontSize: '12px', color: C.muted, margin: '6px 0 18px' }}>
            The system makes a temporary password and emails the staff ID, school email and password to the personal
            email. At the first sign-in the advisor must choose their own password.
          </div>
        ) : (
          <>
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
          </>
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Creating…' : 'Create account'}</button>
        </div>
      </form>
    </Modal>
  )
}

function EditUserModal({ user, onClose, onSaved }) {
  const isAdvisor = user.role === 'advisor'
  const isStudent = user.role === 'student'
  const [name, setName]     = useState(user.full_name)
  const [programme, setProgramme] = useState(user.programme || '')
  const [programmes, setProgrammes] = useState([])
  useEffect(() => {
    if (isStudent) studentAPI.programmes(user.course).then(r => setProgrammes(r.data)).catch(() => {})
  }, [isStudent, user.course])
  const [email, setEmail]   = useState(user.email)
  const domain = EMAIL_DOMAINS[user.role] || 'student.newinti.edu.my'
  const [adv, setAdv]       = useState({
    positionId: advisorPositionOf(user.advisor_position, user.advisor_courses)?.id || '',
    staffNumber: user.staff_number || '',
  })
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return setError('Please enter the full name.')
    if (!EMAIL_RE.test(email.trim())) return setError('Please enter a valid email address.')
    if (!email.trim().toLowerCase().endsWith(`@${domain}`)) return setError(`The email must end with @${domain}.`)
    if (isAdvisor && advisorProblem(adv.positionId, adv.staffNumber)) return setError(advisorProblem(adv.positionId, adv.staffNumber))
    const pos = ADVISOR_POSITIONS.find(p => p.id === adv.positionId)
    setSaving(true)
    setError('')
    try {
      const res = await adminAPI.updateUser(user.user_id, {
        full_name: name.trim(),
        ...(email.trim().toLowerCase() !== user.email.toLowerCase() ? { email: email.trim() } : {}),
        ...(isStudent && programme && programme !== user.programme ? { programme } : {}),
        ...(isAdvisor ? { advisor_position: pos.position, advisor_courses: pos.courses, staff_number: adv.staffNumber } : {}),
      })
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
        <div style={{ fontSize: '13px', color: C.body, marginBottom: '14px', textTransform: 'capitalize' }}>{user.role}</div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="eu-name">Full name</label>
          <input id="eu-name" style={input} value={name} onChange={e => setName(e.target.value)} autoFocus />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="eu-email">School email</label>
          <input id="eu-email" type="email" style={input} value={email} onChange={e => setEmail(e.target.value)} autoComplete="off" />
          <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>
            Must end with @{domain}. The user signs in with the new email from now on.
          </div>
        </div>
        {isStudent && (
          <div style={{ marginBottom: '12px' }}>
            <label style={label} htmlFor="eu-prog">Programme ({courseLabel(user.course)})</label>
            <select id="eu-prog" style={input} value={programme} onChange={e => setProgramme(e.target.value)}>
              {!programme && <option value="">Choose the programme</option>}
              {programme && !programmes.some(p => p.programme_name === programme) &&
                <option value={programme}>{programme}</option>}
              {programmes.map(p => <option key={p.programme_name} value={p.programme_name}>{p.programme_name}</option>)}
            </select>
          </div>
        )}
        {isAdvisor && (
          <AdvisorFields positionId={adv.positionId} staffNumber={adv.staffNumber} keepNumber userId={user.user_id}
            onChange={(v) => setAdv(a => ({ ...a, ...v }))} />
        )}
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '18px' }}>
          The role cannot be changed. To reset the password, use Reset password in the list.
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
  const [courseFilter, setCourse] = useState('')   // '' = all; a course shows only its students
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
        course: courseFilter || undefined,
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
  }, [query, roleFilter, courseFilter, page])

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
            type="search" aria-label="Search users" placeholder="Search by name, email, student ID or staff ID"
            style={{ ...input, flex: '1 1 240px', width: 'auto' }}
            value={search} onChange={e => setSearch(e.target.value)}
          />
          <select aria-label="Filter by role" style={{ ...input, flex: '0 0 160px', width: 'auto' }}
            value={roleFilter} disabled={!!courseFilter} title={courseFilter ? 'A course shows students only' : undefined}
            onChange={e => { setPage(0); setRole(e.target.value) }}>
            <option value="">All roles</option>
            <option value="admin">Admins</option>
            <option value="advisor">Advisors</option>
            <option value="student">Students</option>
          </select>
        </div>

        {/* Course: only students of Computer Science, Business or ICT */}
        <div role="tablist" aria-label="Course" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
          {[{ id: '', label: 'All users' }, ...COURSES].map(c => {
            const active = courseFilter === c.id
            const n = c.id ? stats?.courses?.[c.id] : null
            return (
              <button key={c.id || 'all'} role="tab" aria-selected={active}
                onClick={() => { setPage(0); setCourse(c.id); if (c.id) setRole('') }}
                style={{ padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                         background: active ? C.blue : '#fff', color: active ? '#fff' : C.body,
                         border: `1.5px solid ${active ? C.blue : C.line}` }}>
                {c.id ? `${c.label} students` : c.label}{n != null ? ` (${n})` : ''}
              </button>
            )
          })}
        </div>

        {notice && <Alert type="success">{notice}</Alert>}
        {error && <Alert>{error}</Alert>}

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '820px' }}>
            <thead>
              <tr>{['Name', 'Email', 'ID', 'Course / Position', 'Role', 'Status', 'Created', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>Loading…</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={8} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No users match.</td></tr>
              ) : users.map(u => {
                const badge = ROLE_BADGE[u.role] || ROLE_BADGE.student
                const isMe  = u.user_id === meId
                return (
                  <tr key={u.user_id} style={{ opacity: u.is_active ? 1 : 0.6 }}>
                    <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{u.full_name}{isMe && <span style={{ color: C.muted, fontWeight: '500' }}> (you)</span>}</td>
                    <td style={td}>{u.email}</td>
                    <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{u.student_number || u.staff_number || '—'}</td>
                    <td style={td}>
                      {u.course ? courseLabel(u.course) : (u.position_label || '—')}
                      {u.programme && <div style={{ fontSize: '11px', color: C.muted }}>{u.programme}</div>}
                    </td>
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
            setNotice(u.role === 'advisor'
              ? `${u.full_name} (${u.position_label}, staff ID ${u.staff_number}) was created. ` +
                (u.email_status === 'sent'
                  ? `The login details were emailed to ${u.personal_email}.`
                  : 'No mail server is set up, so the login email is stored: open it under Student Intake → Email outbox.')
              : `${u.full_name} (admin) can now sign in with ${u.email}.`)
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
