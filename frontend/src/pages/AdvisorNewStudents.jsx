// SEAGAS — Advisor: new students
// The advisor uploads an Excel / CSV file (Full Name, Student ID, School Email, Phone Number,
// Personal Email, Course, Programme), checks the list and creates the accounts; each student
// receives the login details at their personal email. Admins only look (AdminIntake).
import { useState, useEffect, useRef } from 'react'
import { intakeAPI } from '../api/intake'
import { authAPI } from '../api/client'
import { COURSES } from '../utils/courses'
import { BatchDetail, Outbox } from './intake/IntakeParts'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
            blue: '#2d5be3', green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }
const th = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', padding: '8px 10px', borderBottom: `1px solid ${C.line}`, whiteSpace: 'nowrap' }
const td = { padding: '9px 10px', fontSize: '13px', color: C.body, borderBottom: '1px solid #f0f1f5' }
const tdOne = { ...td, whiteSpace: 'nowrap' }   // IDs, emails, phones, dates stay on one line
const fmtDate = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'
const button = (primary) => ({ padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer',
  border: primary ? 'none' : `1px solid ${C.line}`, background: primary ? C.blue : '#fff', color: primary ? '#fff' : C.body })

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
  const [tab, setTab]           = useState('lists')
  const [open, setOpen]         = useState(null)    // batch_id of the list being viewed
  const [result, setResult]     = useState(null)    // last upload result
  const [error, setError]       = useState('')
  const [busy, setBusy]         = useState(false)

  // Advisors only add students of their own courses (Dean / Head of Programme)
  const [myCourses, setMyCourses] = useState(COURSES.map(c => c.id))
  useEffect(() => { authAPI.me().then(r => setMyCourses(r.data.advisor_courses || [])).catch(() => {}) }, [])
  const courseNames = COURSES.filter(c => myCourses.includes(c.id)).map(c => c.label).join(', ')

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
      const detail = err.response?.data?.detail
      setError(errorText(err, 'Could not upload the file.'))
      if (detail?.skipped) setResult({ students: 0, skipped: detail.skipped, duplicates: detail.duplicates })
    } finally {
      setBusy(false)
    }
  }

  const tabBtn = (id, text) => (
    <button onClick={() => setTab(id)} style={{
      padding: '10px 18px', fontSize: '13px', fontWeight: tab === id ? '600' : '500', color: tab === id ? C.blue : C.body,
      border: 'none', background: 'none', cursor: 'pointer', borderBottom: `2px solid ${tab === id ? C.blue : 'transparent'}`, marginBottom: '-2px',
    }}>{text}</button>
  )

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>New Students</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '760px' }}>
          Upload the list of new students with their student IDs and school emails, check it, then create the accounts.
          Each student receives the login details at their personal email.
        </div>
      </div>

      <div style={{ display: 'flex', gap: '4px', borderBottom: `2px solid ${C.line}`, marginBottom: '16px' }}>
        {tabBtn('lists', 'New student lists')}
        {tabBtn('outbox', 'Email outbox')}
      </div>

      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}

      {tab === 'outbox' && <Outbox />}

      {tab === 'lists' && <>
      <div style={card}>
        <div style={heading}>Upload a list</div>
        <div style={{ fontSize: '13px', color: C.body, marginBottom: '12px' }}>
          Excel (.xlsx) or CSV, first row with the column names <b>Full Name</b>, <b>Student ID</b> (9 digits),{' '}
          <b>School Email</b> (@student.newinti.edu.my), <b>Phone Number</b>, <b>Personal Email</b>,{' '}
          <b>Course</b> ({courseNames}) and <b>Programme</b> — in the template the last two are drop-down lists, and the
          programme list follows the course chosen in the row. You can add students
          of your own course{myCourses.length === 1 ? '' : 's'} only; rows of other courses are skipped.
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
                {result.students} student{result.students === 1 ? '' : 's'} added. Open the list below, check it and create the accounts.
              </div>
            )}
            {result.duplicates?.length > 0 && (
              <div role="alert" style={{ background: '#fee2e2', border: '1px solid #fecaca', padding: '10px 12px', borderRadius: '8px', color: C.red, marginBottom: '8px' }}>
                <b>Please correct {result.duplicates.length === 1 ? 'this row' : `these ${result.duplicates.length} rows`} in your file, then upload it again:</b>
                <ul style={{ margin: '6px 0 0', paddingLeft: '18px' }}>
                  {result.duplicates.map(d => <li key={d.line}>Row {d.line}: {d.error}</li>)}
                </ul>
              </div>
            )}
            {result.skipped?.length > 0 && (
              <div style={{ background: '#fffbeb', border: '1px solid #fde68a', padding: '10px 12px', borderRadius: '8px', color: C.body }}>
                <b>{result.duplicates?.length
                  ? `${result.skipped.length} other row${result.skipped.length === 1 ? ' also has' : 's also have'} a problem:`
                  : `${result.skipped.length} row${result.skipped.length === 1 ? ' was' : 's were'} skipped:`}</b>
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
                    <td style={tdOne}>{fmtDate(b.uploaded_at)}</td>
                    <td style={td}>{b.total}</td>
                    <td style={{ ...td, color: C.amber, fontWeight: '600' }}>{b.pending}</td>
                    <td style={{ ...td, color: C.green, fontWeight: '600' }}>{b.created}</td>
                    <td style={{ ...td, color: C.red, fontWeight: '600' }}>{b.rejected}</td>
                    <td style={{ ...td, textAlign: 'right' }}>
                      <button onClick={() => setOpen(open === b.batch_id ? null : b.batch_id)}
                        style={{ ...button(b.pending > 0 && open !== b.batch_id), padding: '5px 10px', fontSize: '12px' }}>
                        {open === b.batch_id ? 'Hide' : b.pending > 0 ? 'Check and create' : 'View'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {open && <BatchDetail batchId={open} courses={myCourses} onChanged={load} />}
      </>}
    </div>
  )
}
