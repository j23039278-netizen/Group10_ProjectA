// SEAGAS — Advisor: one student's profile, latest assessment, skill gaps,
// readiness over time and development progress (FR-13). Read-only.
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { advisorAPI } from '../api/advisor'
import { label } from '../utils/labels'
import EvidenceFiles from '../components/EvidenceFiles'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef',
            blue: '#2d5be3', green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }
const muted   = { color: C.muted, fontSize: '13px' }

const DIMENSIONS = [
  ['score_technical',     'Technical Skills'],
  ['score_ai_digital',    'AI / Digital Skills'],
  ['score_analytical',    'Analytical Skills'],
  ['score_communication', 'Communication'],
  ['score_project_exp',   'Project Experience'],
  ['score_certification', 'Certification'],
  ['score_industry_exp',  'Industry Experience'],
]

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

const scoreColor = (s) => s == null ? C.muted : s >= 70 ? C.green : s >= 50 ? C.amber : C.red
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB') : '—'
const num = (v) => v == null ? null : parseFloat(v)

function Pill({ bg, color, children }) {
  return <span style={{ padding: '3px 9px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: bg, color, whiteSpace: 'nowrap' }}>{children}</span>
}

function Field({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.4px' }}>{label}</div>
      <div style={{ fontSize: '13px', color: C.ink, marginTop: '3px' }}>{value || '—'}</div>
    </div>
  )
}

export default function AdvisorStudentDetail() {
  const { userId } = useParams()
  const navigate   = useNavigate()
  const [data, setData]       = useState(null)
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    advisorAPI.getStudent(userId)
      .then(res => { setData(res.data); setError('') })
      .catch(err => setError(err.response?.status === 404
        ? 'This student does not exist or has not created a profile yet.'
        : 'Could not load this student.'))
      .finally(() => setLoading(false))
  }, [userId])

  const back = (
    <button onClick={() => navigate('/', { state: { tab: 'students' } })}
      style={{ border: 'none', background: 'none', color: C.blue, fontSize: '13px', fontWeight: '600', cursor: 'pointer', padding: 0, marginBottom: '14px' }}>
      ← Back to students
    </button>
  )

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>
  if (error) return (
    <div style={{ padding: '28px 32px' }}>
      {back}
      <div role="alert" style={{ ...card, color: C.red }}>{error}</div>
    </div>
  )

  const { student, assessment, skills, skill_gaps, history, projects, certifications, progress } = data
  const score  = num(assessment?.readiness_score)
  const groups = ['strong', 'developing', 'gap'].map(k => ({ key: k, items: skill_gaps.filter(g => g.match_status === k) }))
  const done   = progress.filter(p => p.status === 'completed').length

  // Readiness over time: one line, labelled with the role assessed each time
  const chart = history.map(h => ({
    date: fmtDate(h.created_at), score: num(h.readiness_score), role: h.role_name || 'Job description',
  }))

  return (
    <div style={{ padding: '28px 32px' }}>
      {back}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>{student.full_name}</div>
          <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
            Student ID {student.student_number} · {student.email} · {student.programme || 'No programme'}{student.year_of_study ? ` · Year ${student.year_of_study}` : ''}
          </div>
        </div>
        <Pill bg={student.is_complete ? '#dcfce7' : '#fef3c7'} color={student.is_complete ? C.green : C.amber}>
          {student.is_complete ? 'Profile complete' : 'Profile incomplete'}
        </Pill>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {[
          { label: 'Latest Readiness', value: score == null ? '—' : `${score}%`, color: scoreColor(score) },
          { label: 'Assessments',      value: history.length,                    color: C.blue },
          { label: 'Skills Listed',    value: skills.length,                     color: C.ink },
          { label: 'Activities Done',  value: `${done} / ${progress.length}`,    color: C.green },
        ].map(s => (
          <div key={s.label} style={{ ...card, marginBottom: 0, padding: '18px 20px' }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: s.color, marginTop: '4px', lineHeight: 1.1 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        {/* Profile */}
        <div style={card}>
          <div style={heading}>Profile</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <Field label="University" value={student.university} />
            <Field label="GPA" value={student.gpa} />
            <Field label="Target Role" value={student.target_role} />
            <Field label="Expected Graduation" value={student.expected_graduation} />
            <Field label="Internships" value={String(student.internship_count ?? 0)} />
            <Field label="Career Interests" value={(student.career_interests || []).join(', ')} />
          </div>
        </div>

        {/* Latest assessment */}
        <div style={card}>
          <div style={heading}>Latest Assessment</div>
          {!assessment ? (
            <div style={muted}>This student has not run an assessment yet.</div>
          ) : (
            <>
              <div style={{ fontSize: '12px', color: C.body, marginBottom: '12px' }}>
                {assessment.role_name || 'Pasted job description'} · {label(assessment.matching_method)} matching · {fmtDate(assessment.created_at)}
              </div>
              {DIMENSIONS.map(([key, label]) => {
                const v = num(assessment[key]) ?? 0
                return (
                  <div key={key} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: C.body, marginBottom: '3px' }}>
                      <span>{label}</span><span style={{ fontWeight: '600' }}>{v}%</span>
                    </div>
                    <div style={{ height: '6px', background: C.line, borderRadius: '99px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.min(v, 100)}%`, background: scoreColor(v), borderRadius: '99px' }} />
                    </div>
                  </div>
                )
              })}
            </>
          )}
        </div>
      </div>

      {/* Skill gaps */}
      {assessment && (
        <div style={card}>
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
        </div>
      )}

      {/* Readiness over time */}
      <div style={card}>
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
        {/* Skills */}
        <div style={card}>
          <div style={heading}>Skills ({skills.length})</div>
          {skills.length === 0 ? <div style={muted}>No skills listed.</div> : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {skills.map(s => (
                <span key={s.skill_name} style={{ fontSize: '12px', padding: '4px 9px', borderRadius: '8px', background: '#f5f6fa', color: C.ink }}>
                  {s.skill_name} <span style={{ color: C.muted }}>· {label(s.proficiency_level)}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Projects & certifications */}
        <div style={card}>
          <div style={heading}>Projects ({projects.length}) & Certifications ({certifications.length})</div>
          {projects.length === 0 && certifications.length === 0 && <div style={muted}>None listed.</div>}
          {projects.map((p, i) => (
            <div key={`p${i}`} style={{ padding: '8px 0', borderBottom: '1px solid #f0f1f5' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>{p.project_title}</div>
              <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>
                {[label(p.project_type), p.year_completed, (p.technologies || []).join(', ')].filter(Boolean).join(' · ')}
              </div>
              <EvidenceFiles files={p.files} />
            </div>
          ))}
          {certifications.map((c, i) => (
            <div key={`c${i}`} style={{ padding: '8px 0', borderBottom: '1px solid #f0f1f5' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>🎓 {c.cert_name}</div>
              <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>
                {[c.issuer, c.issue_date && `Issued ${fmtDate(c.issue_date)}`].filter(Boolean).join(' · ')}
              </div>
              <EvidenceFiles files={c.files} />
            </div>
          ))}
        </div>
      </div>

      {/* Development progress */}
      <div style={card}>
        <div style={heading}>Development Activities</div>
        {progress.length === 0 ? <div style={muted}>The student has not started any recommended activity yet.</div> : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '560px' }}>
              <thead>
                <tr>{['Activity', 'Type', 'Skill', 'Status', 'Completed'].map(h => (
                  <th key={h} style={{ textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', padding: '8px 10px', borderBottom: `1px solid ${C.line}` }}>{h}</th>
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
                      <td style={{ padding: '9px 10px', fontSize: '12px', color: C.body }}>{fmtDate(p.completed_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
