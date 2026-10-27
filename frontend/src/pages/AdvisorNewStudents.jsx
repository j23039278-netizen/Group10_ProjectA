// SEAGAS — Advisor: upload the list of new students
// The advisor uploads an Excel / CSV file (Full Name, Phone Number, Personal Email).
// An admin then gives each student a student ID and school email and creates the
// account; the student receives the login details at their personal email.
import { useState, useEffect, useRef } from 'react'
import { intakeAPI } from '../api/intake'
import { courseLabel } from '../utils/courses'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
            blue: '#2d5be3', green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }
const th = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', padding: '8px 10px', borderBottom: `1px solid ${C.line}` }
const td = { padding: '9px 10px', fontSize: '13px', color: C.body, borderBottom: '1px solid #f0f1f5' }
const button = (primary) => ({ padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer',
  border: primary ? 'none' : `1px solid ${C.line}`, background: primary ? C.blue : '#fff', color: primary ? '#fff' : C.body })

const STATUS = {
  pending:  { label: 'Waiting for admin', bg: '#fef3c7', color: C.amber },
  created:  { label: 'Account created',   bg: '#dcfce7', color: C.green },
  rejected: { label: 'Rejected',          bg: '#fee2e2', color: C.red },
}
const fmtDate = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

function errorText(err, fallback) {
  if (!err.response) return 'Cannot reach the server. Please make sure the backend is running.'
  const d = err.response.data?.detail
  if (typeof d === 'string') return d
  if (d?.message) return d.message
  return fallback
}

export default function AdvisorNewStudents() {
  const input = useRef(null)
  const [file, setFile]         = useState(null)
  const [batches, setBatches]   = useState([])
  const [open, setOpen]         = useState(null)    // { batch, rows } of the list being viewed
  const [result, setResult]     = useState(null)    // last upload result
  const [error, setError]       = useState('')
  const [busy, setBusy]         = useState(false)

  const load = () => intakeAPI.batches().then(r => setBatches(r.data)).catch(err => setError(errorText(err, 'Could not load your lists.')))
  useEffect(() => { load() }, [])

  // Excel template from the backend: the Course column is a drop-down list
  const downloadTemplate = async () => {
    try {
      const res = await intakeAPI.template()
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'new_students_template.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(errorText(err, 'Could not download the template.'))
    }
  }

  const upload = async () => {
    if (!file) return setError('Choose an Excel (.xlsx) or CSV file first.')
    setBusy(true)
    setError('')
    setResult(null)
    try {
      const res = await intakeAPI.upload(file)
      setResult(res.data)
      setFile(null)
      input.current.value = ''
      await load()
    } catch (err) {
      const skipped = err.response?.data?.detail?.skipped
      setError(errorText(err, 'Could not upload the file.'))
      if (skipped) setResult({ students: 0, skipped })
    } finally {
      setBusy(false)
    }
  }

  const view = async (b) => {
    if (open?.batch.batch_id === b.batch_id) return setOpen(null)
    try {
      setOpen((await intakeAPI.batch(b.batch_id)).data)
    } catch (err) {
      setError(errorText(err, 'Could not open the list.'))
    }
  }

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>New Students</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '760px' }}>
          Upload the list of new students. An admin gives each student a student ID and a school email and creates the
          account; the student then receives the login details at their personal email.
        </div>
      </div>

      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}

      <div style={card}>
        <div style={heading}>Upload a list</div>
        <div style={{ fontSize: '13px', color: C.body, marginBottom: '12px' }}>
          Excel (.xlsx) or CSV, first row with the column names <b>Full Name</b>, <b>Phone Number</b>, <b>Personal Email</b> and
          <b>Course</b> (Computer Science, Business or ICT — choose it from the drop-down list in the template).
          Up to 1,000 students per file, max 2 MB.{' '}
          <button onClick={downloadTemplate} style={{ border: 'none', background: 'none', color: C.blue, fontWeight: '600', cursor: 'pointer', padding: 0, fontSize: '13px' }}>
            Download the template
          </button>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input ref={input} type="file" accept=".xlsx,.csv" aria-label="Student list file"
            onChange={e => { setFile(e.target.files[0] || null); setError('') }} style={{ fontSize: '13px' }} />
          <button onClick={upload} disabled={busy || !file} style={{ ...button(true), opacity: busy || !file ? 0.6 : 1 }}>
            {busy ? 'Uploading…' : 'Upload'}
          </button>
        </div>
        {result && (
          <div style={{ marginTop: '14px', fontSize: '13px' }}>
            {result.students > 0 && (
              <div role="status" style={{ background: '#dcfce7', color: C.green, padding: '10px 12px', borderRadius: '8px', marginBottom: '8px' }}>
                {result.students} student{result.students === 1 ? '' : 's'} added. An admin will now create their accounts.
              </div>
            )}
            {result.skipped?.length > 0 && (
              <div style={{ background: '#fffbeb', border: '1px solid #fde68a', padding: '10px 12px', borderRadius: '8px', color: C.body }}>
                <b>{result.skipped.length} row{result.skipped.length === 1 ? ' was' : 's were'} skipped:</b>
                <ul style={{ margin: '6px 0 0', paddingLeft: '18px' }}>
                  {result.skipped.map(s => <li key={s.line}>Row {s.line}: {s.error}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div style={card}>
        <div style={heading}>My uploaded lists</div>
        {batches.length === 0 ? <div style={{ color: C.muted, fontSize: '13px' }}>No lists uploaded yet.</div> : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '620px' }}>
              <thead><tr>{['File', 'Uploaded', 'Students', 'Waiting', 'Created', 'Rejected', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
              <tbody>
                {batches.map(b => (
                  <tr key={b.batch_id}>
                    <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{b.file_name}</td>
                    <td style={td}>{fmtDate(b.uploaded_at)}</td>
                    <td style={td}>{b.total}</td>
                    <td style={{ ...td, color: C.amber, fontWeight: '600' }}>{b.pending}</td>
                    <td style={{ ...td, color: C.green, fontWeight: '600' }}>{b.created}</td>
                    <td style={{ ...td, color: C.red, fontWeight: '600' }}>{b.rejected}</td>
                    <td style={{ ...td, textAlign: 'right' }}>
                      <button onClick={() => view(b)} style={{ ...button(false), padding: '5px 10px', fontSize: '12px' }}>
                        {open?.batch.batch_id === b.batch_id ? 'Hide' : 'View'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {open && (
        <div style={card}>
          <div style={heading}>{open.batch.file_name}</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
              <thead><tr>{['Row', 'Name', 'Phone', 'Personal email', 'Course', 'Student ID', 'Status'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
              <tbody>
                {open.rows.map(r => {
                  const st = STATUS[r.status]
                  return (
                    <tr key={r.row_id}>
                      <td style={td}>{r.line_number}</td>
                      <td style={{ ...td, color: C.ink }}>{r.full_name}</td>
                      <td style={td}>{r.phone || '—'}</td>
                      <td style={td}>{r.personal_email}</td>
                      <td style={{ ...td, whiteSpace: 'nowrap' }}>{courseLabel(r.course)}</td>
                      <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{r.status === 'created' ? r.student_number : '—'}</td>
                      <td style={td} title={r.note || undefined}>
                        <span style={{ padding: '3px 9px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: st.bg, color: st.color }}>{st.label}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
