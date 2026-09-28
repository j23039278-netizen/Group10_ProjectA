// SEAGAS — Student Dashboard
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { assessAPI, studentAPI } from '../api/client'

export default function Dashboard({ onLogout }) {
  const navigate = useNavigate()
  const [profile,    setProfile]    = useState(null)
  const [history,    setHistory]    = useState([])
  const [latest,     setLatest]     = useState(null)
  const [loading,    setLoading]    = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [profileRes, historyRes] = await Promise.all([
        studentAPI.getProfile(),
        assessAPI.history(),
      ])
      setProfile(profileRes.data)
      setHistory(historyRes.data)
      if (historyRes.data.length > 0) setLatest(historyRes.data[0])
    } catch (err) {
      // Profile might not exist yet
    } finally {
      setLoading(false)
    }
  }

  if (loading) return (
    <div style={{ padding: '40px', textAlign: 'center', color: '#8b92a8' }}>
      Loading...
    </div>
  )

  const score = latest?.readiness_score || 0
  const scoreColor = score >= 70 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626'

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>
          Good day 👋
        </div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          {profile?.target_role
            ? `Your employability snapshot for ${profile.target_role}`
            : 'Complete your profile to get started'}
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px', marginBottom: '16px' }}>
        {[
          { label: 'Job Readiness',  value: `${score}%`,             color: scoreColor },
          { label: 'Assessments',    value: history.length,           color: '#2d5be3' },
          { label: 'Target Role',    value: profile?.target_role || '—', color: '#1a1f2e', small: true },
          { label: 'GPA',            value: profile?.gpa || '—',     color: '#1a1f2e' },
        ].map((s, i) => (
          <div key={i} style={{
            background: '#fff', border: '1px solid #e4e6ef',
            borderRadius: '12px', padding: '20px'
          }}>
            <div style={{ fontSize: '11px', fontWeight: '600', color: '#8b92a8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {s.label}
            </div>
            <div style={{ fontSize: s.small ? '18px' : '30px', fontWeight: '700', color: s.color, margin: '4px 0', lineHeight: 1 }}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

        {/* Score Breakdown */}
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Employability Profile
          </div>
          {latest ? (
            [
              { label: 'Technical Skills',    val: latest.score_technical },
              { label: 'AI / Digital Skills', val: latest.score_ai_digital },
              { label: 'Analytical Skills',   val: latest.score_analytical },
              { label: 'Communication',       val: latest.score_communication },
              { label: 'Project Experience',  val: latest.score_project_exp },
              { label: 'Certification',       val: latest.score_certification },
              { label: 'Industry Experience', val: latest.score_industry_exp },
            ].map((item, i) => (
              <div key={i} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: '500', color: '#1a1f2e' }}>{item.label}</span>
                  <span style={{ fontWeight: '600', color: '#4a5168' }}>{item.val ?? 0}%</span>
                </div>
                <div style={{ height: '7px', background: '#e4e6ef', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: '99px',
                    width: `${item.val ?? 0}%`,
                    background: (item.val ?? 0) >= 70 ? '#16a34a' : (item.val ?? 0) >= 40 ? '#2d5be3' : '#dc2626',
                    transition: 'width .6s ease'
                  }} />
                </div>
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#8b92a8' }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>📊</div>
              <div>No assessment yet</div>
              <button onClick={() => navigate('/job-analysis')} style={{
                marginTop: '12px', padding: '8px 16px', background: '#2d5be3',
                color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '12px'
              }}>
                Run First Assessment →
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions + History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Quick Actions */}
          <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Quick Actions
            </div>
            {[
              { label: '📄 Analyse a Job Description', path: '/job-analysis', color: '#2d5be3' },
              { label: '👤 Update My Profile',         path: '/profile',      color: '#16a34a' },
              { label: '💡 View Recommendations',      path: '/recommendations', color: '#d97706' },
              { label: '🎯 View Skill Gaps',           path: '/skill-gap',    color: '#7c3aed' },
            ].map((a, i) => (
              <button key={i} onClick={() => navigate(a.path)} style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '10px 14px', marginBottom: '8px',
                background: '#f5f6fa', border: '1px solid #e4e6ef',
                borderRadius: '8px', cursor: 'pointer', fontSize: '13px',
                fontWeight: '500', color: '#1a1f2e',
              }}>
                {a.label}
              </button>
            ))}
          </div>

          {/* Assessment History */}
          <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Assessment History
            </div>
            {history.length === 0 ? (
              <div style={{ color: '#8b92a8', fontSize: '13px' }}>No assessments yet.</div>
            ) : (
              history.slice(0, 4).map((h, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 0', borderBottom: i < 3 ? '1px solid #e4e6ef' : 'none'
                }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '500', color: '#1a1f2e' }}>
                      {h.role_name || 'Custom JD'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#8b92a8' }}>
                      {new Date(h.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div style={{
                    fontSize: '16px', fontWeight: '700',
                    color: h.readiness_score >= 70 ? '#16a34a' : h.readiness_score >= 50 ? '#d97706' : '#dc2626'
                  }}>
                    {h.readiness_score}%
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}