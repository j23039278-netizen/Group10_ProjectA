// SEAGAS — Advisor: one student's profile, latest assessment, skill gaps, readiness over time,
// development progress (FR-13), the student's CV, and advisor notes. Notes include the advisor's
// review of the AI result (agree / disagree), the human check on the automated scores.
import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { advisorAPI } from '../api/advisor'
import { label } from '../utils/labels'
import EvidenceFiles from '../components/EvidenceFiles'
import DecisionNotice from '../components/DecisionNotice'
import { courseLabel } from '../utils/courses'
import { experienceTypeLabel, period } from '../utils/experience'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
            blue: '#2d5be3', green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }
const muted   = { color: C.muted, fontSize: '13px' }
const btn     = (primary) => ({ padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer', whiteSpace: 'nowrap',
                                border: primary ? 'none' : `1px solid ${C.line}`, background: primary ? C.blue : '#fff', color: primary ? '#fff' : C.body })
const small   = (color = C.body) => ({ background: 'none', border: `1px solid ${C.line}`, borderRadius: '6px', padding: '3px 9px', fontSize: '11px', fontWeight: '600', color, cursor: 'pointer' })

const DIMENSIONS = [
  ['score_technical',     'Technical Skills'],
  ['score_ai_digital',    'AI / Digital Skills'],
  ['score_analytical',    'Analytical Skills'],
  ['score_communication', 'Communication'],
  ['score_project_exp',   'Project Experience'],
  ['score_certification', 'Certification'],
  ['score_industry_exp',  'Industry Experience'],
]
const CATEGORIES = [['Technical', 'Technical'], ['AI_Digital', 'AI / Digital'], ['Analytical', 'Analytical'], ['Soft', 'Soft skills']]

const STATUS = {
  strong:     { label: 'Strong',     bg: '#dcfce7', color: C.green },
  developing: { label: 'Developing', bg: '#fef3c7', color: C.amber },
  gap:        { label: 'Skill Gap',  bg: '#fee2e2', color: C.red },
}
const PROGRESS = {
  completed:   { label: 'Completed',   bg: '#dcfce7', color: C.green },
  in_progress: { label: 'In progress', bg: '#dbeafe', color: C.blue },
  saved:       { label: 'Saved',       bg: '#f1f5f9', color: C.muted },
}
const VERDICT = {
  agree:    { label: 'Agrees with the AI result',    bg: '#dcfce7', color: C.green },
  disagree: { label: 'Disagrees with the AI result', bg: '#fee2e2', color: C.red },
}

const scoreColor = (s) => s == null ? C.muted : s >= 70 ? C.green : s >= 40 ? C.amber : C.red
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB') : '—'
const fmtDateTime = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'
const num = (v) => v == null ? null : parseFloat(v)
const errText = (e, fallback) => {
  const d = e.response?.data?.detail
  return typeof d === 'string' ? d : fallback
}

// Print only the report, without the portal around it
const PRINT_CSS = `
@media print {
  @page { size: A4; margin: 12mm; }
  body * { visibility: hidden !important; }
  .report-sheet, .report-sheet * { visibility: visible !important; }
  .report-sheet { position: absolute; left: 0; top: 0; width: 100%; padding: 0 !important; }
  .report-sheet .no-print { display: none !important; }
  .report-card { break-inside: avoid; }
}`

function Pill({ bg, color, children }) {
  return <span style={{ padding: '3px 9px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: bg, color, whiteSpace: 'nowrap' }}>{children}</span>
}

function Field({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.4px' }}>{label}</div>
      <div style={{ fontSize: '13px', color: C.ink, marginTop: '3px', overflowWrap: 'break-word' }}>{value || '—'}</div>
    </div>
  )
}

// ── Advisor notes ────────────────────────────────────────────
function Notes({ userId, notes, assessment, onChange }) {
  const [body, setBody]       = useState('')
  const [type, setType]       = useState('general')
  const [verdict, setVerdict] = useState('agree')
  const [editing, setEditing] = useState(null)        // { note_id, body, ai_verdict }
  const [busy, setBusy]       = useState(false)
  const [error, setError]     = useState('')

  const save = async () => {
    if (!body.trim()) return setError('Write the note first.')
    setBusy(true); setError('')
    try {
      await advisorAPI.addNote(userId, type === 'ai_review'
        ? { body: body.trim(), note_type: 'ai_review', ai_verdict: verdict, assessment_id: assessment.assessment_id }
        : { body: body.trim() })
      setBody(''); setType('general'); setVerdict('agree')
      onChange()
    } catch (e) {
      setError(errText(e, 'Could not save the note.'))
    } finally {
      setBusy(false)
    }
  }

  const saveEdit = async () => {
    if (!editing.body.trim()) return setError('A note cannot be empty.')
    setBusy(true); setError('')
    try {
      await advisorAPI.updateNote(editing.note_id, { body: editing.body.trim(), ...(editing.ai_verdict ? { ai_verdict: editing.ai_verdict } : {}) })
      setEditing(null)
      onChange()
    } catch (e) {
      setError(errText(e, 'Could not save the change.'))
    } finally {
      setBusy(false)
    }
  }

  const remove = async (n) => {
    if (!window.confirm('Delete this note?')) return
    try {
      await advisorAPI.deleteNote(n.note_id)
      onChange()
    } catch (e) {
      setError(errText(e, 'Could not delete the note.'))
    }
  }

  return (
    <div className="report-card" style={card} id="advisor-notes">
      <div style={{ ...heading, marginBottom: '4px' }}>Advisor Notes ({notes.length})</div>
      <div style={{ fontSize: '12px', color: C.muted, marginBottom: '12px' }}>
        Seen by advisors and admins of this course, never by the student. Use a review to record whether you agree with the
        AI result of the latest assessment, and why.
      </div>
      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '8px 10px', borderRadius: '8px', fontSize: '12px', marginBottom: '10px' }}>{error}</div>}

      <div className="no-print" style={{ border: `1px solid ${C.line}`, borderRadius: '10px', padding: '12px', marginBottom: '14px', background: '#fafbfc' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '8px', fontSize: '13px', color: C.body }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input type="radio" name="note-type" checked={type === 'general'} onChange={() => setType('general')} /> General note
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: assessment ? 'pointer' : 'not-allowed', opacity: assessment ? 1 : 0.5 }}
            title={assessment ? undefined : 'The student has no assessment yet'}>
            <input type="radio" name="note-type" checked={type === 'ai_review'} disabled={!assessment} onChange={() => setType('ai_review')} />
            Review of the latest AI result
          </label>
        </div>
        {type === 'ai_review' && assessment && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '8px', fontSize: '12px', color: C.body }}>
            <span>{assessment.role_name || 'Job description'} · {num(assessment.readiness_score)}% · {fmtDate(assessment.created_at)}:</span>
            {Object.entries(VERDICT).map(([k, v]) => (
              <label key={k} style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', padding: '4px 10px', borderRadius: '20px',
                                      border: `1.5px solid ${verdict === k ? v.color : C.line}`, background: verdict === k ? v.bg : '#fff', color: verdict === k ? v.color : C.body, fontWeight: '600' }}>
                <input type="radio" name="verdict" checked={verdict === k} onChange={() => setVerdict(k)} style={{ display: 'none' }} />
                {k === 'agree' ? 'I agree' : 'I disagree'}
              </label>
            ))}
          </div>
        )}
        <textarea aria-label="New advisor note" rows={3} maxLength={2000} value={body} onChange={e => setBody(e.target.value)}
          placeholder={type === 'ai_review' ? 'Why? e.g. "SQL is stronger than the score shows: portfolio project with joins and window functions."'
                                            : 'e.g. Discussed internship options; agreed to finish the Power BI course by December.'}
          style={{ width: '100%', boxSizing: 'border-box', padding: '9px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', fontFamily: 'inherit', resize: 'vertical' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
          <span style={{ fontSize: '11px', color: C.muted }}>{body.length} / 2000</span>
          <button style={btn(true)} disabled={busy} onClick={save}>{busy ? 'Saving…' : 'Add note'}</button>
        </div>
      </div>

      {notes.length === 0 ? <div style={muted}>No notes yet.</div> : notes.map(n => (
        <div key={n.note_id} style={{ padding: '10px 0', borderTop: '1px solid #f0f1f5' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ fontSize: '12px', color: C.body, display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <b style={{ color: C.ink }}>{n.author_name || 'Former staff member'}</b>
              <span>{fmtDateTime(n.created_at)}{n.updated_at && n.updated_at !== n.created_at ? ' (edited)' : ''}</span>
              {n.note_type === 'ai_review' && n.ai_verdict && <Pill bg={VERDICT[n.ai_verdict].bg} color={VERDICT[n.ai_verdict].color}>{VERDICT[n.ai_verdict].label}</Pill>}
              {n.note_type === 'ai_review' && (
                <span style={{ color: C.muted }}>
                  {n.assessment_id ? `${n.assessment_role || 'Job description'} · ${num(n.assessment_score)}% · ${fmtDate(n.assessment_date)}` : 'assessment deleted'}
                </span>
              )}
            </div>
            {n.can_edit && editing?.note_id !== n.note_id && (
              <div className="no-print" style={{ display: 'flex', gap: '6px' }}>
                <button style={small()} onClick={() => setEditing({ note_id: n.note_id, body: n.body, ai_verdict: n.note_type === 'ai_review' ? n.ai_verdict : null })}>Edit</button>
                <button style={small(C.red)} onClick={() => remove(n)}>Delete</button>
              </div>
            )}
          </div>
          {editing?.note_id === n.note_id ? (
            <div className="no-print" style={{ marginTop: '8px' }}>
              {editing.ai_verdict && (
                <div style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                  {Object.keys(VERDICT).map(k => (
                    <button key={k} onClick={() => setEditing(ed => ({ ...ed, ai_verdict: k }))}
                      style={{ ...small(editing.ai_verdict === k ? VERDICT[k].color : C.body), borderColor: editing.ai_verdict === k ? VERDICT[k].color : C.line }}>
                      {k === 'agree' ? 'I agree' : 'I disagree'}
                    </button>
                  ))}
                </div>
              )}
              <textarea aria-label="Edit note" rows={3} maxLength={2000} value={editing.body} onChange={e => setEditing(ed => ({ ...ed, body: e.target.value }))}
                style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', fontFamily: 'inherit', resize: 'vertical' }} />
              <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                <button style={{ ...btn(true), padding: '5px 12px', fontSize: '12px' }} disabled={busy} onClick={saveEdit}>Save</button>
                <button style={{ ...btn(false), padding: '5px 12px', fontSize: '12px' }} onClick={() => setEditing(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: C.ink, marginTop: '4px', whiteSpace: 'pre-wrap', overflowWrap: 'break-word' }}>{n.body}</div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function AdvisorStudentDetail() {
  const { userId } = useParams()
  const navigate   = useNavigate()
  const location   = useLocation()
  const [data, setData]       = useState(null)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    advisorAPI.getStudent(userId)
      .then(res => { setData(res.data); setError('') })
      .catch(err => setError(err.response?.status === 404
        ? 'This student does not exist, is not in your courses, or has not created a profile yet.'
        : 'Could not load this student.'))
      .finally(() => setLoading(false))
  }, [userId])

  const reloadNotes = () => advisorAPI.notes(userId).then(r => setData(d => ({ ...d, notes: r.data }))).catch(() => {})

  const downloadCv = async () => {
    try {
      const r = await advisorAPI.downloadCv(userId)
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url
      a.download = data.cv.file_name
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Could not download the CV.')
    }
  }

  const back = (
    <button className="no-print" onClick={() => navigate('/', { state: { tab: location.state?.tab || 'students', course: location.state?.course || '' } })}
      style={{ border: 'none', background: 'none', color: C.blue, fontSize: '13px', fontWeight: '600', cursor: 'pointer', padding: 0, marginBottom: '14px' }}>
      ← Back to dashboard
    </button>
  )

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>
  if (!data) return (
    <div style={{ padding: '28px 32px' }}>
      {back}
      <div role="alert" style={{ ...card, color: C.red }}>{error}</div>
    </div>
  )

  const { student, assessment, skills, skill_gaps, history, projects, certifications, progress, cv, notes = [], experiences = [] } = data
  const score  = num(assessment?.readiness_score)
  const groups = ['strong', 'developing', 'gap'].map(k => ({ key: k, items: skill_gaps.filter(g => g.match_status === k) }))
  const done   = progress.filter(p => p.status === 'completed').length
  const latestReview = notes.find(n => n.note_type === 'ai_review' && assessment && n.assessment_id === assessment.assessment_id)

  // Readiness over time: one line, labelled with the role assessed each time
  const chart = history.map(h => ({ date: fmtDate(h.created_at), score: num(h.readiness_score), role: h.role_name || 'Job description' }))

  return (
    <div className="report-sheet" style={{ padding: '28px 32px' }}>
      <style>{PRINT_CSS}</style>
      {back}
      {error && <div role="alert" className="no-print" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>{student.full_name}</div>
          <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
            Student ID <span style={{ fontFamily: 'Consolas, monospace' }}>{student.student_number}</span> · {courseLabel(student.course)} · {student.email}
          </div>
          <div style={{ marginTop: '8px' }}>
            <Pill bg={student.is_complete ? '#dcfce7' : '#fef3c7'} color={student.is_complete ? C.green : C.amber}>
              {student.is_complete ? 'Profile complete' : 'Profile incomplete'}
            </Pill>
          </div>
        </div>
        <div className="no-print" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {cv ? (
            <button style={btn(false)} onClick={downloadCv} title={`${cv.file_name}, uploaded ${fmtDate(cv.uploaded_at)}`}>Download CV</button>
          ) : <span style={{ fontSize: '12px', color: C.muted, alignSelf: 'center' }}>No CV uploaded</span>}
          <button style={btn(false)} onClick={() => document.getElementById('advisor-notes')?.scrollIntoView({ behavior: 'smooth' })}>
            Notes ({notes.length})
          </button>
          <button style={btn(true)} onClick={() => window.print()}>Print report</button>
        </div>
      </div>

      <DecisionNotice compact />

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {[
          { label: 'Latest Readiness', value: score == null ? '—' : `${score}%`, color: scoreColor(score) },
          { label: 'Assessments',      value: history.length,                    color: C.blue },
          { label: 'Skills Listed',    value: skills.length,                     color: C.ink },
          { label: 'Activities Done',  value: `${done} / ${progress.length}`,    color: C.green },
        ].map(s => (
          <div key={s.label} className="report-card" style={{ ...card, marginBottom: 0, padding: '18px 20px' }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: s.color, marginTop: '4px', lineHeight: 1.1 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        {/* Profile */}
        <div className="report-card" style={card}>
          <div style={heading}>Profile</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <Field label="Programme" value={student.programme} />
            <Field label="University" value={student.university} />
            <Field label="Year of Study" value={student.year_of_study && `Year ${student.year_of_study}`} />
            <Field label="Expected Graduation" value={student.expected_graduation} />
            <Field label="GPA / CGPA" value={(student.gpa != null || student.cgpa != null) && `${student.gpa ?? '—'} / ${student.cgpa ?? '—'}`} />
            <Field label="Results Updated" value={student.results_updated_at && fmtDate(student.results_updated_at)} />
            <Field label="Target Role" value={student.target_role} />
            <Field label="Work Experience" value={experiences.length ? `${experiences.length} listed` : 'None listed'} />
            <div style={{ gridColumn: '1 / -1' }}><Field label="Career Interests" value={(student.career_interests || []).join(', ')} /></div>
          </div>
        </div>

        {/* Latest assessment */}
        <div className="report-card" style={card}>
          <div style={heading}>Latest Assessment</div>
          {!assessment ? (
            <div style={muted}>This student has not run an assessment yet.</div>
          ) : (
            <>
              <div style={{ fontSize: '12px', color: C.body, marginBottom: '12px' }}>
                {assessment.role_name || 'Pasted job description'} · {label(assessment.matching_method)} matching · {fmtDate(assessment.created_at)}
              </div>
              {DIMENSIONS.map(([key, name]) => {
                const v = num(assessment[key])
                return (
                  <div key={key} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: C.body, marginBottom: '3px' }}>
                      <span>{name}</span><span style={{ fontWeight: '600' }}>{v == null ? 'n/a' : `${v}%`}</span>
                    </div>
                    <div style={{ height: '6px', background: C.line, borderRadius: '99px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min(v ?? 0, 100)}%`, background: scoreColor(v), borderRadius: '99px' }} />
                    </div>
                  </div>
                )
              })}
              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #f0f1f5', fontSize: '12px', color: C.body }}>
                {latestReview
                  ? <>Your review: <Pill bg={VERDICT[latestReview.ai_verdict].bg} color={VERDICT[latestReview.ai_verdict].color}>{VERDICT[latestReview.ai_verdict].label}</Pill></>
                  : <span className="no-print">Not reviewed yet. <button onClick={() => document.getElementById('advisor-notes')?.scrollIntoView({ behavior: 'smooth' })}
                      style={{ border: 'none', background: 'none', color: C.blue, fontWeight: '600', cursor: 'pointer', padding: 0, fontSize: '12px' }}>Review this result</button></span>}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Skill gaps */}
      {assessment && (
        <div className="report-card" style={card}>
          <div style={heading}>Skills vs Requirements (Latest Assessment)</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
            {groups.map(g => (
              <div key={g.key} style={{ borderTop: `3px solid ${STATUS[g.key].color}`, paddingTop: '10px' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: STATUS[g.key].color, marginBottom: '8px' }}>
                  {STATUS[g.key].label} ({g.items.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {g.items.length === 0 && <span style={muted}>None</span>}
                  {g.items.map(s => (
                    <span key={s.skill_name} title={s.reason || undefined}>
                      <Pill bg={STATUS[g.key].bg} color={STATUS[g.key].color}>{s.skill_name}</Pill>
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="no-print" style={{ fontSize: '11px', color: C.muted, marginTop: '10px' }}>Hover over a skill to see why the matcher gave it this result.</div>
        </div>
      )}

      {/* Readiness over time */}
      <div className="report-card" style={card}>
        <div style={heading}>Readiness Over Time</div>
        {chart.length < 2 ? (
          <div style={muted}>At least two assessments are needed to show a trend.</div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v, _n, p) => [`${v}%`, p.payload.role]} />
              <Line type="monotone" dataKey="score" stroke={C.blue} strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        {/* Skills by category */}
        <div className="report-card" style={card}>
          <div style={heading}>Skills ({skills.length})</div>
          {skills.length === 0 ? <div style={muted}>No skills listed.</div> : CATEGORIES.map(([cat, name]) => {
            const list = skills.filter(s => s.category === cat)
            if (!list.length) return null
            return (
              <div key={cat} style={{ marginBottom: '10px' }}>
                <div style={{ fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', marginBottom: '5px' }}>{name}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {list.map(s => (
                    <span key={s.skill_name} style={{ fontSize: '12px', padding: '4px 9px', borderRadius: '8px', background: '#f5f6fa', color: C.ink }}>
                      {s.skill_name} <span style={{ color: C.muted }}>· {label(s.proficiency_level)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Projects & certifications */}
        <div className="report-card" style={card}>
          <div style={heading}>Projects ({projects.length}) & Certifications ({certifications.length})</div>
          {projects.length === 0 && certifications.length === 0 && <div style={muted}>None listed.</div>}
          {projects.map((p, i) => (
            <div key={`p${i}`} style={{ padding: '8px 0', borderBottom: '1px solid #f0f1f5' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>{p.project_title}</div>
              <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>
                {[label(p.project_type), p.year_completed, (p.technologies || []).join(', ')].filter(Boolean).join(' · ')}
              </div>
              {p.description && <div style={{ fontSize: '12px', color: C.body, marginTop: '3px' }}>{p.description}</div>}
              <EvidenceFiles files={p.files} />
            </div>
          ))}
          {certifications.map((c, i) => (
            <div key={`c${i}`} style={{ padding: '8px 0', borderBottom: '1px solid #f0f1f5' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>🎓 {c.cert_name}</div>
              <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>
                {[c.issuer, c.issue_date && `Issued ${fmtDate(c.issue_date)}`, c.expiry_date && `Expires ${fmtDate(c.expiry_date)}`].filter(Boolean).join(' · ')}
              </div>
              <EvidenceFiles files={c.files} />
            </div>
          ))}
        </div>
      </div>

      {/* Work experience */}
      <div className="report-card" style={card}>
        <div style={heading}>Work Experience ({experiences.length})</div>
        {experiences.length === 0 ? <div style={muted}>No work experience listed.</div> : experiences.map(x => (
          <div key={x.experience_id} style={{ padding: '8px 0', borderBottom: '1px solid #f0f1f5' }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>
              {x.job_title} <span style={{ fontWeight: '500', color: C.body }}>· {x.company}{x.location ? `, ${x.location}` : ''}</span>
            </div>
            <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>{experienceTypeLabel(x.experience_type)} · {period(x.start_date, x.end_date)}</div>
            {x.description && <div style={{ fontSize: '12px', color: C.body, marginTop: '3px', whiteSpace: 'pre-wrap' }}>{x.description}</div>}
          </div>
        ))}
      </div>

      {/* Development progress */}
      <div className="report-card" style={card}>
        <div style={heading}>Development Activities</div>
        {progress.length === 0 ? <div style={muted}>The student has not started any recommended activity yet.</div> : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '760px' }}>
              <thead>
                <tr>{['Activity', 'Type', 'Skill', 'Status', 'Started', 'Completed', 'Evidence'].map(h => (
                  <th key={h} style={{ textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', padding: '8px 10px', borderBottom: `1px solid ${C.line}`, whiteSpace: 'nowrap' }}>{h}</th>
                ))}</tr>
              </thead>
              <tbody>
                {progress.map((p, i) => {
                  const st = PROGRESS[p.status] || PROGRESS.saved
                  return (
                    <tr key={i}>
                      <td style={{ padding: '9px 10px', fontSize: '13px', color: C.ink }}>{p.resource_title}</td>
                      <td style={{ padding: '9px 10px', fontSize: '12px', color: C.body, textTransform: 'capitalize' }}>{p.resource_type}</td>
                      <td style={{ padding: '9px 10px', fontSize: '12px', color: C.body }}>{p.skill_name || '—'}</td>
                      <td style={{ padding: '9px 10px' }}><Pill bg={st.bg} color={st.color}>{st.label}</Pill></td>
                      <td style={{ padding: '9px 10px', fontSize: '12px', color: C.body, whiteSpace: 'nowrap' }}>{fmtDate(p.started_at)}</td>
                      <td style={{ padding: '9px 10px', fontSize: '12px', color: C.body, whiteSpace: 'nowrap' }}>{fmtDate(p.completed_at)}</td>
                      <td style={{ padding: '0 10px 6px', fontSize: '12px' }}><EvidenceFiles files={p.files || []} emptyText="—" /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Notes userId={userId} notes={notes} assessment={assessment} onChange={reloadNotes} />

      <div style={{ fontSize: '10px', color: C.muted, marginTop: '4px' }}>
        Report printed from SEAGAS on {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}.
        Scores come from automated skill matching on self-reported skills and support, not replace, the advisor&apos;s judgement.
      </div>
    </div>
  )
}
