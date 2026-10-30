// SEAGAS — Admin: System Settings (FR-16). Values stored in the database (backend/settings.py);
// the mail server is set in backend/.env and only checked here, never stored or shown.
import { useState, useEffect } from 'react'
import { adminAPI } from '../api/admin'
import { C, card, input, label, btn, heading, errorText } from './admin/adminStyles'
import { Alert } from './admin/AdminUi'

const fmtDateTime = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : ''
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const readable = (mmdd) => {
  const [m, d] = mmdd.split('-').map(Number)
  return m >= 1 && m <= 12 && d ? `${d} ${MONTHS[m - 1]}` : mmdd
}

export default function AdminSettings() {
  const [data, setData]     = useState(null)
  const [form, setForm]     = useState({})
  const [error, setError]   = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)
  const [testTo, setTestTo] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  const show = (d) => {
    setData(d)
    setForm(Object.fromEntries(d.settings.map(s => [s.key, s.value])))
  }
  useEffect(() => {
    adminAPI.settings().then(r => show(r.data)).catch(err => setError(errorText(err, 'Could not load the settings.')))
  }, [])

  if (!data) return <div style={{ padding: '40px', color: C.muted }}>{error || 'Loading...'}</div>

  const byKey = Object.fromEntries(data.settings.map(s => [s.key, s]))
  const changed = data.settings.filter(s => JSON.stringify(form[s.key]) !== JSON.stringify(s.value))

  const save = async () => {
    setSaving(true); setError(''); setNotice('')
    try {
      const values = Object.fromEntries(changed.map(s => [s.key, form[s.key]]))
      show((await adminAPI.saveSettings(values)).data)
      setNotice('Settings saved. They apply straight away.')
    } catch (err) {
      setError(errorText(err, 'Could not save the settings.'))
    } finally {
      setSaving(false)
    }
  }

  const sendTest = async () => {
    setTesting(true); setTestResult(null)
    try {
      setTestResult((await adminAPI.testEmail(testTo.trim())).data)
    } catch (err) {
      setTestResult({ status: 'failed', error: errorText(err, 'Could not send the test email.') })
    } finally {
      setTesting(false)
    }
  }

  const numberField = (key) => {
    const s = byKey[key]
    return (
      <div key={key} style={{ marginBottom: '16px' }}>
        <label style={label} htmlFor={`set-${key}`}>{s.label}</label>
        <input id={`set-${key}`} type="number" min={s.min} max={s.max} step={1} style={{ ...input, width: '140px' }}
          value={form[key] ?? ''} onChange={e => setForm(f => ({ ...f, [key]: e.target.value === '' ? '' : Number(e.target.value) }))} />
        <span style={{ fontSize: '12px', color: C.muted, marginLeft: '10px' }}>{s.min}–{s.max} · default {s.default}</span>
        <div style={{ fontSize: '12px', color: C.muted, marginTop: '4px' }}>{s.help}</div>
        {s.updated_at && <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>Changed by {s.updated_by || 'a former admin'} on {fmtDateTime(s.updated_at)}</div>}
      </div>
    )
  }

  const starts = form.semester_starts || []
  const sem = byKey.semester_starts
  const mail = data.email

  return (
    <div style={{ padding: '28px 32px', maxWidth: '980px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>System Settings</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
          Settings that apply to everyone. Changes take effect straight away and are recorded in the audit log.
        </div>
      </div>
      {error && <Alert>{error}</Alert>}
      {notice && <Alert type="success">{notice}</Alert>}

      {/* Academic calendar */}
      <div style={{ ...card, padding: '22px 24px', marginBottom: '16px' }}>
        <div style={{ ...heading, marginBottom: '14px' }}>Academic calendar</div>
        <div style={label}>{sem.label}</div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          {starts.map((d, i) => (
            <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', border: `1px solid ${C.line}`, borderRadius: '8px', padding: '4px 6px 4px 8px' }}>
              <input aria-label={`Semester start ${i + 1} (MM-DD)`} value={d} maxLength={5} placeholder="MM-DD"
                onChange={e => setForm(f => ({ ...f, semester_starts: starts.map((x, j) => (j === i ? e.target.value : x)) }))}
                style={{ width: '60px', border: 'none', outline: 'none', fontFamily: 'Consolas, monospace', fontSize: '13px' }} />
              <span style={{ fontSize: '12px', color: C.muted }}>{readable(d)}</span>
              <button aria-label="Remove this date" disabled={starts.length <= 1}
                onClick={() => setForm(f => ({ ...f, semester_starts: starts.filter((_, j) => j !== i) }))}
                style={{ border: 'none', background: 'none', color: C.red, cursor: 'pointer', fontSize: '14px', padding: '0 2px' }}>×</button>
            </span>
          ))}
          {starts.length < 6 && (
            <button style={{ ...btn('secondary'), padding: '5px 10px', fontSize: '12px' }}
              onClick={() => setForm(f => ({ ...f, semester_starts: [...starts, ''] }))}>+ Add date</button>
          )}
        </div>
        <div style={{ fontSize: '12px', color: C.muted, marginTop: '6px' }}>{sem.help} Default: {sem.default.map(readable).join(', ')}.</div>
        {sem.updated_at && <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>Changed by {sem.updated_by || 'a former admin'} on {fmtDateTime(sem.updated_at)}</div>}
      </div>

      {/* Readiness bands */}
      <div style={{ ...card, padding: '22px 24px', marginBottom: '16px' }}>
        <div style={{ ...heading, marginBottom: '14px' }}>Readiness bands (advisor dashboard)</div>
        {numberField('readiness_on_track')}
        {numberField('readiness_needs_support')}
        <div style={{ fontSize: '12px', color: C.body, background: '#f8fafc', borderRadius: '8px', padding: '8px 10px' }}>
          Preview: <b style={{ color: C.green }}>On Track</b> ≥ {form.readiness_on_track}% · <b style={{ color: C.amber }}>Developing</b> {form.readiness_needs_support}–{(Number(form.readiness_on_track) || 0) - 1}% ·{' '}
          <b style={{ color: C.red }}>Needs Support</b> &lt; {form.readiness_needs_support}%
        </div>
      </div>

      {/* Uploads */}
      <div style={{ ...card, padding: '22px 24px', marginBottom: '16px' }}>
        <div style={{ ...heading, marginBottom: '14px' }}>Uploads</div>
        {numberField('max_upload_mb')}
        {numberField('max_evidence_per_item')}
      </div>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '24px' }}>
        <button style={btn('primary')} disabled={saving || changed.length === 0} onClick={save}>
          {saving ? 'Saving…' : changed.length ? `Save ${changed.length} change${changed.length === 1 ? '' : 's'}` : 'No changes'}
        </button>
        {changed.length > 0 && <button style={btn('secondary')} onClick={() => show(data)}>Undo changes</button>}
      </div>

      {/* Email */}
      <div style={{ ...card, padding: '22px 24px' }}>
        <div style={{ ...heading, marginBottom: '6px' }}>Email (account emails to students and advisors)</div>
        {mail.configured ? (
          <div style={{ fontSize: '13px', color: C.body, marginBottom: '12px' }}>
            <span style={{ color: C.green, fontWeight: '700' }}>● Mail server set up.</span> {mail.host}:{mail.port} · {mail.security.toUpperCase()} ·
            from <b>{mail.from_address}</b>{mail.login ? ' · signs in with a user name' : ''}.
            New account emails are sent automatically; older ones can be resent from Student Intake → Email outbox.
          </div>
        ) : (
          <div style={{ fontSize: '13px', color: C.body, marginBottom: '12px' }}>
            <span style={{ color: C.amber, fontWeight: '700' }}>● No mail server yet.</span> Emails are only stored in Student Intake → Email outbox.
            To send them, add these lines to <code>backend/.env</code> (never to git) and restart the backend:
            <pre style={{ background: '#f8fafc', border: `1px solid ${C.line}`, borderRadius: '8px', padding: '10px 12px', fontSize: '12px', marginTop: '8px', whiteSpace: 'pre-wrap' }}>
{`SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USER=your.account@gmail.com
SMTP_PASSWORD=your 16-letter app password
SMTP_FROM=your.account@gmail.com`}
            </pre>
            <div style={{ fontSize: '12px', color: C.muted }}>
              For Gmail, turn on 2-step verification and create an App Password (Google Account → Security → App passwords);
              the normal account password does not work. Other providers give their own host, port and security (SSL uses port 465).
            </div>
          </div>
        )}
        <label style={label} htmlFor="test-to">Send a test email to</label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input id="test-to" type="email" style={{ ...input, width: '300px' }} value={testTo} onChange={e => setTestTo(e.target.value)} placeholder="you@example.com" />
          <button style={btn('secondary')} disabled={!mail.configured || testing || !testTo.trim()} onClick={sendTest}
            title={mail.configured ? undefined : 'Set up the mail server first'}>
            {testing ? 'Sending…' : 'Send test email'}
          </button>
        </div>
        {testResult && (
          <div role="status" style={{ marginTop: '10px', fontSize: '13px', color: testResult.status === 'sent' ? C.green : C.red }}>
            {testResult.status === 'sent' ? `Sent. Check the inbox (and spam folder) of ${testTo}.` : `Not sent: ${testResult.error || testResult.status}`}
          </div>
        )}
      </div>
    </div>
  )
}
