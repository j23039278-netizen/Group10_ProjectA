// SEAGAS — Advisor Dashboard: cohort overview, skill gaps, student list and learning progress
// for the courses the advisor looks after (Dean / Head of Programme). Every table can be
// exported as CSV. Scores are decision support: see DecisionNotice.
import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { advisorAPI } from '../api/advisor'
import { authAPI, jobsAPI } from '../api/client'
import { COURSES, courseLabel } from '../utils/courses'
import { downloadCsv, csvName } from '../utils/csv'
import DecisionNotice from '../components/DecisionNotice'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef', blue: '#2d5be3',
            green: '#16a34a', amber: '#d97706', red: '#dc2626', bg: '#f5f6fa' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '22px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, textTransform: 'uppercase', letterSpacing: '0.5px' }
const th      = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px',
                  padding: '10px 12px', borderBottom: `1px solid ${C.line}`, whiteSpace: 'nowrap', background: '#fff' }
const td      = { padding: '10px 12px', fontSize: '12px', color: C.body, borderBottom: '1px solid #f0f1f5' }
const input   = { padding: '8px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', background: '#fff', outline: 'none' }
const btn     = (primary) => ({ padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer', whiteSpace: 'nowrap',
                                border: primary ? 'none' : `1px solid ${C.line}`, background: primary ? C.blue : '#fff', color: primary ? '#fff' : C.body })

// The student list can hold thousands of rows; only this many are drawn at once
const PAGE_SIZE = 100
const TABS = [
  { id: 'overview',   label: 'Overview' },
  { id: 'skill gaps', label: 'Skill Gaps' },
  { id: 'students',   label: 'Students' },
  { id: 'progress',   label: 'Learning Progress' },
]

// Readiness bands (the same limits as the backend: 70 and 40). A score of 0 is a real result.
const STATUS = {
  on_track:      { label: 'On Track',      bg: '#dcfce7', color: C.green },
  developing:    { label: 'Developing',    bg: '#fef3c7', color: C.amber },
  needs_support: { label: 'Needs Support', bg: '#fee2e2', color: C.red },
  none:          { label: 'No Assessment', bg: C.bg,      color: C.muted },
}
const num = (v) => (v == null ? null : parseFloat(v))
const statusOf = (score) => score == null ? 'none' : score >= 70 ? 'on_track' : score >= 40 ? 'developing' : 'needs_support'
const scoreColor = (s) => s == null ? C.muted : s >= 70 ? C.green : s >= 40 ? C.amber : C.red
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB') : '—'
const pct = (n, total) => total ? Math.round((n / total) * 100) : 0

function Pill({ status }) {
  const s = STATUS[status]
  return <span style={{ padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: s.bg, color: s.color, whiteSpace: 'nowrap' }}>{s.label}</span>
}

function StatCard({ label, value, sub, color = C.ink }) {
  return (
    <div style={{ ...card, marginBottom: 0, padding: '18px 20px' }}>
      <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
      <div style={{ fontSize: '30px', fontWeight: '700', color, margin: '4px 0 2px', lineHeight: 1.1 }}>{value}</div>
      {sub && <div style={{ fontSize: '12px', color: C.muted }}>{sub}</div>}
    </div>
  )
}

function Empty({ children }) {
  return <div style={{ textAlign: 'center', padding: '36px', color: C.muted, fontSize: '13px' }}>{children}</div>
}

// A table header cell that sorts by its column
function SortTh({ label, k, sort, setSort, align }) {
  const active = sort.key === k
  return (
    <th style={{ ...th, textAlign: align || 'left', cursor: 'pointer', color: active ? C.blue : C.muted }}
      onClick={() => setSort(s => ({ key: k, dir: s.key === k && s.dir === 'asc' ? 'desc' : 'asc' }))}
      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
      {label} {active ? (sort.dir === 'asc' ? '▲' : '▼') : ''}
    </th>
  )
}

export default function AdvisorDashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  // "Back to students" on the detail page returns to the same tab and course
  const [tab, setTab]         = useState(location.state?.tab || 'overview')
  const [course, setCourse]   = useState(location.state?.course || '')
  const [me, setMe]           = useState(null)
  const [students, setStudents] = useState([])
  const [overview, setOverview] = useState(null)
  const [gaps, setGaps]         = useState([])          // course-wide, for the overview chart
  const [roles, setRoles]       = useState([])          // job roles with skills, for the skill-gap filter
  const [roleId, setRoleId]     = useState('')
  const [roleGaps, setRoleGaps] = useState(null)        // skill gaps of one assessed role
  const [progress, setProgress] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  // Student list filters and sorting
  const [search, setSearch]       = useState('')
  const [status, setStatus]       = useState('')
  const [programme, setProgramme] = useState('')
  const [target, setTarget]       = useState('')
  const [profileF, setProfileF]   = useState('')
  const [sort, setSort]           = useState({ key: 'full_name', dir: 'asc' })
  const [shownRows, setShownRows] = useState(PAGE_SIZE)

  useEffect(() => {
    advisorAPI.students().then(r => setStudents(r.data)).catch(() => setError('Could not load the student list.'))
    authAPI.me().then(r => setMe(r.data)).catch(() => {})
    jobsAPI.getRoles().then(r => setRoles(r.data.filter(x => x.skill_count > 0))).catch(() => {})
  }, [])

  // Overview figures and skill gaps are worked out on the server per course
  useEffect(() => {
    let current = true
    Promise.all([advisorAPI.overview(course), advisorAPI.skillGaps(course)])
      .then(([ov, sg]) => { if (current) { setOverview(ov.data); setGaps(sg.data); setError('') } })
      .catch(() => current && setError('Could not load the cohort figures.'))
      .finally(() => current && setLoading(false))
    return () => { current = false }
  }, [course])

  useEffect(() => {
    if (!roleId) { setRoleGaps(null); return }
    let current = true
    advisorAPI.skillGaps(course, roleId).then(r => current && setRoleGaps(r.data)).catch(() => {})
    return () => { current = false }
  }, [course, roleId])

  useEffect(() => {
    if (tab !== 'progress') return
    let current = true
    setProgress(null)
    advisorAPI.progress(course).then(r => current && setProgress(r.data)).catch(() => current && setError('Could not load learning progress.'))
    return () => { current = false }
  }, [tab, course])

  const myCourses  = COURSES.filter(c => !me || (me.advisor_courses || []).includes(c.id))
  const courseIds  = course ? [course] : myCourses.map(c => c.id)
  const courseTabs = myCourses.length > 1 ? [{ id: '', label: 'All my courses' }, ...myCourses] : []
  const cohortName = course ? courseLabel(course) : myCourses.length === 1 ? myCourses[0].label : 'all my courses'
  const courseRoles = roles.filter(r => (r.courses || []).some(c => courseIds.includes(c)))

  // ── Students: filter, sort ─────────────────────────────────
  const inCourse = useMemo(() => students.filter(s => !course || s.course === course), [students, course])
  const programmes = [...new Set(inCourse.map(s => s.programme).filter(Boolean))].sort()
  const targets    = [...new Set(inCourse.map(s => s.target_role).filter(Boolean))].sort()
  const q = search.trim().toLowerCase()
  const filtered = inCourse.filter(s =>
    (!status || statusOf(num(s.latest_score)) === status) &&
    (!programme || s.programme === programme) &&
    (!target || s.target_role === target) &&
    (!profileF || (profileF === 'complete') === !!s.profile_complete) &&
    (!q || [s.full_name, s.email, s.student_number, s.programme, s.target_role].some(v => (v || '').toLowerCase().includes(q)))
  )
  const sorted = [...filtered].sort((a, b) => {
    const dir = sort.dir === 'asc' ? 1 : -1
    let x = a[sort.key], y = b[sort.key]
    if (['latest_score', 'activities_completed', 'note_count'].includes(sort.key)) { x = num(x); y = num(y) }
    if (sort.key === 'last_assessed') { x = x ? Date.parse(x) : null; y = y ? Date.parse(y) : null }
    if (x == null && y == null) return 0
    if (x == null) return 1                       // students without a value always last
    if (y == null) return -1
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * dir
  })
  const anyFilter = search || status || programme || target || profileF
  const clearFilters = () => { setSearch(''); setStatus(''); setProgramme(''); setTarget(''); setProfileF(''); setShownRows(PAGE_SIZE) }
  const openStudent = (id) => navigate(`/students/${id}`, { state: { course, tab } })

  const exportStudents = () => downloadCsv(csvName('advisor_students'), [
    { label: 'Name', value: s => s.full_name }, { label: 'Student ID', value: s => s.student_number },
    { label: 'Email', value: s => s.email }, { label: 'Course', value: s => courseLabel(s.course) },
    { label: 'Programme', value: s => s.programme }, { label: 'Year', value: s => s.year_of_study },
    { label: 'Target role', value: s => s.target_role }, { label: 'GPA', value: s => s.gpa }, { label: 'CGPA', value: s => s.cgpa },
    { label: 'Readiness %', value: s => s.latest_score }, { label: 'Status', value: s => STATUS[statusOf(num(s.latest_score))].label },
    { label: 'Assessed role', value: s => s.assessed_role }, { label: 'Last assessed', value: s => fmtDate(s.last_assessed) },
    { label: 'Activities completed', value: s => s.activities_completed }, { label: 'Profile complete', value: s => (s.profile_complete ? 'Yes' : 'No') },
    { label: 'Advisor notes', value: s => s.note_count },
  ], sorted)

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  const shownGaps = roleId ? (roleGaps || []) : gaps
  const roleName  = roles.find(r => r.role_id === roleId)?.role_name
  const total     = overview?.total_students || 0
  const sc        = overview?.status_counts || {}

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Advisor Dashboard</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
          Employability of {cohortName}
          {me?.position_label && <> · <b style={{ color: C.ink }}>{me.position_label}</b></>}
          {me?.staff_number && <> · Staff ID <span style={{ fontFamily: 'Consolas, monospace' }}>{me.staff_number}</span></>}
        </div>
      </div>

      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{error}</div>}

      {/* Course: every tab shows one of the advisor's courses, or all of them */}
      {courseTabs.length > 0 && (
        <div role="tablist" aria-label="Course" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
          {courseTabs.map(c => {
            const active = course === c.id
            const n = c.id ? students.filter(s => s.course === c.id).length : students.length
            return (
              <button key={c.id || 'all'} role="tab" aria-selected={active}
                onClick={() => { setCourse(c.id); setRoleId(''); setProgramme(''); setTarget(''); setShownRows(PAGE_SIZE) }}
                style={{ padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                         background: active ? C.blue : '#fff', color: active ? '#fff' : C.body, border: `1.5px solid ${active ? C.blue : C.line}` }}>
                {c.label} ({n})
              </button>
            )
          })}
        </div>
      )}

      <DecisionNotice />

      {/* Tabs */}
      <div role="tablist" aria-label="Dashboard section" style={{ display: 'flex', gap: '4px', borderBottom: `2px solid ${C.line}`, marginBottom: '20px', flexWrap: 'wrap' }}>
        {TABS.map(t => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)} style={{
            padding: '10px 18px', fontSize: '13px', fontWeight: tab === t.id ? '600' : '500', color: tab === t.id ? C.blue : C.body,
            border: 'none', background: 'none', cursor: 'pointer', borderBottom: `2px solid ${tab === t.id ? C.blue : 'transparent'}`, marginBottom: '-2px',
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && overview && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            <StatCard label="Students" value={total} sub={`${overview.profiles_complete} profiles complete (${pct(overview.profiles_complete, total)}%)`} />
            <StatCard label="Assessed" value={overview.students_assessed} sub={`${pct(overview.students_assessed, total)}% of students`} color={C.blue} />
            <StatCard label="Avg Readiness" value={`${overview.avg_readiness_score}%`} sub="latest assessment of each student" color={scoreColor(overview.avg_readiness_score)} />
            <StatCard label="Needs Support" value={sc.needs_support ?? 0} sub="latest readiness below 40%" color={C.red} />
            <StatCard label="Activities Completed" value={overview.activities?.completed ?? 0}
              sub={`by ${overview.activities?.students_completed ?? 0} students`} color={C.green} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
            {/* Readiness distribution */}
            <div style={card}>
              <div style={{ ...heading, marginBottom: '4px' }}>Readiness Distribution</div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '12px' }}>Students by their latest readiness score</div>
              {overview.students_assessed === 0 ? <Empty>No assessment data yet.</Empty> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={overview.distribution} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="band" tick={{ fontSize: 10 }} interval={0} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Students']} labelFormatter={(l) => `Readiness ${l}%`} />
                    <Bar dataKey="students" radius={[4, 4, 0, 0]}>
                      {overview.distribution.map(d => <Cell key={d.band} fill={scoreColor(d.from)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Status breakdown */}
            <div style={card}>
              <div style={{ ...heading, marginBottom: '4px' }}>Student Status</div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '16px' }}>On Track ≥ 70% · Developing 40–69% · Needs Support &lt; 40%</div>
              {[['on_track', sc.on_track], ['developing', sc.developing], ['needs_support', sc.needs_support], ['none', sc.not_assessed]].map(([k, n]) => (
                <button key={k} onClick={() => { setStatus(k); setTab('students'); setShownRows(PAGE_SIZE) }}
                  title="Show these students" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', background: 'none', padding: '0 0 14px', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: C.body, marginBottom: '5px' }}>
                    <span style={{ fontWeight: '600', color: STATUS[k].color }}>{STATUS[k].label}</span>
                    <span><b style={{ color: C.ink }}>{n ?? 0}</b> · {pct(n, total)}%</span>
                  </div>
                  <div style={{ height: '8px', background: C.line, borderRadius: '99px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct(n, total)}%`, background: STATUS[k].color, borderRadius: '99px' }} />
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Top skill gaps */}
          <div style={card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', gap: '10px', flexWrap: 'wrap' }}>
              <div style={heading}>Top Skill Gaps</div>
              <button style={{ ...btn(false), padding: '6px 12px', fontSize: '12px' }} onClick={() => setTab('skill gaps')}>See all skill gaps →</button>
            </div>
            {gaps.length === 0 ? <Empty>No assessment data yet.</Empty> : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={gaps.slice(0, 10).map(g => ({ name: g.skill_name.length > 16 ? `${g.skill_name.slice(0, 16)}…` : g.skill_name, full: g.skill_name, gap: num(g.gap_percentage) || 0 }))}
                  margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v) => [`${v}%`, 'Students with this gap']} labelFormatter={(_l, p) => p?.[0]?.payload.full} />
                  <Bar dataKey="gap" fill={C.red} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Target roles */}
          <div style={card}>
            <div style={{ ...heading, marginBottom: '12px' }}>Target Roles</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '560px' }}>
                <thead><tr>{['Target role', 'Students', 'Assessed', 'Avg readiness'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
                <tbody>
                  {(overview.target_roles || []).map(r => (
                    <tr key={r.target_role}>
                      <td style={{ ...td, color: C.ink, fontWeight: '600' }}>
                        {r.target_role === 'Not set' ? <span style={{ color: C.muted, fontWeight: '500' }}>Not set yet</span> : (
                          <button onClick={() => { setTarget(r.target_role); setTab('students'); setShownRows(PAGE_SIZE) }}
                            style={{ border: 'none', background: 'none', padding: 0, color: C.blue, fontWeight: '600', cursor: 'pointer', fontSize: '12px' }}>
                            {r.target_role}
                          </button>
                        )}
                      </td>
                      <td style={td}>{r.students}</td>
                      <td style={td}>{r.assessed} ({pct(r.assessed, r.students)}%)</td>
                      <td style={{ ...td, fontWeight: '700', color: scoreColor(r.avg_score) }}>{r.avg_score == null ? '—' : `${r.avg_score}%`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ── Skill gaps ── */}
      {tab === 'skill gaps' && (
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '6px' }}>
            <div style={heading}>Skill Gap Report — {cohortName}{roleName ? ` · ${roleName}` : ''}</div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <select aria-label="Assessed job role" value={roleId} onChange={e => setRoleId(e.target.value)} style={input}>
                <option value="">All assessed roles</option>
                {courseRoles.map(r => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
              </select>
              <button style={btn(false)} disabled={!shownGaps.length}
                onClick={() => downloadCsv(csvName(`skill_gaps${roleName ? `_${roleName.replace(/\s+/g, '_')}` : ''}`), [
                  { label: 'Skill', value: g => g.skill_name }, { label: 'Category', value: g => g.category },
                  { label: 'Gap %', value: g => g.gap_percentage }, { label: 'Gap', value: g => g.gap_count },
                  { label: 'Developing', value: g => g.developing_count }, { label: 'Strong', value: g => g.strong_count },
                  { label: 'Assessments', value: g => g.total_assessments },
                ], shownGaps)}>
                Export CSV
              </button>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: C.muted, marginBottom: '14px' }}>
            The 20 skills most often missing in each student&apos;s latest assessment{roleName ? ` against ${roleName}` : ''}.
          </div>
          {roleId && roleGaps == null ? <Empty>Loading…</Empty> : shownGaps.length === 0 ? <Empty>No assessment data for this selection yet.</Empty> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                <thead><tr>{['Skill', 'Category', 'Gap %', 'Gap', 'Developing', 'Strong', 'Assessments'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
                <tbody>
                  {shownGaps.map((g, i) => {
                    const p = num(g.gap_percentage) || 0
                    const col = p > 60 ? C.red : p > 30 ? C.amber : C.green
                    return (
                      <tr key={g.skill_name} style={{ background: i % 2 === 0 ? C.bg : '#fff' }}>
                        <td style={{ ...td, fontSize: '13px', fontWeight: '500', color: C.ink }}>{g.skill_name}</td>
                        <td style={td}>{g.category.replace('_', ' / ')}</td>
                        <td style={{ ...td, minWidth: '160px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ flex: 1, height: '6px', background: C.line, borderRadius: '99px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${p}%`, background: col, borderRadius: '99px' }} />
                            </div>
                            <span style={{ fontWeight: '700', color: col, width: '40px' }}>{p}%</span>
                          </div>
                        </td>
                        <td style={{ ...td, color: C.red, fontWeight: '600' }}>{g.gap_count}</td>
                        <td style={{ ...td, color: C.amber, fontWeight: '600' }}>{g.developing_count}</td>
                        <td style={{ ...td, color: C.green, fontWeight: '600' }}>{g.strong_count}</td>
                        <td style={td}>{g.total_assessments}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Students ── */}
      {tab === 'students' && (
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '14px' }}>
            <div style={heading}>
              Students ({filtered.length}{filtered.length !== inCourse.length ? ` of ${inCourse.length}` : ''})
            </div>
            <button style={btn(false)} disabled={!sorted.length} onClick={exportStudents}>Export CSV</button>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}>
            <input type="search" aria-label="Search students" placeholder="Search name, student ID, email, programme or role"
              value={search} onChange={e => { setSearch(e.target.value); setShownRows(PAGE_SIZE) }} style={{ ...input, flex: '1 1 260px' }} />
            <select aria-label="Filter by status" value={status} onChange={e => { setStatus(e.target.value); setShownRows(PAGE_SIZE) }} style={input}>
              <option value="">All statuses</option>
              {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
            <select aria-label="Filter by programme" value={programme} onChange={e => { setProgramme(e.target.value); setShownRows(PAGE_SIZE) }} style={{ ...input, maxWidth: '280px' }}>
              <option value="">All programmes</option>
              {programmes.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select aria-label="Filter by target role" value={target} onChange={e => { setTarget(e.target.value); setShownRows(PAGE_SIZE) }} style={input}>
              <option value="">All target roles</option>
              {targets.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select aria-label="Filter by profile" value={profileF} onChange={e => { setProfileF(e.target.value); setShownRows(PAGE_SIZE) }} style={input}>
              <option value="">Any profile</option>
              <option value="complete">Profile complete</option>
              <option value="incomplete">Profile incomplete</option>
            </select>
            {anyFilter && <button style={{ ...btn(false), color: C.blue }} onClick={clearFilters}>Clear filters</button>}
          </div>
          <div style={{ fontSize: '12px', color: C.muted, marginBottom: '10px' }}>Click a column title to sort, and a student to open their full record.</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '1150px' }}>
              <thead>
                <tr>
                  <SortTh label="Name" k="full_name" sort={sort} setSort={setSort} />
                  <th style={th}>Student ID</th>
                  {!course && myCourses.length > 1 && <th style={th}>Course</th>}
                  <SortTh label="Programme" k="programme" sort={sort} setSort={setSort} />
                  <SortTh label="Target role" k="target_role" sort={sort} setSort={setSort} />
                  <SortTh label="Readiness" k="latest_score" sort={sort} setSort={setSort} />
                  <th style={th}>Status</th>
                  <SortTh label="Last assessed" k="last_assessed" sort={sort} setSort={setSort} />
                  <SortTh label="Activities" k="activities_completed" sort={sort} setSort={setSort} />
                  <SortTh label="Notes" k="note_count" sort={sort} setSort={setSort} />
                </tr>
              </thead>
              <tbody>
                {sorted.length === 0 && (
                  <tr><td colSpan={10} style={{ ...td, textAlign: 'center', padding: '32px', color: C.muted }}>No students match.</td></tr>
                )}
                {sorted.slice(0, shownRows).map((s, i) => {
                  const score = num(s.latest_score)
                  return (
                    <tr key={s.user_id} onClick={() => openStudent(s.user_id)} tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') openStudent(s.user_id) }}
                      style={{ background: i % 2 === 0 ? C.bg : '#fff', cursor: 'pointer' }}>
                      <td style={{ ...td, fontSize: '13px', fontWeight: '500', color: C.blue, whiteSpace: 'nowrap' }}>
                        {s.full_name}
                        {!s.profile_complete && <span title="Profile incomplete" style={{ color: C.amber, marginLeft: '6px' }}>●</span>}
                      </td>
                      <td style={{ ...td, fontFamily: 'Consolas, monospace', whiteSpace: 'nowrap' }}>{s.student_number || '—'}</td>
                      {!course && myCourses.length > 1 && <td style={td}>{courseLabel(s.course)}</td>}
                      <td style={td}>{s.programme || '—'}</td>
                      <td style={td}>{s.target_role || '—'}</td>
                      <td style={{ ...td, fontSize: '14px', fontWeight: '700', color: scoreColor(score) }}>{score == null ? '—' : `${score}%`}</td>
                      <td style={td}><Pill status={statusOf(score)} /></td>
                      <td style={{ ...td, whiteSpace: 'nowrap' }} title={s.assessed_role || undefined}>{fmtDate(s.last_assessed)}</td>
                      <td style={td}>{s.activities_completed ?? 0}</td>
                      <td style={td}>{s.note_count ? <b style={{ color: C.blue }}>{s.note_count}</b> : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: '11px', color: C.muted, marginTop: '8px' }}><span style={{ color: C.amber }}>●</span> profile incomplete</div>
          {sorted.length > shownRows && (
            <div style={{ textAlign: 'center', marginTop: '14px' }}>
              <button style={btn(false)} onClick={() => setShownRows(n => n + PAGE_SIZE)}>Show more ({sorted.length - shownRows} left)</button>
            </div>
          )}
        </div>
      )}

      {/* ── Learning progress ── */}
      {tab === 'progress' && (
        !progress ? <div style={{ color: C.muted, padding: '20px' }}>Loading…</div> : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '16px', marginBottom: '16px' }}>
              <StatCard label="Activities Completed" value={progress.totals.completed} color={C.green} />
              <StatCard label="In Progress" value={progress.totals.in_progress} color={C.blue} />
              <StatCard label="Saved for Later" value={progress.totals.saved} color={C.muted} />
              <StatCard label="Active Students" value={progress.totals.students_active}
                sub={`${pct(progress.totals.students_active, total)}% of students started an activity`} />
              <StatCard label="Completed One or More" value={progress.totals.students_completed} color={C.green}
                sub={`${pct(progress.totals.students_completed, total)}% of students`} />
            </div>

            <div style={card}>
              <div style={{ ...heading, marginBottom: '12px' }}>Most Completed Learning Resources</div>
              {progress.top_resources.length === 0 ? <Empty>No student has started a recommended activity yet.</Empty> : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                    <thead><tr>{['Resource', 'Type', 'Provider', 'Skill', 'Completed', 'In progress'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
                    <tbody>
                      {progress.top_resources.map(r => (
                        <tr key={r.resource_title + r.skill_name}>
                          <td style={{ ...td, color: C.ink, fontWeight: '500' }}>{r.resource_title}</td>
                          <td style={{ ...td, textTransform: 'capitalize' }}>{r.resource_type}</td>
                          <td style={td}>{r.provider || '—'}</td>
                          <td style={td}>{r.skill_name || '—'}</td>
                          <td style={{ ...td, color: C.green, fontWeight: '700' }}>{r.completed}</td>
                          <td style={{ ...td, color: C.blue, fontWeight: '600' }}>{r.in_progress}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div style={card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
                <div style={heading}>Students&apos; Activities ({progress.students.length})</div>
                <button style={btn(false)} disabled={!progress.students.length}
                  onClick={() => downloadCsv(csvName('advisor_learning_progress'), [
                    { label: 'Name', value: s => s.full_name }, { label: 'Student ID', value: s => s.student_number },
                    { label: 'Course', value: s => courseLabel(s.course) }, { label: 'Target role', value: s => s.target_role },
                    { label: 'Completed', value: s => s.completed }, { label: 'In progress', value: s => s.in_progress },
                    { label: 'Saved', value: s => s.saved }, { label: 'Last completed', value: s => fmtDate(s.last_completed) },
                  ], progress.students)}>
                  Export CSV
                </button>
              </div>
              {progress.students.length === 0 ? <Empty>No student has started a recommended activity yet.</Empty> : (
                <div style={{ overflowX: 'auto', maxHeight: '520px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '760px' }}>
                    <thead><tr>{['Name', 'Student ID', 'Target role', 'Completed', 'In progress', 'Saved', 'Last completed'].map(h =>
                      <th key={h} style={{ ...th, position: 'sticky', top: 0 }}>{h}</th>)}</tr></thead>
                    <tbody>
                      {progress.students.slice(0, 300).map((s, i) => (
                        <tr key={s.user_id} onClick={() => openStudent(s.user_id)} style={{ background: i % 2 === 0 ? C.bg : '#fff', cursor: 'pointer' }}>
                          <td style={{ ...td, fontSize: '13px', color: C.blue, fontWeight: '500', whiteSpace: 'nowrap' }}>{s.full_name}</td>
                          <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{s.student_number || '—'}</td>
                          <td style={td}>{s.target_role || '—'}</td>
                          <td style={{ ...td, color: C.green, fontWeight: '700' }}>{s.completed}</td>
                          <td style={{ ...td, color: C.blue, fontWeight: '600' }}>{s.in_progress}</td>
                          <td style={td}>{s.saved}</td>
                          <td style={{ ...td, whiteSpace: 'nowrap' }}>{fmtDate(s.last_completed)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {progress.students.length > 300 && <div style={{ fontSize: '12px', color: C.muted, padding: '10px' }}>Showing the first 300; export CSV for the full list.</div>}
                </div>
              )}
            </div>
          </>
        )
      )}
    </div>
  )
}
