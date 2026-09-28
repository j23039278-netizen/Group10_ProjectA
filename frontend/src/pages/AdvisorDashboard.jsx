// SEAGAS — Advisor Dashboard
import { useState, useEffect } from 'react'
import { advisorAPI } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function AdvisorDashboard() {
  const [overview,  setOverview]  = useState(null)
  const [skillGaps, setSkillGaps] = useState([])
  const [students,  setStudents]  = useState([])
  const [tab,       setTab]       = useState('overview')
  const [loading,   setLoading]   = useState(true)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    try {
      const [ovRes, sgRes, stRes] = await Promise.all([
        advisorAPI.overview(),
        advisorAPI.skillGaps(),
        advisorAPI.students(),
      ])
      setOverview(ovRes.data)
      setSkillGaps(sgRes.data)
      setStudents(stRes.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (s) => {
    if (!s) return '#8b92a8'
    return s >= 70 ? '#16a34a' : s >= 50 ? '#d97706' : '#dc2626'
  }

  const statusBadge = (score) => {
    if (!score) return { label: 'No Assessment', bg: '#f5f6fa', color: '#8b92a8' }
    if (score >= 70) return { label: 'On Track',    bg: '#dcfce7', color: '#16a34a' }
    if (score >= 40) return { label: 'Developing',  bg: '#fef3c7', color: '#d97706' }
    return { label: 'At Risk', bg: '#fee2e2', color: '#dc2626' }
  }

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  const chartData = skillGaps.slice(0, 10).map(g => ({
    name: g.skill_name.length > 15 ? g.skill_name.slice(0, 15) + '…' : g.skill_name,
    'Gap %': parseFloat(g.gap_percentage) || 0,
  }))

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Advisor Dashboard</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          Cohort-level employability insights
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '2px solid #e4e6ef', marginBottom: '20px' }}>
        {['overview', 'skill gaps', 'students'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '10px 18px', fontSize: '13px',
            fontWeight: tab === t ? '600' : '500',
            color: tab === t ? '#2d5be3' : '#4a5168',
            border: 'none', background: 'none', cursor: 'pointer',
            borderBottom: `2px solid ${tab === t ? '#2d5be3' : 'transparent'}`,
            marginBottom: '-2px', textTransform: 'capitalize'
          }}>{t}</button>
        ))}
      </div>

      {/* TAB: Overview */}
      {tab === 'overview' && (
        <>
          {/* Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '16px', marginBottom: '16px' }}>
            {[
              { label: 'Total Students',    value: overview?.total_students     || 0, color: '#1a1f2e' },
              { label: 'Avg Readiness',     value: `${overview?.avg_readiness_score || 0}%`, color: '#d97706' },
              { label: 'Profiles Complete', value: overview?.profiles_complete   || 0, color: '#16a34a' },
              { label: 'Students at Risk',  value: overview?.students_at_risk    || 0, color: '#dc2626' },
            ].map((s, i) => (
              <div key={i} style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '20px' }}>
                <div style={{ fontSize: '11px', fontWeight: '600', color: '#8b92a8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {s.label}
                </div>
                <div style={{ fontSize: '32px', fontWeight: '700', color: s.color, margin: '4px 0', lineHeight: 1 }}>
                  {s.value}
                </div>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Top Skill Gaps Across Cohort
            </div>
            {chartData.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#8b92a8' }}>
                No assessment data yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Students with Gap']} />
                  <Bar dataKey="Gap %" fill="#dc2626" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}

      {/* TAB: Skill Gaps */}
      {tab === 'skill gaps' && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Skill Gap Report — All Students
          </div>
          {skillGaps.length === 0 ? (
            <div style={{ color: '#8b92a8', textAlign: 'center', padding: '40px' }}>No data yet.</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Skill', 'Category', 'Gap %', 'Gap Count', 'Developing', 'Strong'].map(h => (
                    <th key={h} style={{ textAlign: 'left', fontSize: '11px', fontWeight: '700', color: '#8b92a8', textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: '1px solid #e4e6ef' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {skillGaps.map((g, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#f5f6fa' : '#fff' }}>
                    <td style={{ padding: '10px 12px', fontSize: '13px', fontWeight: '500', color: '#1a1f2e' }}>{g.skill_name}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168' }}>{g.category}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, height: '6px', background: '#e4e6ef', borderRadius: '99px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${g.gap_percentage}%`, background: g.gap_percentage > 60 ? '#dc2626' : g.gap_percentage > 30 ? '#d97706' : '#16a34a', borderRadius: '99px' }} />
                        </div>
                        <span style={{ fontSize: '12px', fontWeight: '700', color: g.gap_percentage > 60 ? '#dc2626' : g.gap_percentage > 30 ? '#d97706' : '#16a34a', width: '36px' }}>
                          {g.gap_percentage}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#dc2626', fontWeight: '600' }}>{g.gap_count}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#d97706', fontWeight: '600' }}>{g.developing_count}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#16a34a', fontWeight: '600' }}>{g.strong_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* TAB: Students */}
      {tab === 'students' && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Student List ({students.length})
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Name', 'Programme', 'Target Role', 'Readiness', 'Status'].map(h => (
                  <th key={h} style={{ textAlign: 'left', fontSize: '11px', fontWeight: '700', color: '#8b92a8', textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: '1px solid #e4e6ef' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {students.map((s, i) => {
                const badge = statusBadge(s.latest_score)
                return (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#f5f6fa' : '#fff' }}>
                    <td style={{ padding: '10px 12px', fontSize: '13px', fontWeight: '500', color: '#1a1f2e' }}>{s.full_name}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168' }}>{s.programme || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168' }}>{s.target_role || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: '14px', fontWeight: '700', color: scoreColor(s.latest_score) }}>
                      {s.latest_score ? `${s.latest_score}%` : '—'}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: badge.bg, color: badge.color }}>
                        {badge.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}