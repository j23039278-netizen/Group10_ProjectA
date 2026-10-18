// SEAGAS — Admin: Audit Log
// Who did what and when: sign-ins (also failed ones), registrations, assessments,
// JD analyses, advisors opening a student's record and every admin change.
import { useState, useEffect, useCallback } from 'react'
import { adminAPI } from '../api/admin'
import { C, card, th, td, input, smallBtn, errorText } from './admin/adminStyles'
import { Alert } from './admin/AdminUi'

const PAGE_SIZE = 50

// action prefix filters (the API matches the start of the action name)
const GROUPS = [
  { id: '',          label: 'All events' },
  { id: 'auth.',     label: 'Sign-in and registration' },
  { id: 'auth.login_failed', label: 'Failed sign-ins only' },
  { id: 'assessment.', label: 'Assessments' },
  { id: 'jd.',       label: 'JD analyses' },
  { id: 'advisor.',  label: 'Advisor views' },
  { id: 'admin.',    label: 'Admin changes' },
]

const ACTION_LABEL = {
  'auth.login': 'Signed in', 'auth.login_failed': 'Failed sign-in', 'auth.register': 'Registered',
  'assessment.run': 'Ran assessment', 'jd.analyse': 'Analysed JD',
  'advisor.view_student': 'Viewed student', 'advisor.view_file': 'Opened evidence file',
  'admin.user_create': 'Created account', 'admin.user_update': 'Changed account',
  'admin.password_reset': 'Reset password',
  'admin.skill_create': 'Added skill', 'admin.skill_update': 'Changed skill',
  'admin.role_create': 'Added role', 'admin.role_update': 'Changed role',
  'admin.resource_create': 'Added resource', 'admin.resource_update': 'Changed resource',
}

function describe(details) {
  if (!details) return '—'
  return Object.entries(details).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' · ')
}

export default function AdminAudit() {
  const [entries, setEntries] = useState([])
  const [total, setTotal]     = useState(0)
  const [group, setGroup]     = useState('')
  const [search, setSearch]   = useState('')
  const [query, setQuery]     = useState('')
  const [page, setPage]       = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminAPI.auditLog({ action: group || undefined, search: query || undefined,
                                            limit: PAGE_SIZE, offset: page * PAGE_SIZE })
      setEntries(res.data.entries)
      setTotal(res.data.total)
      setError('')
    } catch (err) {
      setError(errorText(err, 'Could not load the audit log.'))
    } finally {
      setLoading(false)
    }
  }, [group, query, page])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    const t = setTimeout(() => { setPage(0); setQuery(search.trim()) }, 300)
    return () => clearTimeout(t)
  }, [search])

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Audit Log</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
          Sign-ins, registrations, assessments, JD analyses, advisors viewing students, and admin changes. Newest first.
        </div>
      </div>

      {error && <Alert>{error}</Alert>}

      <div style={{ ...card, padding: '20px 24px' }}>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
          <input type="search" aria-label="Search by email" placeholder="Search by email or record ID"
            style={{ ...input, flex: '1 1 240px', width: 'auto' }} value={search} onChange={e => setSearch(e.target.value)} />
          <select aria-label="Filter by event type" style={{ ...input, flex: '0 0 220px', width: 'auto' }}
            value={group} onChange={e => { setPage(0); setGroup(e.target.value) }}>
            {GROUPS.map(g => <option key={g.id} value={g.id}>{g.label}</option>)}
          </select>
          <button style={smallBtn()} onClick={load}>Refresh</button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '860px' }}>
            <thead><tr>{['Time', 'Who', 'Event', 'Details', 'IP'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>Loading…</td></tr>
              ) : entries.length === 0 ? (
                <tr><td colSpan={5} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No events match.</td></tr>
              ) : entries.map(e => {
                const failed = e.action === 'auth.login_failed'
                return (
                  <tr key={e.log_id}>
                    <td style={{ ...td, whiteSpace: 'nowrap' }}>{new Date(e.created_at).toLocaleString('en-GB')}</td>
                    <td style={td}>
                      <div style={{ color: C.ink }}>{e.actor_email || '—'}</div>
                      {e.actor_role && <div style={{ fontSize: '11px', color: C.muted, textTransform: 'capitalize' }}>{e.actor_role}</div>}
                    </td>
                    <td style={{ ...td, whiteSpace: 'nowrap', fontWeight: '600', color: failed ? C.red : C.ink }}>
                      {ACTION_LABEL[e.action] || e.action}
                    </td>
                    <td style={{ ...td, color: C.muted, fontSize: '12px' }}>
                      {e.target_type && <div>{e.target_type}: <span style={{ fontFamily: 'monospace' }}>{e.target_id}</span></div>}
                      <div>{describe(e.details)}</div>
                    </td>
                    <td style={{ ...td, whiteSpace: 'nowrap', fontSize: '12px' }}>{e.ip_address || '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', fontSize: '12px', color: C.muted, flexWrap: 'wrap', gap: '8px' }}>
          <span>{total} event{total === 1 ? '' : 's'}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button style={smallBtn()} disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Prev</button>
            <span>Page {page + 1} of {pages}</span>
            <button style={smallBtn()} disabled={page + 1 >= pages} onClick={() => setPage(p => p + 1)}>Next →</button>
          </div>
        </div>
      </div>
    </div>
  )
}
