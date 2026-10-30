// SEAGAS — Career Paths (FR-15): how well the student's current skills fit each job role of
// their course, what is missing, and a free resource for the most important missing skills.
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { careerAPI, studentAPI } from '../api/client'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef', blue: '#2d5be3',
            green: '#16a34a', amber: '#d97706', red: '#dc2626' }
const matchColor = (p) => p >= 70 ? C.green : p >= 40 ? C.amber : C.red
const IMPORTANCE = { required: { label: 'Required', color: C.red, bg: '#fee2e2' },
                     preferred: { label: 'Preferred', color: C.amber, bg: '#fef3c7' },
                     bonus: { label: 'Bonus', color: C.muted, bg: '#f1f5f9' } }
const chip = (bg, color) => ({ fontSize: '12px', padding: '3px 9px', borderRadius: '999px', background: bg, color, whiteSpace: 'nowrap' })

export default function CareerPaths() {
  const navigate = useNavigate()
  const [data, setData]       = useState(null)
  const [open, setOpen]       = useState(null)       // role whose skills are expanded
  const [error, setError]     = useState('')
  const [notice, setNotice]   = useState('')
  const [busy, setBusy]       = useState('')

  const load = () => careerAPI.paths().then(r => setData(r.data)).catch(() => setError('Could not load career paths.'))
  useEffect(() => { load() }, [])

  // Only the target role changes; the other profile fields are sent back as they are
  const setTarget = async (role) => {
    setBusy(role.role_id); setError(''); setNotice('')
    try {
      const p = (await studentAPI.getProfile().catch(() => ({ data: {} }))).data
      await studentAPI.updateProfile({
        university: p.university || null, gpa: p.gpa ?? null, cgpa: p.cgpa ?? null,
        expected_graduation: p.expected_graduation || null, year_of_study: p.year_of_study ?? null,
        career_interests: p.career_interests || [], target_role: role.role_name,
      })
      setNotice(`${role.role_name} is now your target role.`)
      await load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not change your target role.')
    } finally {
      setBusy('')
    }
  }

  if (error && !data) return <div style={{ padding: '40px', color: C.red }}>{error}</div>
  if (!data) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Career Paths</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '820px' }}>
          How well the {data.skill_count} skill{data.skill_count === 1 ? '' : 's'} on your profile fit each job role of your course.
          This is a quick guide based on which required, preferred and bonus skills you list; run a full assessment in Job Analysis
          for a readiness score that also looks at your levels, projects and experience.
        </div>
      </div>

      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}
      {notice && <div role="status" style={{ background: '#dcfce7', color: C.green, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{notice}</div>}

      {data.skill_count === 0 && (
        <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px', padding: '12px 14px', fontSize: '13px', color: '#92400e', marginBottom: '16px' }}>
          You have not added any skills yet, so every role shows 0%. <button onClick={() => navigate('/profile')}
            style={{ border: 'none', background: 'none', color: C.blue, fontWeight: '600', cursor: 'pointer', padding: 0, fontSize: '13px' }}>
            Add your skills (or upload your CV)</button> first.
        </div>
      )}

      {data.paths.length === 0 ? (
        <div style={{ color: C.muted, fontSize: '13px' }}>No job roles with skill requirements are available for your course yet.</div>
      ) : data.paths.map((p, i) => {
        const expanded = open === p.role_id
        return (
          <div key={p.role_id} style={{ background: '#fff', border: `1px solid ${p.is_target_role ? '#c7d4fb' : C.line}`, borderRadius: '12px',
                                        padding: '20px 24px', marginBottom: '14px', boxShadow: p.is_target_role ? '0 0 0 2px #eef2fd' : 'none' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <div style={{ flex: '1 1 320px', minWidth: 0 }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '12px', color: C.muted, fontWeight: '700' }}>#{i + 1}</span>
                  <span style={{ fontSize: '18px', fontWeight: '700', color: C.ink }}>{p.role_name}</span>
                  {p.is_target_role && <span style={chip('#eef2fd', C.blue)}>Your target role</span>}
                </div>
                {p.description && <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>{p.description}</div>}
                <div style={{ fontSize: '12px', color: C.muted, marginTop: '6px' }}>
                  Required skills {p.required.have}/{p.required.total} · Preferred {p.preferred.have}/{p.preferred.total} · Bonus {p.bonus.have}/{p.bonus.total}
                  {p.latest_assessment && <> · Last assessed {p.latest_assessment.score}% on {new Date(p.latest_assessment.date).toLocaleDateString('en-GB')}</>}
                </div>
              </div>
              <div style={{ textAlign: 'right', minWidth: '140px' }}>
                <div style={{ fontSize: '30px', fontWeight: '700', color: matchColor(p.match_pct), lineHeight: 1 }}>{p.match_pct}%</div>
                <div style={{ fontSize: '11px', color: C.muted }}>skill match</div>
              </div>
            </div>
            <div style={{ height: '8px', background: C.line, borderRadius: '99px', overflow: 'hidden', margin: '12px 0' }}>
              <div style={{ height: '100%', width: `${p.match_pct}%`, background: matchColor(p.match_pct), borderRadius: '99px' }} />
            </div>

            {p.next_steps.length > 0 && (
              <div style={{ background: '#fafbfc', border: `1px solid ${C.line}`, borderRadius: '10px', padding: '10px 12px', marginBottom: '10px' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: C.ink, marginBottom: '6px' }}>Next steps: required skills you do not list yet</div>
                {p.next_steps.map(s => (
                  <div key={s.skill_name} style={{ fontSize: '13px', color: C.body, padding: '3px 0' }}>
                    <b style={{ color: C.ink }}>{s.skill_name}</b>
                    {s.resource ? (
                      <> — <a href={s.resource.url} target="_blank" rel="noopener noreferrer" style={{ color: C.blue }}>{s.resource.title}</a>
                        <span style={{ color: C.muted }}>{[s.resource.provider, s.resource.cost, s.resource.duration_hours && `${s.resource.duration_hours} h`].filter(Boolean).length
                          ? ` · ${[s.resource.provider, s.resource.cost, s.resource.duration_hours && `${s.resource.duration_hours} h`].filter(Boolean).join(' · ')}` : ''}</span></>
                    ) : <span style={{ color: C.muted }}> — no learning resource listed yet</span>}
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <button onClick={() => setOpen(expanded ? null : p.role_id)}
                style={{ padding: '7px 12px', fontSize: '12px', fontWeight: '600', border: `1px solid ${C.line}`, borderRadius: '8px', background: '#fff', color: C.body, cursor: 'pointer' }}>
                {expanded ? 'Hide skills' : `Show all skills (${p.matched_skills.length + p.missing_skills.length})`}
              </button>
              <button onClick={() => navigate('/job-analysis', { state: { roleId: p.role_id } })}
                style={{ padding: '7px 12px', fontSize: '12px', fontWeight: '600', border: 'none', borderRadius: '8px', background: C.blue, color: '#fff', cursor: 'pointer' }}>
                Assess me against this role
              </button>
              {!p.is_target_role && (
                <button onClick={() => setTarget(p)} disabled={busy === p.role_id}
                  style={{ padding: '7px 12px', fontSize: '12px', fontWeight: '600', border: `1px solid ${C.line}`, borderRadius: '8px', background: '#fff', color: C.blue, cursor: 'pointer' }}>
                  {busy === p.role_id ? 'Saving…' : 'Make this my target role'}
                </button>
              )}
            </div>

            {expanded && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginTop: '14px' }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '700', color: C.green, marginBottom: '6px' }}>You have ({p.matched_skills.length})</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {p.matched_skills.length === 0 && <span style={{ fontSize: '12px', color: C.muted }}>None yet</span>}
                    {p.matched_skills.map(s => <span key={s} style={chip('#dcfce7', C.green)}>{s}</span>)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '700', color: C.red, marginBottom: '6px' }}>Missing ({p.missing_skills.length})</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {p.missing_skills.length === 0 && <span style={{ fontSize: '12px', color: C.muted }}>Nothing missing</span>}
                    {p.missing_skills.map(s => (
                      <span key={s.skill_name} title={IMPORTANCE[s.importance].label} style={chip(IMPORTANCE[s.importance].bg, IMPORTANCE[s.importance].color)}>
                        {s.skill_name}
                      </span>
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: C.muted, marginTop: '6px' }}>Red: required · Amber: preferred · Grey: bonus</div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
