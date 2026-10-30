// SEAGAS — Admin: Student Intake
// Lists of new students uploaded by advisors. For each list the admin lets the
// system suggest a student ID and school email (both editable), rejects any
// student who should not get an account, and creates the accounts. Each new
// student gets a temporary password by email; without a mail server the emails
// are kept in the Email Outbox tab, so the admin can pass them on.
import { useState, useEffect, useCallback } from 'react'
import { intakeAPI } from '../api/intake'
import { COURSES, courseLabel } from '../utils/courses'
import { studentAPI } from '../api/client'
import { C, card, th, td, tdOne, input, btn, smallBtn, heading, errorText } from './admin/adminStyles'
import { Alert } from './admin/AdminUi'

const STATUS = {
  pending:  { label: 'Pending',  bg: '#fef3c7', color: C.amber },
  created:  { label: 'Created',  bg: '#dcfce7', color: C.green },
  rejected: { label: 'Rejected', bg: '#fee2e2', color: C.red },
}
const MAIL = {
  sent:     { label: 'Sent',     bg: '#dcfce7', color: C.green },
  not_sent: { label: 'Not sent (no mail server)', bg: '#f1f5f9', color: C.body },
  failed:   { label: 'Failed',   bg: '#fee2e2', color: C.red },
}
const fmtDate = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

function Pill({ s }) {
  return <span style={{ padding: '3px 9px', borderRadius: '999px', fontSize: '11px', fontWeight: '600', background: s.bg, color: s.color, whiteSpace: 'nowrap' }}>{s.label}</span>
}

// ── One list: assign IDs, edit, reject, create accounts ──────
function BatchDetail({ batchId, onChanged, onCreated }) {
  const [data, setData]     = useState(null)
  const [edits, setEdits]   = useState({})     // row_id -> { student_number, school_email }
  const [error, setError]   = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy]     = useState('')
  const [programmes, setProgrammes] = useState([])   // every course's programmes

  useEffect(() => { studentAPI.programmes().then(r => setProgrammes(r.data)).catch(() => {}) }, [])

  const load = useCallback(() => intakeAPI.batch(batchId)
    .then(r => { setData(r.data); setEdits({}) })
    .catch(err => setError(errorText(err, 'Could not load the list.'))), [batchId])
  useEffect(() => { setError(''); setNotice(''); load() }, [load])

  const run = async (key, fn) => {
    setBusy(key)
    setError('')
    setNotice('')
    try {
      await fn()
    } catch (err) {
      setError(errorText(err, 'Something went wrong.'))
    } finally {
      setBusy('')
    }
  }

  const assign = () => run('assign', async () => {
    const r = await intakeAPI.assign(batchId)
    setData(r.data)
    setEdits({})
    setNotice('Student IDs and school emails suggested. Check them, change any if needed, then create the accounts.')
  })

  const save = (row) => run(row.row_id, async () => {
    const e = edits[row.row_id]
    await intakeAPI.updateRow(row.row_id, { student_number: e.student_number.trim(), school_email: e.school_email.trim() })
    await load()
    setNotice(`Saved ${row.full_name}.`)
  })

  const changeCourse = (row, course) => run(row.row_id, async () => {
    await intakeAPI.updateRow(row.row_id, { course })
    await load()
    setNotice(`${row.full_name}: course set to ${courseLabel(course)}. Check the programme.`)
  })

  const changeProgramme = (row, programme) => run(row.row_id, async () => {
    await intakeAPI.updateRow(row.row_id, { programme })
    await load()
    setNotice(`${row.full_name}: programme set to ${programme}.`)
  })

  const reject = (row) => {
    const note = window.prompt(`Reject ${row.full_name}? No account will be created.\n\nReason (optional):`, '')
    if (note === null) return
    run(row.row_id, async () => {
      await intakeAPI.reject(row.row_id, note)
      await load()
      onChanged()
      setNotice(`${row.full_name} rejected.`)
    })
  }

  const create = () => {
    const pending = data.rows.filter(r => r.status === 'pending')
    if (Object.keys(edits).length) return setError('Save or undo your changes first.')
    if (!window.confirm(`Create ${pending.length} student account${pending.length === 1 ? '' : 's'} and email each student their login details?`)) return
    run('create', async () => {
      const r = await intakeAPI.createAccounts(batchId)
      await load()
      onChanged()
      const n = r.data.created.length
      const where = r.data.mail_server ? 'were emailed to the students' : 'are in the Email Outbox tab (no mail server is configured)'
      setNotice(`${n} account${n === 1 ? '' : 's'} created. The login details ${where}.`)
      if (r.data.failed.length) setError('Not created: ' + r.data.failed.map(f => `${f.full_name} (${f.error})`).join('; '))
      if (n) onCreated()
    })
  }

  if (!data) return error ? <Alert>{error}</Alert> : <div style={{ color: C.muted, padding: '12px 0' }}>Loading…</div>

  const pending = data.rows.filter(r => r.status === 'pending')
  const missing = pending.filter(r => !r.student_number).length
  const field = (row, key) => edits[row.row_id]?.[key] ?? row[key] ?? ''
  const setField = (row, key, value) => setEdits(e => ({
    ...e, [row.row_id]: { student_number: field(row, 'student_number'), school_email: field(row, 'school_email'), ...e[row.row_id], [key]: value },
  }))

  return (
    <div style={{ ...card, padding: '20px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <div>
          <div style={heading}>{data.batch.file_name}</div>
          <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>{pending.length} pending of {data.rows.length}</div>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button style={btn('secondary')} disabled={!missing || busy === 'assign'} onClick={assign}>
            {busy === 'assign' ? 'Suggesting…' : `Suggest student IDs${missing ? ` (${missing})` : ''}`}
          </button>
          <button style={btn('primary')} disabled={!pending.length || busy === 'create'} onClick={create}>
            {busy === 'create' ? 'Creating…' : `Create ${pending.length} account${pending.length === 1 ? '' : 's'}`}
          </button>
        </div>
      </div>
      {notice && <Alert type="success">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '1450px' }}>
          <thead><tr>{['Row', 'Name', 'Phone', 'Personal email', 'Course', 'Programme', 'Student ID', 'School email', 'Status', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
          <tbody>
            {data.rows.map(r => {
              const editable = r.status === 'pending' && r.student_number
              const changed = !!edits[r.row_id]
              return (
                <tr key={r.row_id} style={{ opacity: r.status === 'rejected' ? 0.6 : 1 }}>
                  <td style={td}>{r.line_number}</td>
                  <td style={{ ...tdOne, color: C.ink, fontWeight: '600' }}>{r.full_name}</td>
                  <td style={tdOne}>{r.phone || '—'}</td>
                  <td style={tdOne}>{r.personal_email}</td>
                  <td style={{ ...td, minWidth: '170px' }}>
                    {r.status === 'pending'
                      ? <select aria-label={`Course for ${r.full_name}`} style={{ ...input, width: 'auto', padding: '6px 8px' }}
                          value={r.course || ''} disabled={busy === r.row_id} onChange={e => changeCourse(r, e.target.value)}>
                          {!r.course && <option value="">Choose…</option>}
                          {COURSES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                        </select>
                      : <span>{courseLabel(r.course)}</span>}
                  </td>
                  <td style={{ ...td, minWidth: '220px' }}>
                    {r.status === 'pending' && r.course
                      ? <select aria-label={`Programme for ${r.full_name}`} style={{ ...input, width: '260px', padding: '6px 8px' }}
                          value={r.programme || ''} disabled={busy === r.row_id} onChange={e => changeProgramme(r, e.target.value)}>
                          {!r.programme && <option value="">Choose…</option>}
                          {programmes.filter(p => p.course === r.course).map(p =>
                            <option key={p.programme_name} value={p.programme_name}>{p.programme_name}</option>)}
                        </select>
                      : <span>{r.programme || '—'}</span>}
                  </td>
                  <td style={tdOne}>
                    {editable
                      ? <input aria-label={`Student ID for ${r.full_name}`} style={{ ...input, width: '110px', fontFamily: 'Consolas, monospace' }} maxLength={9}
                          value={field(r, 'student_number')} onChange={e => setField(r, 'student_number', e.target.value.replace(/\D/g, ''))} />
                      : <span style={{ fontFamily: 'Consolas, monospace' }}>{r.student_number || '—'}</span>}
                  </td>
                  <td style={tdOne}>
                    {editable
                      ? <input aria-label={`School email for ${r.full_name}`} style={{ ...input, width: '250px' }}
                          value={field(r, 'school_email')} onChange={e => setField(r, 'school_email', e.target.value)} />
                      : r.school_email || '—'}
                  </td>
                  <td style={td} title={r.note || undefined}><Pill s={STATUS[r.status]} /></td>
                  <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {changed && (
                      <>
                        <button style={{ ...smallBtn('primary'), marginRight: '6px' }} disabled={busy === r.row_id} onClick={() => save(r)}>Save</button>
                        <button style={{ ...smallBtn(), marginRight: '6px' }} onClick={() => setEdits(e => { const n = { ...e }; delete n[r.row_id]; return n })}>Undo</button>
                      </>
                    )}
                    {r.status === 'pending' && (
                      <button style={smallBtn('danger')} disabled={busy === r.row_id} onClick={() => reject(r)}>Reject</button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Email outbox ─────────────────────────────────────────────
function Outbox() {
  const [data, setData]   = useState(null)
  const [open, setOpen]   = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy]   = useState('')
  const load = () => intakeAPI.outbox().then(r => setData(r.data)).catch(err => setError(errorText(err, 'Could not load the outbox.')))
  useEffect(() => { load() }, [])

  // Send a stored email again, e.g. after the mail server was set up or after a failure
  const resend = async (e) => {
    setBusy(e.email_id); setError(''); setNotice('')
    try {
      const r = await intakeAPI.resend(e.email_id)
      if (r.data.status === 'sent') setNotice(`Sent to ${e.to_address}.`)
      else setError(`Not sent to ${e.to_address}: ${r.data.error || r.data.status}`)
      await load()
    } catch (err) {
      setError(errorText(err, 'Could not send the email.'))
    } finally {
      setBusy('')
    }
  }
  if (error) return <Alert>{error}</Alert>
  if (!data) return <div style={{ color: C.muted }}>Loading…</div>
  return (
    <div style={{ ...card, padding: '20px 24px' }}>
      <div style={{ fontSize: '13px', color: C.body, marginBottom: '14px' }}>
        {data.mail_server
          ? 'A mail server is configured: emails are sent and also listed here.'
          : <>No mail server is configured (<code>SMTP_HOST</code> in backend/.env, see System Settings), so emails are <b>not sent</b>. Open one to pass the login details on, or set up the mail server and use <b>Resend</b>.</>}
        {' '}The newest 50 are shown.
      </div>
      {notice && <Alert type="success">{notice}</Alert>}
      {data.emails.length === 0 ? <div style={{ color: C.muted, fontSize: '13px' }}>No emails yet.</div> : data.emails.map(e => (
        <div key={e.email_id} style={{ borderBottom: '1px solid #f0f1f5', padding: '10px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '13px' }}>
              <b style={{ color: C.ink }}>{e.to_address}</b> <span style={{ color: C.muted }}>· {e.subject} · {fmtDate(e.created_at)}</span>
              {e.related_user_name && <span style={{ color: C.muted }}> · for {e.related_user_name}</span>}
              {(e.attempts > 1 || e.sent_at) && (
                <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>
                  {e.attempts > 1 && `${e.attempts} attempts`}{e.attempts > 1 && e.sent_at && ' · '}{e.sent_at && `sent ${fmtDate(e.sent_at)}`}
                </div>
              )}
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <Pill s={MAIL[e.status] || MAIL.not_sent} />
              {data.mail_server && (
                <button style={smallBtn(e.status === 'sent' ? 'secondary' : 'primary')} disabled={busy === e.email_id}
                  title={e.body.includes('Temporary password') && !e.password_still_temporary
                    ? 'This person already chose their own password: reset it in User Management instead' : undefined}
                  onClick={() => resend(e)}>
                  {busy === e.email_id ? 'Sending…' : e.status === 'sent' ? 'Send again' : 'Resend'}
                </button>
              )}
              <button style={smallBtn()} onClick={() => setOpen(open === e.email_id ? null : e.email_id)}>{open === e.email_id ? 'Hide' : 'Open'}</button>
            </div>
          </div>
          {e.error && <div style={{ fontSize: '12px', color: C.red, marginTop: '4px' }}>{e.error}</div>}
          {open === e.email_id && (
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', background: '#f8fafc', border: `1px solid ${C.line}`, borderRadius: '8px', padding: '12px', marginTop: '8px', color: C.ink }}>{e.body}</pre>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────
export default function AdminIntake() {
  const [tab, setTab]         = useState('lists')
  const [batches, setBatches] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError]     = useState('')
  const [outboxKey, setOutboxKey] = useState(0)

  const load = () => intakeAPI.batches()
    .then(r => { setBatches(r.data); setError('') })
    .catch(err => setError(errorText(err, 'Could not load the lists.')))
  useEffect(() => { load() }, [])

  const tabBtn = (id, text) => (
    <button onClick={() => setTab(id)} style={{
      padding: '10px 18px', fontSize: '13px', fontWeight: tab === id ? '600' : '500', color: tab === id ? C.blue : C.body,
      border: 'none', background: 'none', cursor: 'pointer', borderBottom: `2px solid ${tab === id ? C.blue : 'transparent'}`, marginBottom: '-2px',
    }}>{text}</button>
  )

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Student Intake</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '780px' }}>
          Advisors upload lists of new students. Give each student a student ID and school email, then create the accounts.
          Every student receives a temporary password and must choose their own at first sign-in.
        </div>
      </div>
      <div style={{ display: 'flex', gap: '4px', borderBottom: `2px solid ${C.line}`, marginBottom: '16px' }}>
        {tabBtn('lists', `New student lists${batches.some(b => b.pending) ? ` (${batches.reduce((n, b) => n + b.pending, 0)} pending)` : ''}`)}
        {tabBtn('outbox', 'Email outbox')}
      </div>
      {error && <Alert>{error}</Alert>}

      {tab === 'lists' && (
        <>
          <div style={{ ...card, padding: '20px 24px', marginBottom: '16px' }}>
            {batches.length === 0 ? <div style={{ color: C.muted, fontSize: '13px' }}>No lists uploaded yet. Advisors upload them on their New Students page.</div> : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                  <thead><tr>{['File', 'Uploaded by', 'Uploaded', 'Students', 'Pending', 'Created', 'Rejected', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
                  <tbody>
                    {batches.map(b => (
                      <tr key={b.batch_id} style={{ background: selected === b.batch_id ? '#f5f8ff' : 'transparent' }}>
                        <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{b.file_name}</td>
                        <td style={td}>{b.uploaded_by_name || '—'}</td>
                        <td style={td}>{fmtDate(b.uploaded_at)}</td>
                        <td style={td}>{b.total}</td>
                        <td style={{ ...td, color: C.amber, fontWeight: '600' }}>{b.pending}</td>
                        <td style={{ ...td, color: C.green, fontWeight: '600' }}>{b.created}</td>
                        <td style={{ ...td, color: C.red, fontWeight: '600' }}>{b.rejected}</td>
                        <td style={{ ...td, textAlign: 'right' }}>
                          <button style={smallBtn(b.pending ? 'primary' : 'secondary')} onClick={() => setSelected(selected === b.batch_id ? null : b.batch_id)}>
                            {selected === b.batch_id ? 'Close' : b.pending ? 'Process' : 'View'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          {selected && <BatchDetail batchId={selected} onChanged={load} onCreated={() => setOutboxKey(k => k + 1)} />}
        </>
      )}
      {tab === 'outbox' && <Outbox key={outboxKey} />}
    </div>
  )
}
