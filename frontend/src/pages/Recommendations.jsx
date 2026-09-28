// SEAGAS — Recommendations Page
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { assessAPI } from '../api/client'

export default function Recommendations() {
  const location = useLocation()
  const [recs,    setRecs]    = useState([])
  const [history, setHistory] = useState([])
  const [selId,   setSelId]   = useState(location.state?.assessmentId || '')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    assessAPI.history().then(r => {
      setHistory(r.data)
      const id = location.state?.assessmentId || (r.data[0]?.assessment_id || '')
      setSelId(id)
      if (id) loadRecs(id)
      else setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const loadRecs = async (id) => {
    setLoading(true)
    try {
      const res = await assessAPI.getRecs(id)
      setRecs(res.data.recommendations)
    } catch {}
    finally { setLoading(false) }
  }

  const typeIcon = {
    course:        '📚',
    certification: '🏆',
    project:       '🛠️',
    workshop:      '🎓',
    competition:   '🏅',
    internship:    '💼',
  }

  const typeColor = {
    course:        { bg: '#fef3c7', color: '#d97706' },
    certification: { bg: '#eef2fd', color: '#2d5be3' },
    project:       { bg: '#dcfce7', color: '#16a34a' },
    workshop:      { bg: '#ede9fe', color: '#7c3aed' },
    competition:   { bg: '#fce7f3', color: '#db2777' },
    internship:    { bg: '#f0fdf4', color: '#15803d' },
  }

  const gapColor = {
    gap:        { bg: '#fee2e2', color: '#dc2626' },
    developing: { bg: '#fef3c7', color: '#d97706' },
  }

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Personalised Recommendations</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          Activities to close your skill gaps
        </div>
      </div>

      {/* Assessment Selector */}
      {history.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '16px 24px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5168' }}>Assessment:</label>
          <select value={selId} onChange={e => { setSelId(e.target.value); loadRecs(e.target.value) }}
            style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
            {history.map(h => (
              <option key={h.assessment_id} value={h.assessment_id}>
                {h.role_name || 'Custom JD'} — {h.readiness_score}% — {new Date(h.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
        </div>
      )}

      {recs.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '80px', color: '#8b92a8' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>💡</div>
          <div>No recommendations yet. Run an assessment first.</div>
        </div>
      )}

      {recs.map((rec, i) => (
        <div key={i} style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '20px', marginBottom: '12px' }}>
          {/* Skill Gap Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <span style={{
              padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
              background: gapColor[rec.gap_type]?.bg || '#fee2e2',
              color: gapColor[rec.gap_type]?.color || '#dc2626',
            }}>
              {rec.gap_type === 'gap' ? '✖ Skill Gap' : '◆ Developing'}
            </span>
            <span style={{ fontSize: '15px', fontWeight: '700', color: '#1a1f2e' }}>{rec.skill_name}</span>
          </div>

          {/* Resources */}
          {rec.resources.length === 0 ? (
            <div style={{ fontSize: '13px', color: '#8b92a8', fontStyle: 'italic' }}>
              No specific resources available yet. Try searching online for {rec.skill_name} courses.
            </div>
          ) : (
            rec.resources.map((r, j) => (
              <div key={j} style={{
                display: 'flex', alignItems: 'flex-start', gap: '14px',
                padding: '14px', background: '#f5f6fa', borderRadius: '10px',
                marginBottom: j < rec.resources.length - 1 ? '10px' : '0'
              }}>
                {/* Icon */}
                <div style={{
                  width: '38px', height: '38px', borderRadius: '8px', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '18px',
                  background: typeColor[r.resource_type]?.bg || '#f5f6fa',
                }}>
                  {typeIcon[r.resource_type] || '📖'}
                </div>

                {/* Details */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e', marginBottom: '3px' }}>
                    {r.resource_title}
                  </div>
                  {r.description && (
                    <div style={{ fontSize: '12px', color: '#4a5168', marginBottom: '6px' }}>{r.description}</div>
                  )}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
                      background: typeColor[r.resource_type]?.bg || '#f5f6fa',
                      color: typeColor[r.resource_type]?.color || '#4a5168',
                    }}>
                      {r.resource_type}
                    </span>
                    {r.provider && (
                      <span style={{ fontSize: '11px', color: '#8b92a8' }}>📍 {r.provider}</span>
                    )}
                    {r.cost && (
                      <span style={{ fontSize: '11px', color: '#8b92a8' }}>💰 {r.cost}</span>
                    )}
                    {r.duration_hours && (
                      <span style={{ fontSize: '11px', color: '#8b92a8' }}>⏱ ~{r.duration_hours} hrs</span>
                    )}
                    {r.difficulty && (
                      <span style={{ fontSize: '11px', color: '#8b92a8', textTransform: 'capitalize' }}>
                        📊 {r.difficulty}
                      </span>
                    )}
                  </div>
                </div>

                {/* Link */}
                {r.url && (
                  <a href={r.url} target="_blank" rel="noreferrer" style={{
                    padding: '7px 14px', background: '#2d5be3', color: '#fff',
                    borderRadius: '7px', fontSize: '12px', fontWeight: '600',
                    textDecoration: 'none', flexShrink: 0, alignSelf: 'center'
                  }}>
                    Open →
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      ))}

      {/* Note */}
      {recs.length > 0 && (
        <div style={{ background: '#eef2fd', border: '1px solid #c7d7f8', borderRadius: '10px', padding: '14px 18px', marginTop: '8px' }}>
          <div style={{ fontSize: '12px', color: '#2d5be3', fontWeight: '600', marginBottom: '3px' }}>
            ℹ️ About these recommendations
          </div>
          <div style={{ fontSize: '12px', color: '#4a5168' }}>
            These are AI-assisted suggestions based on your skill gaps. Consult your academic advisor for personalised career guidance.
          </div>
        </div>
      )}
    </div>
  )
}