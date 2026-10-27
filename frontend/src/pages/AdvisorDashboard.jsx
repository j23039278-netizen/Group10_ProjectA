// SEAGAS — Advisor Dashboard
import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { advisorAPI } from '../api/advisor'
import { COURSES, courseLabel } from '../utils/courses'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// The student list can hold thousands of rows; only this many are drawn at once
const PAGE_SIZE = 100

export default function AdvisorDashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const [overview,  setOverview]  = useState(null)
  const [skillGaps, setSkillGaps] = useState([])
  const [students,  setStudents]  = useState([])
  // "Back to students" on the detail page returns to this tab
  const [tab,       setTab]       = useState(location.state?.tab || 'overview')
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [status,    setStatus]    = useState('')
  // One course for every tab ('' = all courses); kept when coming back from a student
  const [course,    setCourse]    = useState(location.state?.course || '')
  const [shownRows, setShownRows] = useState(PAGE_SIZE)

  useEffect(() => {
    advisorAPI.students().then(r => setStudents(r.data)).catch(console.error)
  }, [])

  // The overview numbers and the skill gaps are worked out on the server per course
  useEffect(() => {
    let current = true
    Promise.all([advisorAPI.overview(course), advisorAPI.skillGaps(course)])
      .then(([ovRes, sgRes]) => {
        if (!current) return
        setOverview(ovRes.data)
        setSkillGaps(sgRes.data)
      })
      .catch(console.error)
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [course])

  // A score of 0 is a real result, so only null means "not assessed"
  const scoreColor = (s) => {
    if (s == null) return '#8b92a8'
    return s >= 70 ? '#16a34a' : s >= 50 ? '#d97706' : '#dc2626'
  }

  const statusBadge = (score) => {
    if (score == null) return { key: 'none',       label: 'No Assessment', bg: '#f5f6fa', color: '#8b92a8' }
    if (score >= 70)   return { key: 'on_track',   label: 'On Track',      bg: '#dcfce7', color: '#16a34a' }
    if (score >= 40)   return { key: 'developing', label: 'Developing',    bg: '#fef3c7', color: '#d97706' }
    return { key: 'at_risk', label: 'At Risk', bg: '#fee2e2', color: '#dc2626' }
  }

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  const cohortName = course ? `${courseLabel(course)} Students` : 'All Students'
  const noGapsText = course === 'BUSINESS'
    ? 'No assessment data yet. Business roles do not have their skills yet, so Business students cannot be assessed.'
    : 'No assessment data yet.'

  const q = search.trim().toLowerCase()
  const filteredStudents = students.filter(s =>
    (!course || s.course === course) &&
    (!status || statusBadge(s.latest_score == null ? null : parseFloat(s.latest_score)).key === status) &&
    (!q || [s.full_name, s.email, s.student_number, s.programme, s.target_role].some(v => (v || '').toLowerCase().includes(q)))
  )

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

      {/* Course: every tab shows only Computer Science, Business or ICT students */}
      <div role="tablist" aria-label="Course" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
        {[{ id: '', label: 'All courses' }, ...COURSES].map(c => {
          const active = course === c.id
          const n = c.id ? students.filter(s => s.course === c.id).length : students.length
          return (
            <button key={c.id || 'all'} role="tab" aria-selected={active}
              onClick={() => { setCourse(c.id); setShownRows(PAGE_SIZE) }}
              style={{ padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                       background: active ? '#2d5be3' : '#fff', color: active ? '#fff' : '#4a5168',
                       border: `1.5px solid ${active ? '#2d5be3' : '#e4e6ef'}` }}>
              {c.label} ({n})
            </button>
          )
        })}
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
              Top Skill Gaps — {cohortName}
            </div>
            {chartData.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#8b92a8' }}>
                {noGapsText}
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
            Skill Gap Report — {cohortName}
          </div>
          {skillGaps.length === 0 ? (
            <div style={{ color: '#8b92a8', textAlign: 'center', padding: '40px' }}>{noGapsText}</div>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Student List ({filteredStudents.length}{filteredStudents.length !== students.length ? ` of ${students.length}` : ''})
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <input type="search" aria-label="Search students" placeholder="Search name, student ID, email, programme or role"
                value={search} onChange={e => { setSearch(e.target.value); setShownRows(PAGE_SIZE) }}
                style={{ width: '280px', maxWidth: '100%', padding: '8px 11px', fontSize: '13px', border: '1px solid #e4e6ef', borderRadius: '8px', outline: 'none' }} />
              <select aria-label="Filter by status" value={status} onChange={e => { setStatus(e.target.value); setShownRows(PAGE_SIZE) }}
                style={{ padding: '8px 11px', fontSize: '13px', border: '1px solid #e4e6ef', borderRadius: '8px', background: '#fff' }}>
                <option value="">All statuses</option>
                <option value="on_track">On Track</option>
                <option value="developing">Developing</option>
                <option value="at_risk">At Risk</option>
                <option value="none">No Assessment</option>
              </select>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: '#8b92a8', marginBottom: '10px' }}>Click a student to open their full record.</div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Name', 'Student ID', 'Course', 'Programme', 'Target Role', 'Readiness', 'Status'].map(h => (
                  <th key={h} style={{ textAlign: 'left', fontSize: '11px', fontWeight: '700', color: '#8b92a8', textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: '1px solid #e4e6ef' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredStudents.length === 0 && (
                <tr><td colSpan={7} style={{ padding: '32px', textAlign: 'center', fontSize: '13px', color: '#8b92a8' }}>No students match.</td></tr>
              )}
              {filteredStudents.slice(0, shownRows).map((s, i) => {
                const score = s.latest_score == null ? null : parseFloat(s.latest_score)
                const badge = statusBadge(score)
                const open  = () => navigate(`/students/${s.user_id}`, { state: { course } })
                return (
                  <tr key={s.user_id} onClick={open} tabIndex={0}
                    onKeyDown={e => { if (e.key === 'Enter') open() }}
                    style={{ background: i % 2 === 0 ? '#f5f6fa' : '#fff', cursor: 'pointer' }}>
                    <td style={{ padding: '10px 12px', fontSize: '13px', fontWeight: '500', color: '#2d5be3' }}>{s.full_name}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168', fontFamily: 'Consolas, monospace' }}>{s.student_number || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168', whiteSpace: 'nowrap' }}>{courseLabel(s.course)}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168' }}>{s.programme || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: '12px', color: '#4a5168' }}>{s.target_role || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: '14px', fontWeight: '700', color: scoreColor(score) }}>
                      {score == null ? '—' : `${score}%`}
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
          {filteredStudents.length > shownRows && (
            <div style={{ textAlign: 'center', marginTop: '14px' }}>
              <button onClick={() => setShownRows(n => n + PAGE_SIZE)}
                style={{ padding: '8px 16px', fontSize: '13px', fontWeight: '600', border: '1px solid #e4e6ef', borderRadius: '8px', background: '#fff', color: '#4a5168', cursor: 'pointer' }}>
                Show more ({filteredStudents.length - shownRows} left)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}