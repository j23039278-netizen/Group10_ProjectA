// SEAGAS — Admin: Student Intake (read-only)
// Advisors upload the lists of new students, create the accounts and send the emails
// (AdvisorNewStudents). Admins can see the lists, the students and the emails here.
// The only thing admins can do is resend the account emails of staff they created.
import { useState, useEffect } from 'react'
import { intakeAPI } from '../api/intake'
import { C, card, th, td, smallBtn, errorText } from './admin/adminStyles'
import { Alert } from './admin/AdminUi'
import { BatchDetail, Outbox } from './intake/IntakeParts'

const fmtDate = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

export default function AdminIntake() {
  const [tab, setTab]         = useState('lists')
  const [batches, setBatches] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError]     = useState('')

  useEffect(() => {
    intakeAPI.batches()
      .then(r => { setBatches(r.data); setError('') })
      .catch(err => setError(errorText(err, 'Could not load the lists.')))
  }, [])

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
          View only. Advisors upload the lists of new students, create the accounts and send the login emails.
        </div>
      </div>
      <div style={{ display: 'flex', gap: '4px', borderBottom: `2px solid ${C.line}`, marginBottom: '16px' }}>
        {tabBtn('lists', 'New student lists')}
        {tabBtn('outbox', 'Email outbox')}
      </div>
      {error && <Alert>{error}</Alert>}

      {tab === 'lists' && (
        <>
          <div style={{ ...card, padding: '20px 24px', marginBottom: '16px' }}>
            {batches.length === 0 ? <div style={{ color: C.muted, fontSize: '13px' }}>No lists uploaded yet. Advisors upload them on their New Students page.</div> : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                  <thead><tr>{['File', 'Uploaded by', 'Uploaded', 'Students', 'Waiting', 'Created', 'Rejected', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
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
                          <button style={smallBtn()} onClick={() => setSelected(selected === b.batch_id ? null : b.batch_id)}>
                            {selected === b.batch_id ? 'Close' : 'View'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          {selected && <BatchDetail batchId={selected} readOnly />}
        </>
      )}
      {tab === 'outbox' && <Outbox />}
    </div>
  )
}
