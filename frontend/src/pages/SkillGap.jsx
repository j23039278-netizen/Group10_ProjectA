// SEAGAS — Skill Gap Analysis Page
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { assessAPI } from '../api/client'

export default function SkillGap() {
  const location     = useLocation()
  const [assessment, setAssessment] = useState(null)
  const [matches,    setMatches]    = useState([])
  const [history,    setHistory]    = useState([])
  const [selId,      setSelId]      = useState(location.state?.assessmentId || '')
  const [loading,    setLoading]    = useState(true)

  useEffect(() => {
    assessAPI.history().then(r => {
      setHistory(r.data)
      const id = location.state?.assessmentId || (r.data[0]?.assessment_id || '')
      setSelId(id)
      if (id) loadAssessment(id)
      else setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const loadAssessment = async (id) => {
    setLoading(true)
    try {
      const res = await assessAPI.get(id)
      setAssessment(res.data.assessment)
      setMatches(res.data.match_results)
    } catch {}
    finally { setLoading(false) }
  }

  const strong     = matches.filter(m => m.match_status === 'strong')
  const developing = matches.filter(m => m.match_status === 'developing')
  const gaps       = matches.filter(m => m.match_status === 'gap')

  const scoreColor = (s) => s >= 70 ? '#16a34a' : s >= 50 ? '#d97706' : '#dc2626'

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Skill Gap Analysis</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          Detailed breakdown of your skills vs job requirements
        </div>
      </div>

      {/* Assessment Selector */}
      {history.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '16px 24px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5168' }}>Assessment:</label>
          <select value={selId} onChange={e => { setSelId(e.target.value); loadAssessment(e.target.value) }}
            style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
            {history.map(h => (
              <option key={h.assessment_id} value={h.assessment_id}>
                {h.role_name || 'Custom JD'} — {h.readiness_score}% — {new Date(h.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
        </div>
      )}

      {!assessment && (
        <div style={{ textAlign: 'center', padding: '80px', color: '#8b92a8' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎯</div>
          <div>No assessment found. Run an assessment first from Job Analysis page.</div>
        </div>
      )}

      {assessment && (
        <>
          {/* Score Banner */}
          <div style={{
            background: '#eef2fd', border: '2px solid #2d5be3',
            borderRadius: '12px', padding: '18px 24px',
            display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '16px'
          }}>
            <div style={{ fontSize: '42px', fontWeight: '800', color: scoreColor(assessment.readiness_score) }}>
              {assessment.readiness_score}%
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '15px', fontWeight: '700', color: '#2d5be3' }}>Job Readiness Score</div>
              <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>
                Method: {assessment.matching_method} · {new Date(assessment.created_at).toLocaleDateString()}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '16px' }}>
              {[
                { label: 'Strong',     count: strong.length,     color: '#16a34a', bg: '#dcfce7' },
                { label: 'Developing', count: developing.length, color: '#d97706', bg: '#fef3c7' },
                { label: 'Gaps',       count: gaps.length,       color: '#dc2626', bg: '#fee2e2' },
              ].map((s, i) => (
                <div key={i} style={{ textAlign: 'center', background: s.bg, borderRadius: '10px', padding: '10px 16px' }}>
                  <div style={{ fontSize: '22px', fontWeight: '700', color: s.color }}>{s.count}</div>
                  <div style={{ fontSize: '11px', color: s.color, fontWeight: '600' }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 7-Dimension Scores */}
          <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              7-Dimension Employability Assessment
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              {[
                { label: 'Technical Skills',    val: assessment.score_technical },
                { label: 'AI / Digital Skills', val: assessment.score_ai_digital },
                { label: 'Analytical Skills',   val: assessment.score_analytical },
                { label: 'Communication',       val: assessment.score_communication },
                { label: 'Project Experience',  val: assessment.score_project_exp },
                { label: 'Certification',       val: assessment.score_certification },
                { label: 'Industry Experience', val: assessment.score_industry_exp },
              ].map((d, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: '500', color: '#1a1f2e' }}>{d.label}</span>
                    <span style={{ fontWeight: '700', color: '#4a5168' }}>{d.val ?? 0}%</span>
                  </div>
                  <div style={{ height: '7px', background: '#e4e6ef', borderRadius: '99px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', borderRadius: '99px', width: `${d.val ?? 0}%`,
                      background: (d.val ?? 0) >= 70 ? '#16a34a' : (d.val ?? 0) >= 40 ? '#2d5be3' : '#dc2626',
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skill Categories */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            {[
              { title: '✅ Strong Skills',     items: strong,     border: '#16a34a', bg: '#dcfce7', color: '#16a34a' },
              { title: '◆ Developing Skills', items: developing, border: '#d97706', bg: '#fef3c7', color: '#d97706' },
              { title: '✖ Skill Gaps',        items: gaps,       border: '#dc2626', bg: '#fee2e2', color: '#dc2626' },
            ].map((col, i) => (
              <div key={i} style={{
                background: '#fff', border: `1px solid #e4e6ef`,
                borderTop: `3px solid ${col.border}`,
                borderRadius: '12px', padding: '20px'
              }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: col.color, marginBottom: '12px' }}>
                  {col.title} ({col.items.length})
                </div>
                {col.items.length === 0
                  ? <div style={{ fontSize: '12px', color: '#8b92a8' }}>None</div>
                  : col.items.map((s, j) => (
                    <div key={j} style={{
                      padding: '6px 10px', borderRadius: '20px', fontSize: '12px',
                      fontWeight: '500', background: col.bg, color: col.color,
                      display: 'inline-block', margin: '3px'
                    }}>
                      {s.skill_name}
                    </div>
                  ))
                }
                {col.title.includes('Developing') && col.items.length > 0 && (
                  <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '10px' }}>
                    You have some evidence — needs further development.
                  </div>
                )}
                {col.title.includes('Gaps') && col.items.length > 0 && (
                  <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '10px' }}>
                    No evidence found in your profile.
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}