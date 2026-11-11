// SEAGAS — Start-of-semester reminder (January, May, September) to update GPA and CGPA.
// Shown while the profile's results_reminder is true (worked out by the backend).
import { useState } from 'react'
import { studentAPI } from '../api/client'

const fmt = (d) => new Date(d).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })

export default function ResultsReminder({ profile, onUpdate, onConfirmed }) {
  const [busy, setBusy]   = useState(false)
  const [error, setError] = useState('')
  if (!profile?.results_reminder) return null

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      await studentAPI.confirmResults()
      onConfirmed?.()
    } catch {
      setError('Could not save. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  // Fixed yellow and red (not the theme's status colours, which are grey in the student theme),
  // so the reminder stands out
  const btn = (primary) => ({ padding: '7px 14px', fontSize: '12px', fontWeight: '700', borderRadius: '8px', cursor: 'pointer',
    border: primary ? '1px solid #dc2626' : '1px solid #facc15', background: primary ? '#dc2626' : '#fff', color: primary ? '#fff' : '#854d0e' })

  return (
    <div role="status" style={{ background: '#fef9c3', border: '1px solid #facc15', borderLeft: '5px solid #dc2626', borderRadius: '12px',
                                padding: '14px 18px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap',
                                boxShadow: '0 2px 8px rgba(202, 138, 4, 0.15)' }}>
      <span aria-hidden="true" style={{ fontSize: '20px', lineHeight: 1 }}>🔔</span>
      <div style={{ flex: '1 1 320px', fontSize: '13px', color: '#713f12' }}>
        <b style={{ color: '#b91c1c' }}>New semester ({fmt(profile.semester_start)}):</b> please update your GPA and CGPA so your advisor sees your latest results.
        {error && <div style={{ color: '#dc2626', marginTop: '4px' }}>{error}</div>}
      </div>
      <button onClick={onUpdate} style={btn(true)}>Update GPA / CGPA</button>
      <button onClick={confirm} disabled={busy} style={{ ...btn(false), opacity: busy ? 0.6 : 1 }}>
        {busy ? 'Saving…' : 'No change this semester'}
      </button>
    </div>
  )
}
