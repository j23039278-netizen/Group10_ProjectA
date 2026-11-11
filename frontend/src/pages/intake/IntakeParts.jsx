// SEAGAS — Parts of the new-student pages. Advisors check a list, create the accounts and
// resend emails (AdvisorNewStudents); admins see the same things read-only (AdminIntake).
import { useState, useEffect, useCallback } from 'react'
import { intakeAPI } from '../../api/intake'
import { studentAPI } from '../../api/client'
import { COURSES, courseLabel } from '../../utils/courses'
import { C, card, th, td, tdOne, input, btn, smallBtn, heading, errorText } from '../admin/adminStyles'
import { Alert } from '../admin/AdminUi'

const STATUS = {
  pending:  { label: 'Waiting',          bg: '#fef3c7', color: C.amber },
  created:  { label: 'Account created',  bg: '#dcfce7', color: C.green },
  rejected: { label: 'Rejected',         bg: '#fee2e2', color: C.red },
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

// ── One list. readOnly: only look (admins). courses: the course codes the advisor may choose ──
export function BatchDetail({ batchId, readOnly = false, courses = [], onChanged, onCreated }) {
  const [data, setData]     = useState(null)
  const [edits, setEdits]   = useState({})     // row_id -> { student_number, school_email }
  const [error, setError]   = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy]     = useState('')
  const [programmes, setProgrammes] = useState([])   // every course's programmes

  useEffect(() => {
    if (!readOnly) studentAPI.programmes().then(r => setProgrammes(r.data)).catch(() => {})
  }, [readOnly])

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
      onChanged?.()
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
      onChanged?.()
      const n = r.data.created.length
      const where = r.data.mail_server ? 'were emailed to the students' : 'are in the Email outbox tab (no mail server is set up)'
      setNotice(`${n} account${n === 1 ? '' : 's'} created. The login details ${where}.`)
      if (r.data.failed.length) setError('Not created: ' + r.data.failed.map(f => `${f.full_name} (${f.error})`).join('; '))
      if (n) onCreated?.()
    })
  }

  if (!data) return error ? <Alert>{error}</Alert> : <div style={{ color: C.muted, padding: '12px 0' }}>Loading…</div>

  const pending = data.rows.filter(r => r.status === 'pending')
  const field = (row, key) => edits[row.row_id]?.[key] ?? row[key] ?? ''
  const setField = (row, key, value) => setEdits(e => ({
    ...e, [row.row_id]: { student_number: field(row, 'student_number'), school_email: field(row, 'school_email'), ...e[row.row_id], [key]: value },
  }))
  const headers = ['Row', 'Name', 'Student ID', 'School email', 'Phone', 'Course', 'Programme', 'Status']

  return (
    <div style={{ ...card, padding: '20px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <div>
          <div style={heading}>{data.batch.file_name}</div>
          <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>{pending.length} waiting of {data.rows.length}</div>
        </div>
        {!readOnly && (
          <button style={btn('primary')} disabled={!pending.length || busy === 'create'} onClick={create}>
            {busy === 'create' ? 'Creating…' : `Create ${pending.length} account${pending.length === 1 ? '' : 's'} and send emails`}
          </button>
        )}
      </div>
      {notice && <Alert type="success">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '1250px' }}>
          <thead><tr>{(readOnly ? headers : [...headers, '']).map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
          <tbody>
            {data.rows.map(r => {
              const editable = !readOnly && r.status === 'pending'
              const changed = !!edits[r.row_id]
              return (
                <tr key={r.row_id} style={{ opacity: r.status === 'rejected' ? 0.6 : 1 }}>
                  <td style={td}>{r.line_number}</td>
                  <td style={{ ...tdOne, color: C.ink, fontWeight: '600' }}>{r.full_name}</td>
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
                  <td style={tdOne}>{r.phone || '—'}</td>
                  <td style={{ ...td, minWidth: '170px' }}>
                    {editable
                      ? <select aria-label={`Course for ${r.full_name}`} style={{ ...input, width: 'auto', padding: '6px 8px' }}
                          value={r.course || ''} disabled={busy === r.row_id} onChange={e => changeCourse(r, e.target.value)}>
                          {!r.course && <option value="">Choose…</option>}
                          {COURSES.filter(c => courses.includes(c.id)).map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                        </select>
                      : <span>{courseLabel(r.course)}</span>}
                  </td>
                  <td style={{ ...td, minWidth: '220px' }}>
                    {editable && r.course
                      ? <select aria-label={`Programme for ${r.full_name}`} style={{ ...input, width: '260px', padding: '6px 8px' }}
                          value={r.programme || ''} disabled={busy === r.row_id} onChange={e => changeProgramme(r, e.target.value)}>
                          {!r.programme && <option value="">Choose…</option>}
                          {programmes.filter(p => p.course === r.course).map(p =>
                            <option key={p.programme_name} value={p.programme_name}>{p.programme_name}</option>)}
                        </select>
                      : <span>{r.programme || '—'}</span>}
                  </td>
                  <td style={td} title={r.note || undefined}><Pill s={STATUS[r.status]} /></td>
                  {!readOnly && (
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
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Email outbox. Resend shows only where the backend allows it (can_resend) ──
export function Outbox() {
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
  if (!data) return error ? <Alert>{error}</Alert> : <div style={{ color: C.muted }}>Loading…</div>
  return (
    <div style={{ ...card, padding: '20px 24px' }}>
      <div style={{ fontSize: '13px', color: C.body, marginBottom: '14px' }}>
        {data.mail_server
          ? 'A mail server is set up: emails are sent and also listed here.'
          : <>No mail server is set up (<code>SMTP_HOST</code> in backend/.env), so emails are <b>not sent</b>. Open one to pass the login details on, or use <b>Resend</b> once the mail server is set up.</>}
        {' '}The newest 50 are shown.
      </div>
      {notice && <Alert type="success">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}
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
              {data.mail_server && e.can_resend && (
                <button style={smallBtn(e.status === 'sent' ? 'secondary' : 'primary')} disabled={busy === e.email_id}
                  title={e.body.includes('Temporary password') && !e.password_still_temporary
                    ? 'This person already chose their own password: an admin can reset it in User Management' : undefined}
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
