// SEAGAS — Student Progress Tracking (FR-11)
// How readiness changed across assessments, and which recommended activities the
// student has started or finished. Scores are only compared within one role,
// because readiness for different roles measures different skills.
// Unfinished activities can be completed or given up from here, so students do
// not have to find them again among all their recommendations.
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { assessAPI, progressAPI } from '../api/client'
import CompleteActivity from '../components/CompleteActivity'
import EvidenceFiles from '../components/EvidenceFiles'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
            blue: '#2d5be3', green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }
const muted   = { color: C.muted, fontSize: '13px' }
const JD_ROLE = 'Pasted job description'

const scoreColor = (s) => s == null ? C.muted : s >= 70 ? C.green : s >= 50 ? C.amber : C.red
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB') : '—'
const actionBtn = (bg, color, border = bg) => ({
  padding: '5px 11px', fontSize: '12px', fontWeight: '600', borderRadius: '7px', cursor: 'pointer',
  background: bg, color, border: `1px solid ${border}`, whiteSpace: 'nowrap',
})

// actions: optional (activity) => buttons shown on the right of each row
function ActivityList({ items, empty, done, actions }) {
  if (items.length === 0) return <div style={muted}>{empty}</div>
  return items.map(p => (
    <div key={p.progress_id} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '10px 0', borderBottom: '1px solid #f0f1f5' }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>
          {p.url
            ? <a href={p.url} target="_blank" rel="noopener noreferrer" style={{ color: C.ink }}>{p.resource_title}</a>
            : p.resource_title}
        </div>
        <div style={{ fontSize: '11px', color: C.muted, marginTop: '3px', textTransform: 'capitalize' }}>
          {[p.resource_type, p.skill_name, p.provider,
            done ? `Completed ${fmtDate(p.completed_at)}` : `Started ${fmtDate(p.started_at)}`].filter(Boolean).join(' · ')}
        </div>
        {/* Evidence attached to this activity */}
        <EvidenceFiles files={p.files || []} />
      </div>
      <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start', flexWrap: 'wrap', justifyContent: 'flex-end', flexShrink: 0 }}>
        {done && (
          <span style={{ fontSize: '11px', fontWeight: '600', color: C.green, background: '#dcfce7', padding: '3px 9px', borderRadius: '20px', whiteSpace: 'nowrap' }}>✓ Completed</span>
        )}
        {actions && actions(p)}
      </div>
    </div>
  ))
}

export default function ProgressTracking() {
  const navigate = useNavigate()
  const [history, setHistory]   = useState([])
  const [progress, setProgress] = useState([])
  const [role, setRole]         = useState('')
  const [noProfile, setNoProfile] = useState(false)
  const [error, setError]       = useState('')
  const [notice, setNotice]     = useState('')
  const [busy, setBusy]         = useState(null)   // resource_id while a button's request runs
  // Activity whose "Complete" dialog is open (evidence is required to complete)
  const [completing, setCompleting] = useState(null)
  const [loading, setLoading]   = useState(true)

  const load = () => Promise.all([assessAPI.history(), progressAPI.getMy()])
    .then(([h, p]) => {
      // history comes newest first; the chart reads oldest first
      const rows = [...h.data].reverse().map(a => ({ ...a, role_name: a.role_name || JD_ROLE }))
      setHistory(rows)
      setProgress(p.data.progress)
      setRole(r => r || (rows.length ? rows[rows.length - 1].role_name : ''))
      setError('')
    })
    .catch(err => {
      if (err.response?.status === 404) setNoProfile(true)
      else setError('Could not load your progress. Please make sure the backend is running.')
    })
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  // Called by the Complete dialog once evidence is attached and the activity is completed
  const completed = async (p, res) => {
    setCompleting(null)
    await load()
    setNotice(`Well done! "${p.resource_title}" is completed.`)
    // Same follow-up as the Recommendations page: offer to update the profile
    const prompt = res.data.prompt
    if (prompt && window.confirm(`${prompt.message}\n\nOK opens My Profile.`)) {
      try {
        await progressAPI.markSkillAdded(p.resource_id)
      } catch { /* the activity is completed either way */ }
      navigate('/profile')
    }
  }

  const giveUp = async (p) => {
    if (!window.confirm(`Stop "${p.resource_title}"?\n\nIt will show as not started again and any evidence you attached to it is deleted. You can restart it later from Recommendations.`)) return
    setBusy(p.resource_id)
    setNotice('')
    try {
      await progressAPI.drop(p.resource_id)
      await load()
      setNotice(`"${p.resource_title}" was removed from your activities.`)
    } catch {
      setError('Could not remove it. Please try again.')
    } finally {
      setBusy(null)
    }
  }

  const activeActions = (p) => (
    <>
      <button onClick={() => { setNotice(''); setCompleting(p) }} disabled={busy === p.resource_id} style={actionBtn(C.green, '#fff')}>✓ Mark Complete</button>
      {p.assessment_id && (
        <button onClick={() => navigate('/recommendations', { state: { assessmentId: p.assessment_id } })}
          style={actionBtn('#fff', C.blue, C.line)}>View in Recommendations</button>
      )}
      <button onClick={() => giveUp(p)} disabled={busy === p.resource_id} style={actionBtn('#fff', C.red, C.line)}>Give up</button>
    </>
  )

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  const header = (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Progress Tracking</div>
      <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>Track how your readiness improves over time</div>
    </div>
  )

  if (noProfile) return (
    <div style={{ padding: '28px 32px' }}>
      {header}
      <div style={card}>
        <div style={{ ...muted, marginBottom: '12px' }}>Create your profile and run an assessment to start tracking your progress.</div>
        <button onClick={() => navigate('/profile')} style={{ padding: '9px 18px', background: C.blue, color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
          Go to My Profile
        </button>
      </div>
    </div>
  )

  const roles     = [...new Set(history.map(h => h.role_name))]
  const forRole   = history.filter(h => h.role_name === role)
  const first     = forRole.length ? parseFloat(forRole[0].readiness_score) : null
  const current   = forRole.length ? parseFloat(forRole[forRole.length - 1].readiness_score) : null
  const change    = forRole.length > 1 ? Math.round((current - first) * 100) / 100 : null
  const doneList  = progress.filter(p => p.status === 'completed')
  const active    = progress.filter(p => p.status !== 'completed')
  const chart     = forRole.map(h => ({ date: fmtDate(h.created_at), score: parseFloat(h.readiness_score), method: h.matching_method }))

  return (
    <div style={{ padding: '28px 32px' }}>
      {header}

      {completing && (
        <CompleteActivity resource={completing}
          evidence={progress.find(x => x.resource_id === completing.resource_id)?.files || []}
          onChanged={load}
          onCompleted={res => completed(completing, res)}
          onClose={() => setCompleting(null)} />
      )}

      {notice && <div role="status" style={{ background: '#dcfce7', color: C.green, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{notice}</div>}
      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {[
          { label: 'Current Readiness', value: current == null ? '—' : `${current}%`, color: scoreColor(current),
            note: role || 'No assessment yet' },
          { label: 'Change Since First', value: change == null ? '—' : `${change > 0 ? '+' : ''}${change}%`,
            color: change == null ? C.muted : change > 0 ? C.green : change < 0 ? C.red : C.body,
            note: change == null ? 'Run another assessment for this role' : `Over ${forRole.length} assessments` },
          { label: 'Completed Actions', value: `${doneList.length} / ${progress.length}`, color: C.blue,
            note: `${active.length} still in progress` },
        ].map(s => (
          <div key={s.label} style={{ ...card, marginBottom: 0, padding: '18px 20px' }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</div>
            <div style={{ fontSize: '30px', fontWeight: '700', color: s.color, margin: '4px 0', lineHeight: 1.1 }}>{s.value}</div>
            <div style={{ fontSize: '12px', color: C.muted }}>{s.note}</div>
          </div>
        ))}
      </div>

      {/* Readiness over time */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <div style={{ ...heading, marginBottom: 0 }}>Readiness Over Time</div>
          {roles.length > 1 && (
            <select aria-label="Role" value={role} onChange={e => setRole(e.target.value)}
              style={{ padding: '7px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', background: '#fff' }}>
              {roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          )}
        </div>
        {history.length === 0 ? (
          <div style={muted}>
            No assessments yet. <a href="/job-analysis" onClick={e => { e.preventDefault(); navigate('/job-analysis') }} style={{ color: C.blue }}>Run your first assessment</a>.
          </div>
        ) : chart.length < 2 ? (
          <div style={muted}>
            You have one assessment for {role} ({chart[0].score}%). Improve your profile and run it again to see your progress here.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v, _n, p) => [`${v}% (${p.payload.method})`, 'Readiness']} />
              <Line type="monotone" dataKey="score" stroke={C.blue} strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Activities */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        <div style={card}>
          <div style={heading}>In Progress ({active.length})</div>
          <ActivityList items={active} empty="Nothing in progress. Start an activity from Recommendations." actions={activeActions} />
        </div>
        <div style={card}>
          <div style={heading}>Completed ({doneList.length})</div>
          <ActivityList items={doneList} empty="No completed activities yet." done />
        </div>
      </div>
    </div>
  )
}
