// SEAGAS — Job Analysis Page
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { jobsAPI, assessAPI } from '../api/client'

export default function JobAnalysis() {
  const navigate = useNavigate()
  const [roles,     setRoles]     = useState([])
  const [mode,      setMode]      = useState('template') // 'template' | 'custom'
  const [selRole,   setSelRole]   = useState('')
  const [jdText,    setJdText]    = useState('')
  const [jdTitle,   setJdTitle]   = useState('')
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState('')

  useEffect(() => {
    jobsAPI.getRoles().then(r => setRoles(r.data)).catch(() => {})
  }, [])

  const runAssessment = async () => {
    setError('')
    setLoading(true)
    setResult(null)
    try {
      let payload = {}

      if (mode === 'template') {
        if (!selRole) { setError('Please select a job role.'); setLoading(false); return }
        payload = { role_id: selRole, matching_method: 'semantic' }
      } else {
        if (jdText.trim().length < 50) { setError('Job description must be at least 50 characters.'); setLoading(false); return }
        // Submit JD first
        const jdRes = await jobsAPI.submitJD({ title: jdTitle, raw_text: jdText })
        const jdId  = jdRes.data.jd_id
        // Trigger NLP
        await jobsAPI.analyseJD(jdId)
        payload = { jd_id: jdId, matching_method: 'semantic' }
      }

      // Run assessment
      const res = await assessAPI.run(payload)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Error running assessment. Make sure your profile has skills added.')
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (s) => s >= 70 ? '#16a34a' : s >= 50 ? '#d97706' : '#dc2626'
  const statusColor = { strong: '#16a34a', developing: '#d97706', gap: '#dc2626' }
  const statusBg    = { strong: '#dcfce7', developing: '#fef3c7', gap: '#fee2e2' }

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Job Description Analysis</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          Select a job role template or paste a job description to analyse your match
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

        {/* Input Panel */}
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Input
          </div>

          {/* Mode Toggle */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            {[
              { id: 'template', label: '📋 Use Role Template' },
              { id: 'custom',   label: '📝 Paste Job Description' },
            ].map(m => (
              <button key={m.id} onClick={() => setMode(m.id)} style={{
                flex: 1, padding: '9px', border: `2px solid ${mode === m.id ? '#2d5be3' : '#e4e6ef'}`,
                borderRadius: '8px', background: mode === m.id ? '#eef2fd' : '#f5f6fa',
                color: mode === m.id ? '#2d5be3' : '#4a5168',
                fontSize: '12px', fontWeight: '600', cursor: 'pointer'
              }}>{m.label}</button>
            ))}
          </div>

          {/* Template Mode */}
          {mode === 'template' && (
            <div>
              <label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '6px' }}>
                Select Target Role
              </label>
              <select value={selRole} onChange={e => setSelRole(e.target.value)} style={{
                width: '100%', padding: '10px 12px', border: '1.5px solid #e4e6ef',
                borderRadius: '8px', fontSize: '13px', background: '#f5f6fa', marginBottom: '12px'
              }}>
                <option value="">Choose a job role...</option>
                {roles.map(r => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
              </select>
              {selRole && (
                <div style={{ background: '#eef2fd', borderRadius: '8px', padding: '12px', fontSize: '12px', color: '#2d5be3' }}>
                  ℹ️ This will compare your skills against the pre-built skill requirements for this role.
                </div>
              )}
            </div>
          )}

          {/* Custom JD Mode */}
          {mode === 'custom' && (
            <div>
              <label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '6px' }}>
                Job Title (optional)
              </label>
              <input value={jdTitle} onChange={e => setJdTitle(e.target.value)}
                placeholder="e.g. Junior Data Analyst"
                style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa', marginBottom: '12px', boxSizing: 'border-box' }}
              />
              <label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '6px' }}>
                Job Description Text *
              </label>
              <textarea value={jdText} onChange={e => setJdText(e.target.value)}
                placeholder="Paste the full job description here (minimum 50 characters)..."
                rows={8}
                style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa', resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' }}
              />
              <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '4px' }}>
                {jdText.length} characters {jdText.length < 50 && '(minimum 50)'}
              </div>
            </div>
          )}

          {error && (
            <div style={{ background: '#fee2e2', color: '#dc2626', padding: '10px', borderRadius: '8px', fontSize: '13px', marginTop: '12px' }}>
              {error}
            </div>
          )}

          <button onClick={runAssessment} disabled={loading} style={{
            width: '100%', marginTop: '16px', padding: '12px',
            background: loading ? '#93a8f0' : '#2d5be3',
            color: '#fff', border: 'none', borderRadius: '8px',
            fontSize: '14px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer'
          }}>
            {loading ? '⏳ Analysing...' : '⚡ Run Assessment'}
          </button>
        </div>

        {/* Result Panel */}
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Results
          </div>

          {!result && !loading && (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#8b92a8' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>🔍</div>
              <div>Select a role or paste a JD and click Run Assessment</div>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#8b92a8' }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>⏳</div>
              <div>Analysing your skills...</div>
            </div>
          )}

          {result && (
            <>
              {/* Readiness Score */}
              <div style={{
                background: '#eef2fd', border: '1px solid #c7d7f8',
                borderRadius: '12px', padding: '18px',
                display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px'
              }}>
                <div style={{ fontSize: '40px', fontWeight: '800', color: scoreColor(result.readiness_score) }}>
                  {result.readiness_score}%
                </div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: '700', color: '#2d5be3' }}>Job Readiness Score</div>
                  <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>
                    Decision-support indicator — not a hiring prediction
                  </div>
                  <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '4px' }}>
                    ✅ {result.skill_summary.strong} Strong &nbsp;
                    ◆ {result.skill_summary.developing} Developing &nbsp;
                    ✖ {result.skill_summary.gaps} Gaps
                  </div>
                </div>
              </div>

              {/* Skill Results */}
              <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
                {result.match_results.map((mr, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 0', borderBottom: i < result.match_results.length-1 ? '1px solid #e4e6ef' : 'none'
                  }}>
                    <div style={{ fontSize: '13px', fontWeight: '500', color: '#1a1f2e' }}>{mr.skill_name}</div>
                    <span style={{
                      padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
                      background: statusBg[mr.match_status],
                      color: statusColor[mr.match_status]
                    }}>
                      {mr.match_status === 'strong' ? '✅ Strong' : mr.match_status === 'developing' ? '◆ Developing' : '✖ Gap'}
                    </span>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button onClick={() => navigate('/skill-gap', { state: { assessmentId: result.assessment_id }})}
                  style={{ flex: 1, padding: '10px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
                  View Skill Gap →
                </button>
                <button onClick={() => navigate('/recommendations', { state: { assessmentId: result.assessment_id }})}
                  style={{ flex: 1, padding: '10px', background: '#f5f6fa', color: '#1a1f2e', border: '1px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
                  View Recommendations →
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}