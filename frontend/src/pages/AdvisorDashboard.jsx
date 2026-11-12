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

const C = { ink: 'var(--s-ink, #1a1f2e)', body: 'var(--s-body, #4a5168)', muted: 'var(--s-muted, #8b92a8)', line: 'var(--s-line, #e4e6ef)', blue: 'var(--s-accent, #2d5be3)',
            green: '#16a34a', amber: '#d97706', red: '#dc2626', bg: 'var(--s-bg, #f5f6fa)' }
const card    = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '22px 24px', marginBottom: '16px' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, textTransform: 'uppercase', letterSpacing: '0.5px' }
const th      = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px',
                  padding: '10px 12px', borderBottom: `1px solid ${C.line}`, whiteSpace: 'nowrap', background: '#fff' }
const td      = { padding: '10px 12px', fontSize: '12px', color: C.body, borderBottom: '1px solid var(--s-line-soft, #f0f1f5)' }
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

// Readiness bands come from System Settings (overview.bands; defaults 70 and 40). A score of 0 is a real result.
// Student status (computed by the backend, backend/student_status.py): the latest readiness
// compared with what is expected for the student's year of study, and recent activity.
// Only Needs Support asks the advisor to act; the order is the order of the status chart.
const STATUS = {
  needs_support:   { label: 'Needs Support',   bg: '#fee2e2', color: C.red,
                     help: 'Below the level expected for their year and no learning activity recently: worth contacting.' },
  improving:       { label: 'Improving',       bg: '#e0f2fe', color: '#0369a1',
                     help: 'Below the expected level, but working on activities or their score went up.' },
  getting_started: { label: 'Getting Started', bg: '#f3e8ff', color: '#7e22ce',
                     help: 'New Year 1 student this semester: a low score is normal at the start.' },
  developing:      { label: 'Developing',      bg: '#fef3c7', color: C.amber,
                     help: 'Within the expected range for their year.' },
  on_track:        { label: 'On Track',        bg: '#dcfce7', color: C.green,
                     help: 'At or above the On Track level for their year.' },
  none:            { label: 'Not Assessed',    bg: C.bg,      color: C.muted,
                     help: 'Has not run an assessment yet.' },
}
// Learning Progress cards: what each counts and what clicking it lists
const PVIEWS = [
  { id: 'completed',   label: 'Activities Completed', total: 'completed',   color: C.green, kind: 'activities', hint: 'See completed activities',
    title: 'Completed activities', explain: 'Recommended activities students have finished with evidence, grouped by student.',
    dateLabel: 'Completed', dateKey: 'completed_at', countLabel: 'Completed', unit: 'completed activities', empty: 'No activity has been completed yet.' },
  { id: 'in_progress', label: 'In Progress',          total: 'in_progress', color: C.blue,  kind: 'activities', hint: 'See activities in progress',
    title: 'Activities in progress', explain: 'Activities students have started but not finished yet, grouped by student.',
    dateLabel: 'Started', dateKey: 'started_at', countLabel: 'In progress', unit: 'activities in progress', empty: 'No activity is in progress.' },
  { id: 'saved',       label: 'Saved for Later',      total: 'saved',       color: C.muted, kind: 'activities', hint: 'See saved activities',
    title: 'Activities saved for later', explain: 'Activities students saved but have not started, grouped by student.',
    dateLabel: 'Saved', dateKey: 'created_at', countLabel: 'Saved', unit: 'saved activities', empty: 'No activity is saved for later.' },
  { id: 'active',      label: 'Active Students',      total: 'students_active', color: C.ink, kind: 'students', hint: 'See active students',
    sub: (t, all) => `${pct(t.students_active, all)}% of students started an activity`,
    title: 'Students who started an activity', explain: 'Students with at least one saved, started or completed activity.',
    empty: 'No student has started a recommended activity yet.' },
  { id: 'completers',  label: 'Completed One or More', total: 'students_completed', color: C.green, kind: 'students', hint: 'See who completed one',
    sub: (t, all) => `${pct(t.students_completed, all)}% of students`,
    title: 'Students who completed an activity', explain: 'Students who finished at least one activity.',
    empty: 'No student has completed an activity yet.' },
]
// Skill categories (skills_library.category); Soft is the soft-skill view the lecturer asked for
const CATEGORIES = [
  { id: 'Technical',  label: 'Technical' },
  { id: 'AI_Digital', label: 'AI & Digital' },
  { id: 'Analytical', label: 'Analytical' },
  { id: 'Soft',       label: 'Soft skills' },
]
const categoryLabel = (id) => CATEGORIES.find(c => c.id === id)?.label || id
const num = (v) => (v == null ? null : parseFloat(v))
let BANDS = { on_track: 70, needs_support: 40 }
const scoreColor = (s) => s == null ? C.muted : s >= BANDS.on_track ? C.green : s >= BANDS.needs_support ? C.amber : C.red
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB') : '—'
const pct = (n, total) => total ? Math.round((n / total) * 100) : 0

function Pill({ status, title }) {
  const s = STATUS[status] || STATUS.none
  return <span title={title || s.help} style={{ padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', background: s.bg, color: s.color, whiteSpace: 'nowrap' }}>{s.label}</span>
}

// onClick: the card opens the list behind its number (e.g. the students who need support);
// hint says where it goes
function StatCard({ label, value, sub, color = C.ink, onClick, hint, active }) {
  const [hover, setHover] = useState(false)
  const body = <>
    <div style={{ fontSize: '11px', fontWeight: '600', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
    <div style={{ fontSize: '30px', fontWeight: '700', color, margin: '4px 0 2px', lineHeight: 1.1 }}>{value}</div>
    {sub && <div style={{ fontSize: '12px', color: C.muted }}>{sub}</div>}
    {onClick && <div style={{ fontSize: '12px', fontWeight: '600', color: hover || active ? color : C.muted, marginTop: '8px' }}>
      {active ? 'Showing below ↓' : `${hint || 'View'} →`}</div>}
  </>
  if (!onClick) return <div style={{ ...card, marginBottom: 0, padding: '18px 20px' }}>{body}</div>
  return (
    <button type="button" onClick={onClick} title={hint} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      onFocus={() => setHover(true)} onBlur={() => setHover(false)}
      aria-pressed={active || undefined}
      style={{ ...card, marginBottom: 0, padding: '18px 20px', textAlign: 'left', font: 'inherit', cursor: 'pointer', width: '100%',
               borderColor: hover || active ? color : undefined, borderWidth: active ? '2px' : undefined,
               transform: hover ? 'translateY(-2px)' : 'none',
               boxShadow: hover ? '0 8px 20px rgba(17, 17, 17, 0.08)' : card.boxShadow, transition: 'transform .15s, box-shadow .15s, border-color .15s' }}>
      {body}
    </button>
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
  const [gapProgramme, setGapProgramme] = useState('')  // skill gaps of one programme (major)
  const [gapCategory, setGapCategory]   = useState('')  // skill gaps of one skill category
  const [roleGaps, setRoleGaps] = useState(null)        // skill gaps with the filters above
  const [categories, setCategories] = useState(null)    // Strong / Developing / Gap per category
  const [mqfOpen, setMqfOpen]   = useState(false)       // MQF learning-outcome cluster view shown
  const [mqfRows, setMqfRows]   = useState(null)        // gaps per MQF cluster (same filters)
  const [mqfCluster, setMqfCluster] = useState(null)    // cluster whose skills are unfolded
  const [mqfSkill, setMqfSkill] = useState(null)        // skill (in that cluster) whose students are unfolded
  const [skillStudents, setSkillStudents] = useState(null)
  const [skillResult, setSkillResult] = useState('gap') // gap / developing / strong shown for that skill
  const [progress, setProgress] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  // Student list filters and sorting
  const [search, setSearch]       = useState('')
  const [status, setStatus]       = useState('')
  const [band, setBand]           = useState(null)   // lower limit of a readiness bar that was clicked
  const [programme, setProgramme] = useState('')
  const [target, setTarget]       = useState('')
  const [profileF, setProfileF]   = useState('')
  const [year, setYear]           = useState('')
  // Learning Progress: which card was clicked ('' = the full page). completed / in_progress /
  // saved list single activities; active / completers list students
  const [pview, setPview]         = useState(location.state?.pview || '')
  const [acts, setActs]           = useState(null)   // { status, total, activities } for pview
  const [openStu, setOpenStu]     = useState(null)   // student whose activities are unfolded in that list     // '' all, 'none' not set, or a year of study ('1', '2', ...)
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
      .then(([ov, sg]) => {
        if (!current) return
        if (ov.data.bands) BANDS = ov.data.bands
        setOverview(ov.data); setGaps(sg.data); setError('')
      })
      .catch(() => current && setError('Could not load the cohort figures.'))
      .finally(() => current && setLoading(false))
    return () => { current = false }
  }, [course])

  const gapFilter = roleId || gapProgramme || gapCategory
  useEffect(() => {
    if (!gapFilter) { setRoleGaps(null); return }
    let current = true
    setRoleGaps(null)
    advisorAPI.skillGaps(course, roleId, gapProgramme, gapCategory).then(r => current && setRoleGaps(r.data)).catch(() => {})
    return () => { current = false }
  }, [course, roleId, gapProgramme, gapCategory, gapFilter])

  useEffect(() => {
    if (tab !== 'skill gaps') return
    let current = true
    setCategories(null)
    advisorAPI.skillCategories(course, roleId, gapProgramme).then(r => current && setCategories(r.data)).catch(() => {})
    return () => { current = false }
  }, [tab, course, roleId, gapProgramme])

  // Students behind one skill of the MQF view (same filters)
  useEffect(() => {
    if (!mqfSkill) return
    let current = true
    setSkillStudents(null)
    advisorAPI.skillStudents(mqfSkill, course, roleId, gapProgramme).then(r => current && setSkillStudents(r.data)).catch(() => current && setSkillStudents([]))
    return () => { current = false }
  }, [mqfSkill, course, roleId, gapProgramme])

  // MQF clusters: loaded when the view is opened, with the same course / role / programme filters
  useEffect(() => {
    if (tab !== 'skill gaps' || !mqfOpen) return
    let current = true
    setMqfRows(null)
    advisorAPI.mqfClusters(course, roleId, gapProgramme).then(r => current && setMqfRows(r.data)).catch(() => {})
    return () => { current = false }
  }, [tab, mqfOpen, course, roleId, gapProgramme])

  useEffect(() => {
    if (tab !== 'progress') return
    let current = true
    setProgress(null)
    advisorAPI.progress(course).then(r => current && setProgress(r.data)).catch(() => current && setError('Could not load learning progress.'))
    return () => { current = false }
  }, [tab, course])

  // The single activities behind the clicked Learning Progress card
  useEffect(() => {
    if (tab !== 'progress' || !['completed', 'in_progress', 'saved'].includes(pview)) return
    let current = true
    setActs(null)
    advisorAPI.activities(pview, course).then(r => current && setActs(r.data)).catch(() => current && setError('Could not load the activities.'))
    return () => { current = false }
  }, [tab, pview, course])

  const myCourses  = COURSES.filter(c => !me || (me.advisor_courses || []).includes(c.id))
  const courseIds  = course ? [course] : myCourses.map(c => c.id)
  const courseTabs = myCourses.length > 1 ? [{ id: '', label: 'All my courses' }, ...myCourses] : []
  const cohortName = course ? courseLabel(course) : myCourses.length === 1 ? myCourses[0].label : 'all my courses'
  const courseRoles = roles.filter(r => (r.courses || []).some(c => courseIds.includes(c)))

  // ── Students: filter, sort ─────────────────────────────────
  const inCourse = useMemo(() => students.filter(s => !course || s.course === course), [students, course])
  const programmes = [...new Set(inCourse.map(s => s.programme).filter(Boolean))].sort()
  const targets    = [...new Set(inCourse.map(s => s.target_role).filter(Boolean))].sort()
  // Years of study present in the course (Year 1, Year 2, ...), for the Year filter
  const years      = [...new Set(inCourse.map(s => s.year_of_study).filter(y => y != null))].map(Number).sort((a, b) => a - b)
  const noYear     = inCourse.some(s => s.year_of_study == null)
  // Word by word, so extra spaces and the order of the words do not matter
  const words = search.toLowerCase().split(/\s+/).filter(Boolean)
  const filtered = inCourse.filter(s =>
    (!status || (status === 'assessed' ? s.status !== 'none' : s.status === status)) &&
    (band == null || (s.latest_score != null && num(s.latest_score) >= band && (band === 90 || num(s.latest_score) < band + 10))) &&
    (!programme || s.programme === programme) &&
    (!target || s.target_role === target) &&
    (!year || (year === 'none' ? s.year_of_study == null : String(s.year_of_study) === year)) &&
    (!profileF || (profileF === 'complete') === !!s.profile_complete) &&
    words.every(w => [s.full_name, s.email, s.student_number, s.programme, s.target_role].some(v => (v || '').toLowerCase().includes(w)))
  )
  const sorted = [...filtered].sort((a, b) => {
    const dir = sort.dir === 'asc' ? 1 : -1
    let x = a[sort.key], y = b[sort.key]
    if (['latest_score', 'activities_completed', 'note_count', 'year_of_study'].includes(sort.key)) { x = num(x); y = num(y) }
    if (sort.key === 'last_assessed') { x = x ? Date.parse(x) : null; y = y ? Date.parse(y) : null }
    if (x == null && y == null) return 0
    if (x == null) return 1                       // students without a value always last
    if (y == null) return -1
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * dir
  })
  const anyFilter = search || status || band != null || programme || target || profileF || year
  const clearFilters = () => { setSearch(''); setStatus(''); setBand(null); setProgramme(''); setTarget(''); setProfileF(''); setYear(''); setShownRows(PAGE_SIZE) }
  const openStudent = (id) => navigate(`/students/${id}`, { state: { course, tab, pview } })
  // Open the Students tab with only the given filter (overview cards)
  const openList = ({ status: st = '', sort: so = { key: 'full_name', dir: 'asc' } }) => {
    clearFilters()
    setStatus(st)
    setSort(so)
    setTab('students')
  }

  const exportStudents = () => downloadCsv(csvName('advisor_students'), [
    { label: 'Name', value: s => s.full_name }, { label: 'Student ID', value: s => s.student_number },
    { label: 'Email', value: s => s.email }, { label: 'Course', value: s => courseLabel(s.course) },
    { label: 'Programme', value: s => s.programme }, { label: 'Year', value: s => s.year_of_study },
    { label: 'Target role', value: s => s.target_role }, { label: 'GPA', value: s => s.gpa }, { label: 'CGPA', value: s => s.cgpa },
    { label: 'Readiness %', value: s => s.latest_score }, { label: 'Status', value: s => STATUS[s.status]?.label },
    { label: 'Why', value: s => s.status_reason },
    { label: 'Assessed role', value: s => s.assessed_role }, { label: 'Last assessed', value: s => fmtDate(s.last_assessed) },
    { label: 'Activities completed', value: s => s.activities_completed }, { label: 'Profile complete', value: s => (s.profile_complete ? 'Yes' : 'No') },
    { label: 'Advisor notes', value: s => s.note_count },
  ], sorted)

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  const shownGaps = gapFilter ? (roleGaps || []) : gaps
  const roleName  = roles.find(r => r.role_id === roleId)?.role_name
  const gapTitle  = [roleName, gapProgramme, gapCategory && categoryLabel(gapCategory)].filter(Boolean).join(' · ')
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
                onClick={() => { setCourse(c.id); setRoleId(''); setGapProgramme(''); setProgramme(''); setTarget(''); setBand(null); setShownRows(PAGE_SIZE) }}
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
            <StatCard label="Students" value={total} sub={`${overview.profiles_complete} profiles complete (${pct(overview.profiles_complete, total)}%)`}
              onClick={() => openList({})} hint="See all students" />
            <StatCard label="Assessed" value={overview.students_assessed} sub={`${pct(overview.students_assessed, total)}% of students`} color={C.blue}
              onClick={() => openList({ status: 'assessed' })} hint="See assessed students" />
            <StatCard label="Avg Readiness" value={`${overview.avg_readiness_score}%`} sub="latest assessment of each student" color={scoreColor(overview.avg_readiness_score)}
              onClick={() => openList({ status: 'assessed', sort: { key: 'latest_score', dir: 'desc' } })} hint="See students by readiness" />
            <StatCard label="Needs Support" value={sc.needs_support ?? 0}
              sub={`below their year's level, no activity in ${overview.status_rules?.active_days ?? 30} days`} color={C.red}
              onClick={() => openList({ status: 'needs_support', sort: { key: 'latest_score', dir: 'asc' } })} hint="See who needs support" />
            <StatCard label="Activities Completed" value={overview.activities?.completed ?? 0}
              sub={`by ${overview.activities?.students_completed ?? 0} students`} color={C.green}
              onClick={() => { setPview('completed'); setTab('progress') }} hint="See completed activities" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
            {/* Readiness distribution */}
            <div style={card}>
              <div style={{ ...heading, marginBottom: '4px' }}>Readiness Distribution</div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '12px' }}>Students by their latest readiness score. Click a bar to see those students.</div>
              {overview.students_assessed === 0 ? <Empty>No assessment data yet.</Empty> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={overview.distribution} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="band" tick={{ fontSize: 10 }} interval={0} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip formatter={(v) => [v, 'Students']} labelFormatter={(l) => `Readiness ${l}%`} />
                    <Bar dataKey="students" radius={[4, 4, 0, 0]} cursor="pointer"
                      onClick={d => { setBand(d.payload?.from ?? d.from); setStatus(''); setTab('students'); setShownRows(PAGE_SIZE) }}>
                      {overview.distribution.map(d => <Cell key={d.band} fill={scoreColor(d.from)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Status breakdown */}
            <div style={card}>
              <div style={{ ...heading, marginBottom: '4px' }}>Student Status</div>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '16px' }}>
                Each student is compared with what is expected for their year of study. Needs Support = below the
                expected level <b>and</b> no learning activity in the last {overview.status_rules?.active_days ?? 30} days.
              </div>
              {overview.status_rules && (
                <div style={{ display: 'grid', gridTemplateColumns: 'auto repeat(4, 1fr)', gap: '2px 10px', fontSize: '11px', color: C.body,
                              background: C.bg, borderRadius: '8px', padding: '8px 10px', marginBottom: '14px' }}>
                  <span style={{ color: C.muted }}>Year</span>
                  {['1', '2', '3', '4+'].map(y => <b key={y} style={{ color: C.ink }}>{y}</b>)}
                  <span style={{ color: C.green }}>On Track ≥</span>
                  {['1', '2', '3'].map(y => <span key={y}>{overview.status_rules.years[y]?.on_track}%</span>)}
                  <span>{overview.status_rules.default.on_track}%</span>
                  <span style={{ color: C.red }}>Below expected &lt;</span>
                  {['1', '2', '3'].map(y => <span key={y}>{overview.status_rules.years[y]?.needs_support}%</span>)}
                  <span>{overview.status_rules.default.needs_support}%</span>
                </div>
              )}
              {Object.keys(STATUS).map(k => [k, sc[k]]).map(([k, n]) => (
                <button key={k} onClick={() => { setStatus(k); setBand(null); setTab('students'); setShownRows(PAGE_SIZE) }}
                  title="Show these students" style={{ display: 'block', width: '100%', textAlign: 'left', border: 'none', background: 'none', padding: '0 0 14px', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: C.body, marginBottom: '5px' }}>
                    <span style={{ fontWeight: '600', color: STATUS[k].color }} title={STATUS[k].help}>{STATUS[k].label}</span>
                    <span><b style={{ color: C.ink }}>{n ?? 0}</b> · {pct(n, total)}%</span>
                  </div>
                  <div style={{ height: '8px', background: C.line, borderRadius: '99px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct(n, total)}%`, background: STATUS[k].color, borderRadius: '99px' }} />
                  </div>
                </button>
              ))}
            </div>
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
            <div style={heading}>Skill Gap Report — {cohortName}{gapTitle ? ` · ${gapTitle}` : ''}</div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <select aria-label="Programme" value={gapProgramme} onChange={e => setGapProgramme(e.target.value)} style={{ ...input, maxWidth: '280px' }}>
                <option value="">All programmes</option>
                {programmes.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <select aria-label="Assessed job role" value={roleId} onChange={e => setRoleId(e.target.value)} style={input}>
                <option value="">All assessed roles</option>
                {courseRoles.map(r => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
              </select>
              <button style={btn(false)} disabled={!shownGaps.length}
                onClick={() => downloadCsv(csvName(`skill_gaps${gapTitle ? `_${gapTitle.replace(/[^A-Za-z0-9]+/g, '_')}` : ''}`), [
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
            The 20 skills{gapCategory ? ` (${categoryLabel(gapCategory)} only)` : ''} most often missing in each
            student&apos;s latest assessment{roleName ? ` against ${roleName}` : ''}{gapProgramme ? `, ${gapProgramme} students only` : ''}.
            Click a category to see only its skills.
          </div>

          {/* Skill categories: how strong the cohort is in each; a card shows only that category */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '10px', marginBottom: '16px' }}>
            {(categories || CATEGORIES.map(c => ({ category: c.id, total: null }))).map(cat => {
              const selected = gapCategory === cat.category
              const soft = cat.category === 'Soft'
              const parts = [['strong', C.green], ['developing', C.amber], ['gap', C.red]]
              return (
                <button key={cat.category} onClick={() => setGapCategory(selected ? '' : cat.category)} aria-pressed={selected}
                  title={selected ? 'Show every category' : `Show only ${categoryLabel(cat.category)}`}
                  style={{ textAlign: 'left', cursor: 'pointer', borderRadius: '10px', padding: '12px 14px',
                           background: selected ? 'var(--s-accent-soft, #eef3ff)' : soft ? '#fbf8ff' : '#fff',
                           border: `1.5px solid ${selected ? C.blue : soft ? '#ddd6fe' : C.line}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '6px' }}>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: C.ink }}>{categoryLabel(cat.category)}</span>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: cat.gap_percentage == null ? C.muted : C.red }}>
                      {cat.total == null ? '…' : cat.gap_percentage == null ? 'No data' : `${cat.gap_percentage}% gap`}
                    </span>
                  </div>
                  <div style={{ display: 'flex', height: '8px', borderRadius: '99px', overflow: 'hidden', background: C.line, margin: '8px 0 6px' }}>
                    {cat.total > 0 && parts.map(([k, col]) => (
                      <div key={k} style={{ width: `${pct(cat[`${k}_count`], cat.total)}%`, background: col }} />
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: C.muted }}>
                    {!cat.total ? 'Not asked for in these assessments'
                      : `${pct(cat.strong_count, cat.total)}% strong · ${pct(cat.developing_count, cat.total)}% developing · ${cat.assessments} assessments`}
                  </div>
                </button>
              )
            })}
          </div>

          {/* The same gaps in the language of MQA accreditation: MQF learning-outcome clusters */}
          <div style={{ border: `1px solid ${C.line}`, borderRadius: '10px', marginBottom: '16px', overflow: 'hidden' }}>
            <button type="button" onClick={() => setMqfOpen(o => !o)} aria-expanded={mqfOpen}
              style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', padding: '12px 14px',
                       background: mqfOpen ? '#fafafa' : '#fff', border: 'none', cursor: 'pointer', textAlign: 'left', font: 'inherit' }}>
              <span>
                <span style={{ fontSize: '13px', fontWeight: '700', color: C.ink }}>View by MQF learning-outcome cluster</span>
                <span style={{ fontSize: '12px', color: C.muted, marginLeft: '8px' }}>MQA · COPPA standard 1.1.4 · aligned with the ASEAN framework (AQRF)</span>
              </span>
              <span style={{ color: C.muted }}>{mqfOpen ? '▾' : '▸'}</span>
            </button>
            {mqfOpen && (
              <div style={{ padding: '4px 14px 14px' }}>
                <div style={{ fontSize: '12px', color: C.muted, margin: '6px 0 12px', lineHeight: 1.5 }}>
                  The skill gaps above, grouped by the five clusters of learning outcomes in the Malaysian Qualifications Framework
                  (2nd edition), the clusters that every programme&apos;s learning outcomes must correspond to for MQA accreditation.
                  Each skill counts in its main cluster; this mapping is our own preliminary one.
                </div>
                {mqfRows == null ? <Empty>Loading…</Empty> : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                      <thead><tr>{['MQF cluster', 'Gap %', 'Strong · Developing · Gap', 'Most frequent gaps'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
                      <tbody>
                        {mqfRows.map(r => {
                          const open = mqfCluster === r.cluster
                          const canOpen = r.skills?.length > 0
                          return [
                          <tr key={r.cluster} onClick={() => { if (canOpen) { setMqfCluster(open ? null : r.cluster); setMqfSkill(null) } }} aria-expanded={canOpen ? open : undefined}
                            title={canOpen ? (open ? 'Hide the skills' : 'Show every skill in this cluster') : undefined}
                            style={{ cursor: canOpen ? 'pointer' : 'default', background: open ? '#fff7f8' : undefined }}>
                            <td style={{ ...td, color: C.ink, fontWeight: '600' }}>
                              <span style={{ display: 'inline-block', width: '16px', color: C.muted }}>{canOpen ? (open ? '▾' : '▸') : ''}</span>
                              <span style={{ display: 'inline-block', minWidth: '26px', color: C.muted }}>{r.cluster}</span>{r.name}
                              {canOpen && <div style={{ fontSize: '11px', fontWeight: '500', color: C.muted, marginLeft: '42px' }}>{r.skills.length} skill{r.skills.length === 1 ? '' : 's'} · click to see them</div>}
                            </td>
                            <td style={{ ...td, fontWeight: '700', color: r.gap_percentage == null ? C.muted : C.red, whiteSpace: 'nowrap' }}>
                              {r.gap_percentage == null ? 'Not asked for' : `${r.gap_percentage}%`}
                            </td>
                            <td style={{ ...td, minWidth: '170px' }}>
                              {r.total > 0 ? <>
                                <div style={{ display: 'flex', height: '8px', borderRadius: '99px', overflow: 'hidden', background: C.line }}>
                                  {[['strong_count', C.green], ['developing_count', C.amber], ['gap_count', C.red]].map(([k, col]) => (
                                    <div key={k} style={{ width: `${pct(r[k], r.total)}%`, background: col }} />
                                  ))}
                                </div>
                                <div style={{ fontSize: '11px', color: C.muted, marginTop: '3px' }}>{r.strong_count} · {r.developing_count} · {r.gap_count}</div>
                              </> : '—'}
                            </td>
                            <td style={{ ...td, fontSize: '12px' }}>
                              {r.top_gaps.length ? r.top_gaps.map(g => `${g.skill_name} (${g.gap_count})`).join(', ') : '—'}
                            </td>
                          </tr>,
                          open && (
                            <tr key={`${r.cluster}-skills`}>
                              <td colSpan={4} style={{ padding: '6px 12px 14px 42px', background: '#fff7f8', borderBottom: `1px solid ${C.line}` }}>
                                <div style={{ fontSize: '12px', color: C.muted, margin: '2px 0 8px' }}>
                                  Every skill in cluster {r.cluster}, most gaps first. Counts are skill results in the latest assessments
                                  (one per student). Click a skill to see the students.
                                </div>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                  <thead><tr>{['Skill', 'Category', 'Gap %', 'Strong', 'Developing', 'Gap', 'Assessments'].map(h =>
                                    <th key={h} style={{ ...th, background: 'transparent', fontSize: '10px' }}>{h}</th>)}</tr></thead>
                                  <tbody>
                                    {r.skills.map(sk => {
                                      const skOpen = mqfSkill === sk.skill_id
                                      const shown = (skillStudents || []).filter(x => x.match_status === skillResult)
                                      return [
                                      <tr key={sk.skill_name} onClick={() => { setMqfSkill(skOpen ? null : sk.skill_id); setSkillResult(sk.gap_count ? 'gap' : sk.developing_count ? 'developing' : 'strong') }}
                                        aria-expanded={skOpen} title={skOpen ? 'Hide the students' : 'Show the students'}
                                        style={{ cursor: 'pointer', background: skOpen ? '#ffeef1' : undefined }}>
                                        <td style={{ ...td, color: C.ink, fontWeight: '500' }}>
                                          <span style={{ display: 'inline-block', width: '16px', color: C.muted }}>{skOpen ? '▾' : '▸'}</span>{sk.skill_name}
                                        </td>
                                        <td style={td}>{categoryLabel(sk.category)}</td>
                                        <td style={{ ...td, fontWeight: '700', color: sk.gap_percentage == null ? C.muted : sk.gap_percentage >= 50 ? C.red : sk.gap_percentage >= 25 ? C.amber : C.green }}>
                                          {sk.gap_percentage == null ? '—' : `${sk.gap_percentage}%`}
                                        </td>
                                        <td style={{ ...td, color: C.green }}>{sk.strong_count}</td>
                                        <td style={{ ...td, color: C.amber }}>{sk.developing_count}</td>
                                        <td style={{ ...td, color: C.red, fontWeight: '600' }}>{sk.gap_count}</td>
                                        <td style={td}>{sk.total}</td>
                                      </tr>,
                                      skOpen && (
                                        <tr key={`${sk.skill_name}-students`}>
                                          <td colSpan={7} style={{ padding: '8px 10px 12px 26px', background: '#fff', borderBottom: `1px solid ${C.line}` }}>
                                            {/* Gap / Developing / Strong: who is behind each number */}
                                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px', alignItems: 'center' }}>
                                              {[['gap', 'Gap', sk.gap_count, C.red], ['developing', 'Developing', sk.developing_count, C.amber], ['strong', 'Strong', sk.strong_count, C.green]].map(([k, lbl, n, col]) => (
                                                <button key={k} type="button" onClick={() => setSkillResult(k)} aria-pressed={skillResult === k}
                                                  style={{ padding: '5px 11px', fontSize: '12px', fontWeight: '600', borderRadius: '999px', cursor: 'pointer',
                                                           border: `1.5px solid ${col}`, background: skillResult === k ? col : '#fff', color: skillResult === k ? '#fff' : col }}>
                                                  {lbl} ({n})
                                                </button>
                                              ))}
                                              <span style={{ fontSize: '11px', color: C.muted }}>Students whose latest assessment asked for {sk.skill_name}. Click a student to open their record.</span>
                                            </div>
                                            {skillStudents == null ? <div style={{ color: C.muted, fontSize: '12px', padding: '6px 0' }}>Loading…</div>
                                              : shown.length === 0 ? <div style={{ color: C.muted, fontSize: '12px', padding: '6px 0' }}>No student in this group.</div> : (
                                              <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
                                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                  <thead><tr>{['Student', 'Student ID', 'Programme', 'Year', 'Readiness'].map(h =>
                                                    <th key={h} style={{ ...th, fontSize: '10px', position: 'sticky', top: 0 }}>{h}</th>)}</tr></thead>
                                                  <tbody>
                                                    {shown.slice(0, 300).map(st => (
                                                      <tr key={st.user_id} onClick={e => { e.stopPropagation(); openStudent(st.user_id) }} style={{ cursor: 'pointer' }}>
                                                        <td style={{ ...td, color: C.blue, fontWeight: '500', whiteSpace: 'nowrap' }}>{st.full_name}</td>
                                                        <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{st.student_number || '—'}</td>
                                                        <td style={td}>{st.programme || '—'}</td>
                                                        <td style={{ ...td, whiteSpace: 'nowrap' }}>{st.year_of_study != null ? `Year ${st.year_of_study}` : '—'}</td>
                                                        <td style={{ ...td, fontWeight: '700', color: scoreColor(num(st.readiness_score)) }}>
                                                          {st.readiness_score == null ? '—' : `${num(st.readiness_score)}%`}
                                                        </td>
                                                      </tr>
                                                    ))}
                                                  </tbody>
                                                </table>
                                                {shown.length > 300 && <div style={{ fontSize: '11px', color: C.muted, padding: '6px' }}>Showing the first 300 of {shown.length}.</div>}
                                              </div>
                                            )}
                                          </td>
                                        </tr>
                                      ),
                                      ]
                                    })}
                                  </tbody>
                                </table>
                              </td>
                            </tr>
                          ),
                          ]
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

          {gapFilter && roleGaps == null ? <Empty>Loading…</Empty> : shownGaps.length === 0 ? <Empty>No assessment data for this selection yet.</Empty> : (
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
              <option value="assessed">Assessed (any status)</option>
              {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
            <select aria-label="Filter by programme" value={programme} onChange={e => { setProgramme(e.target.value); setShownRows(PAGE_SIZE) }} style={{ ...input, maxWidth: '280px' }}>
              <option value="">All programmes</option>
              {programmes.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select aria-label="Filter by year of study" value={year} onChange={e => { setYear(e.target.value); setShownRows(PAGE_SIZE) }} style={input}>
              <option value="">All years</option>
              {years.map(y => <option key={y} value={String(y)}>Year {y}</option>)}
              {noYear && <option value="none">Year not set</option>}
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
            {band != null && (
              <button style={{ ...btn(false), color: C.blue }} onClick={() => setBand(null)} title="Remove this filter">
                Readiness {band}–{band === 90 ? 100 : band + 9}% ✕
              </button>
            )}
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
                  <SortTh label="Year" k="year_of_study" sort={sort} setSort={setSort} />
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
                  <tr><td colSpan={11} style={{ ...td, textAlign: 'center', padding: '32px', color: C.muted }}>No students match.</td></tr>
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
                      <td style={{ ...td, whiteSpace: 'nowrap' }}>{s.year_of_study != null ? `Year ${s.year_of_study}` : '—'}</td>
                      <td style={td}>{s.target_role || '—'}</td>
                      {/* Latest Job Readiness Score, with the role it was assessed against */}
                      <td style={{ ...td, whiteSpace: 'nowrap' }}>
                        {score == null ? <span style={{ color: C.muted }} title="This student has not run an assessment yet">Not assessed</span> : <>
                          <div style={{ fontSize: '14px', fontWeight: '700', color: (STATUS[s.status] || STATUS.none).color }}>{score}%</div>
                          <div style={{ fontSize: '11px', color: C.muted }}>{s.assessed_role || 'Job description'}</div>
                        </>}
                      </td>
                      <td style={{ ...td, maxWidth: '260px' }}>
                        <Pill status={s.status} title={s.status_reason} />
                        {['needs_support', 'improving', 'getting_started'].includes(s.status) &&
                          <div style={{ fontSize: '11px', color: C.muted, marginTop: '4px', lineHeight: 1.35 }}>{s.status_reason}</div>}
                      </td>
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
            {/* Each card opens only what its number counts; click it again (or "Show all") to go back */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '16px', marginBottom: '16px' }}>
              {PVIEWS.map(v => (
                <StatCard key={v.id} label={v.label} value={progress.totals[v.total]} color={v.color}
                  sub={v.sub ? v.sub(progress.totals, total) : undefined}
                  hint={v.hint} active={pview === v.id} onClick={() => setPview(pview === v.id ? '' : v.id)} />
              ))}
            </div>

            {pview ? (() => {
              const v = PVIEWS.find(x => x.id === pview)
              const studentRows = pview === 'active' ? progress.students : progress.students.filter(x => x.completed > 0)
              return (
                <div style={{ ...card, borderTop: `3px solid ${v.color}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '6px' }}>
                    <div style={heading}>{v.title} ({progress.totals[v.total]})</div>
                    <button style={{ ...btn(false), color: C.blue }} onClick={() => setPview('')}>Show all progress ✕</button>
                  </div>
                  <div style={{ fontSize: '12px', color: C.muted, marginBottom: '12px' }}>{v.explain} Click a student to open their full record.</div>

                  {v.kind === 'activities' ? (
                    !acts || acts.status !== pview ? <div style={{ color: C.muted, padding: '12px' }}>Loading…</div>
                      : acts.activities.length === 0 ? <Empty>{v.empty}</Empty> : (() => {
                        // One row per student with how many; click a student to see their activities
                        const groups = []
                        const byId = {}
                        for (const a of acts.activities) {
                          if (!byId[a.user_id]) { byId[a.user_id] = { ...a, items: [] }; groups.push(byId[a.user_id]) }
                          byId[a.user_id].items.push(a)
                        }
                        groups.sort((x, y) => y.items.length - x.items.length || (x.full_name || '').localeCompare(y.full_name || ''))
                        return (
                          <div style={{ overflowX: 'auto', maxHeight: '620px' }}>
                            <div style={{ fontSize: '12px', color: C.muted, margin: '-4px 0 10px' }}>
                              {acts.total} {v.unit} by {groups.length} student{groups.length === 1 ? '' : 's'}. Click a student to see their {v.unit}.
                            </div>
                            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
                              <thead><tr>{['', 'Student', 'Student ID', v.countLabel, `Latest ${v.dateLabel.toLowerCase()}`, ''].map((h, k) =>
                                <th key={k} style={{ ...th, position: 'sticky', top: 0, zIndex: 1 }}>{h}</th>)}</tr></thead>
                              <tbody>
                                {groups.map((g, i) => {
                                  const open = openStu === g.user_id
                                  return [
                                    <tr key={g.user_id} onClick={() => setOpenStu(open ? null : g.user_id)} aria-expanded={open}
                                      style={{ background: open ? '#fff7f8' : i % 2 === 0 ? C.bg : '#fff', cursor: 'pointer' }}>
                                      <td style={{ ...td, width: '28px', color: C.muted }}>{open ? '▾' : '▸'}</td>
                                      <td style={{ ...td, fontSize: '13px', color: C.ink, fontWeight: '600', whiteSpace: 'nowrap' }}>{g.full_name}</td>
                                      <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{g.student_number || '—'}</td>
                                      <td style={{ ...td, fontSize: '15px', fontWeight: '700', color: v.color }}>{g.items.length}</td>
                                      <td style={{ ...td, whiteSpace: 'nowrap' }}>{fmtDate(g.items[0][v.dateKey] || g.items[0].happened_at)}</td>
                                      <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                                        <button style={{ ...btn(false), padding: '5px 10px', fontSize: '12px', color: C.blue }}
                                          onClick={e => { e.stopPropagation(); openStudent(g.user_id) }}>Open record →</button>
                                      </td>
                                    </tr>,
                                    open && (
                                      <tr key={`${g.user_id}-items`}>
                                        <td colSpan={6} style={{ padding: '4px 12px 14px 40px', background: '#fff7f8', borderBottom: `1px solid ${C.line}` }}>
                                          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                            <thead><tr>{['Activity', 'Type', 'Skill', v.dateLabel, ...(pview === 'completed' ? ['Evidence'] : [])].map(h =>
                                              <th key={h} style={{ ...th, background: 'transparent', fontSize: '10px' }}>{h}</th>)}</tr></thead>
                                            <tbody>
                                              {g.items.map((a, k) => (
                                                <tr key={k}>
                                                  <td style={{ ...td, color: C.ink, fontWeight: '500' }}>{a.resource_title}</td>
                                                  <td style={{ ...td, textTransform: 'capitalize' }}>{a.resource_type || '—'}</td>
                                                  <td style={td}>{a.skill_name || '—'}</td>
                                                  <td style={{ ...td, whiteSpace: 'nowrap' }}>{fmtDate(a[v.dateKey] || a.happened_at)}</td>
                                                  {pview === 'completed' && <td style={td}>{a.evidence_count ? `${a.evidence_count} file${a.evidence_count === 1 ? '' : 's'}` : '—'}</td>}
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </td>
                                      </tr>
                                    ),
                                  ]
                                })}
                              </tbody>
                            </table>
                            {acts.total > acts.activities.length &&
                              <div style={{ fontSize: '12px', color: C.muted, padding: '10px' }}>Counted from the newest {acts.activities.length} of {acts.total}.</div>}
                          </div>
                        )
                      })()
                  ) : (
                    studentRows.length === 0 ? <Empty>{v.empty}</Empty> : (
                      <div style={{ overflowX: 'auto', maxHeight: '560px' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '760px' }}>
                          <thead><tr>{['Name', 'Student ID', 'Target role', 'Completed', 'In progress', 'Saved', 'Last completed'].map(h =>
                            <th key={h} style={{ ...th, position: 'sticky', top: 0 }}>{h}</th>)}</tr></thead>
                          <tbody>
                            {studentRows.slice(0, 500).map((x, i) => (
                              <tr key={x.user_id} onClick={() => openStudent(x.user_id)} style={{ background: i % 2 === 0 ? C.bg : '#fff', cursor: 'pointer' }}>
                                <td style={{ ...td, fontSize: '13px', color: C.blue, fontWeight: '500', whiteSpace: 'nowrap' }}>{x.full_name}</td>
                                <td style={{ ...td, fontFamily: 'Consolas, monospace' }}>{x.student_number || '—'}</td>
                                <td style={td}>{x.target_role || '—'}</td>
                                <td style={{ ...td, color: C.green, fontWeight: '700' }}>{x.completed}</td>
                                <td style={{ ...td, color: C.blue, fontWeight: '600' }}>{x.in_progress}</td>
                                <td style={td}>{x.saved}</td>
                                <td style={{ ...td, whiteSpace: 'nowrap' }}>{fmtDate(x.last_completed)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {studentRows.length > 500 && <div style={{ fontSize: '12px', color: C.muted, padding: '10px' }}>Showing the first 500 of {studentRows.length}.</div>}
                      </div>
                    )
                  )}
                </div>
              )
            })() : <>
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
            </>}
          </>
        )
      )}
    </div>
  )
}
