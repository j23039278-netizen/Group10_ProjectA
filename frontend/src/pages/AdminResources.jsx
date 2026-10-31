// SEAGAS — Learning Resources (recommendations library, FR-16; admin and advisor portals)
// The courses, certifications and projects the recommendation engine suggests for
// each skill gap. Staff can add resources, edit the ones added on the website, and
// switch them on or off; inactive resources are no longer recommended. Advisors add
// resources for the skills of their courses and change the ones of their courses or
// that they added (can_edit from routers/library.py). Seed resources come from
// database/seed_recommendations_library_final.sql and are only switched on/off here,
// the same rule as the skills and roles library.
import { useState, useEffect } from 'react'
import { authAPI } from '../api/client'
import { libraryAPI } from '../api/library'
import { label as labelText } from '../utils/labels'
import { COURSES, coursesText } from '../utils/courses'
import { C, card, th, td, input, label, btn, smallBtn, heading, errorText } from './admin/adminStyles'
import { Modal, Alert, StatusPill, SourcePill, SharedNote } from './admin/AdminUi'

const TYPES = ['course', 'certification', 'project', 'workshop', 'competition', 'internship']
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced']
const select = { ...input, width: 'auto' }

// ── Add / edit a resource ────────────────────────────────────
function ResourceModal({ resource, skills, allowed, onClose, onSaved }) {
  const editing = !!resource
  const [form, setForm] = useState({
    skill_id: resource?.skill_id || '', resource_title: resource?.resource_title || '',
    resource_type: resource?.resource_type || 'course', provider: resource?.provider || '',
    url: resource?.url || '', duration_hours: resource?.duration_hours ?? '',
    cost: resource?.cost || 'Free', difficulty: resource?.difficulty || 'beginner',
    description: resource?.description || '',
  })
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.skill_id) return setError('Please choose the skill this resource helps with.')
    if (!form.resource_title.trim()) return setError('Please enter the title.')
    const url = form.url.trim()
    if (url && !/^https?:\/\//i.test(url)) return setError('The link must start with http:// or https://')
    const body = {
      skill_id: form.skill_id, resource_title: form.resource_title.trim(),
      resource_type: form.resource_type, provider: form.provider.trim() || null, url: url || null,
      duration_hours: form.duration_hours === '' ? null : parseInt(form.duration_hours, 10),
      cost: form.cost.trim() || 'Free', difficulty: form.difficulty,
      description: form.description.trim() || null,
    }
    setSaving(true)
    setError('')
    try {
      const res = editing ? await libraryAPI.updateResource(resource.resource_id, body) : await libraryAPI.createResource(body)
      onSaved(res.data, editing)
    } catch (err) {
      setError(errorText(err, 'Could not save the resource.'))
      setSaving(false)
    }
  }

  const activeSkills = skills.filter(s => s.skill_id === form.skill_id ||
    (s.is_active && (s.courses || []).some(c => allowed.includes(c))))

  return (
    <Modal title={editing ? `Edit ${resource.resource_title}` : 'Add learning resource'} onClose={onClose} width="560px">
      <form onSubmit={submit} noValidate>
        {error && <Alert>{error}</Alert>}
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="rs-skill">Skill it closes</label>
          <select id="rs-skill" style={input} value={form.skill_id} onChange={set('skill_id')} autoFocus>
            <option value="">Choose a skill…</option>
            {activeSkills.map(s => <option key={s.skill_id} value={s.skill_id}>{s.skill_name}</option>)}
          </select>
          <div style={{ fontSize: '11px', color: C.muted, marginTop: '4px' }}>
            Students with this skill as a gap or developing skill will see this resource.
          </div>
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="rs-title">Title</label>
          <input id="rs-title" style={input} value={form.resource_title} onChange={set('resource_title')} placeholder="e.g. Kubernetes for Beginners" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
          <div>
            <label style={label} htmlFor="rs-type">Type</label>
            <select id="rs-type" style={{ ...input, textTransform: 'capitalize' }} value={form.resource_type} onChange={set('resource_type')}>
              {TYPES.map(t => <option key={t} value={t}>{labelText(t)}</option>)}
            </select>
          </div>
          <div>
            <label style={label} htmlFor="rs-diff">Difficulty</label>
            <select id="rs-diff" style={{ ...input, textTransform: 'capitalize' }} value={form.difficulty} onChange={set('difficulty')}>
              {DIFFICULTIES.map(d => <option key={d} value={d}>{labelText(d)}</option>)}
            </select>
          </div>
          <div>
            <label style={label} htmlFor="rs-prov">Provider</label>
            <input id="rs-prov" style={input} value={form.provider} onChange={set('provider')} placeholder="e.g. Coursera" />
          </div>
          <div>
            <label style={label} htmlFor="rs-cost">Cost</label>
            <input id="rs-cost" style={input} value={form.cost} onChange={set('cost')} placeholder="Free" />
          </div>
          <div>
            <label style={label} htmlFor="rs-hours">Duration (hours)</label>
            <input id="rs-hours" type="number" min="0" style={input} value={form.duration_hours} onChange={set('duration_hours')} />
          </div>
          <div>
            <label style={label} htmlFor="rs-url">Link</label>
            <input id="rs-url" style={input} value={form.url} onChange={set('url')} placeholder="https://…" />
          </div>
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="rs-desc">Description</label>
          <textarea id="rs-desc" rows={3} style={{ ...input, resize: 'vertical', fontFamily: 'inherit' }} value={form.description} onChange={set('description')} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Saving…' : editing ? 'Save' : 'Add resource'}</button>
        </div>
      </form>
    </Modal>
  )
}

// ── Page ─────────────────────────────────────────────────────
export default function AdminResources() {
  const [myCourses, setMyCourses] = useState([])     // courses the user manages (every course for admins)
  const [isAdmin, setIsAdmin]     = useState(false)
  const [course, setCourse]       = useState('')     // '' = all; resources of skills of one course
  const [resources, setResources] = useState([])
  const [skills, setSkills]       = useState([])
  const [search, setSearch]       = useState('')
  const [type, setType]           = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [notice, setNotice]       = useState('')
  const [modal, setModal]         = useState(null)   // null | 'new' | resource
  const [busy, setBusy]           = useState(null)

  const load = () => Promise.all([libraryAPI.resources(), libraryAPI.skills()])
    .then(([r, s]) => { setResources(r.data); setSkills(s.data); setError('') })
    .catch(err => setError(errorText(err, 'Could not load the learning resources.')))
    .finally(() => setLoading(false))

  useEffect(() => {
    authAPI.me().then(r => { setMyCourses(r.data.advisor_courses || []); setIsAdmin(r.data.role === 'admin') }).catch(() => {})
    load()
  }, [])

  const toggle = async (r) => {
    setBusy(r.resource_id)
    setNotice('')
    try {
      await libraryAPI.updateResource(r.resource_id, { is_active: !r.is_active })
      setNotice(`${r.resource_title} is now ${r.is_active ? 'inactive: it is no longer recommended' : 'active'}.`)
      await load()
    } catch (err) {
      setError(errorText(err, 'Could not change it.'))
    } finally {
      setBusy(null)
    }
  }

  const q = search.trim().toLowerCase()
  const forCourse = (r) => !course || (r.skill_courses || []).includes(course)
  const shown = resources.filter(r =>
    forCourse(r) &&
    (showInactive || r.is_active) &&
    (!type || r.resource_type === type) &&
    (!q || [r.resource_title, r.skill_name, r.provider].some(v => (v || '').toLowerCase().includes(q)))
  )
  const active = resources.filter(r => r.is_active)
  const covered = new Set(active.map(r => r.skill_id)).size
  const activeSkills = skills.filter(s => s.is_active).length

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Learning Resources</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '760px' }}>
          {active.length} active resources covering {covered} of {activeSkills} active skills. The recommendation engine suggests these for the skill gaps students have.
          Entries marked <SourcePill source="admin" /> were added on the website and can be edited.
          Seed entries come from database/seed_recommendations_library_final.sql: edit them there; here they can only be switched on or off.
          {!isAdmin && <> You can add resources for the skills of your courses ({coursesText(myCourses)}) and change the ones you added or that only your courses use.</>}
        </div>
      </div>

      {notice && <Alert type="success">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}

      {/* Course: resources for the skills of one course */}
      <div role="tablist" aria-label="Course" style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
        {[{ id: '', label: 'All courses' }, ...COURSES].map(c => {
          const selected = course === c.id
          return (
            <button key={c.id || 'all'} role="tab" aria-selected={selected} onClick={() => setCourse(c.id)}
              style={{ padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', cursor: 'pointer',
                       background: selected ? C.blue : '#fff', color: selected ? '#fff' : C.body,
                       border: `1.5px solid ${selected ? C.blue : C.line}` }}>
              {c.label} ({active.filter(r => !c.id || (r.skill_courses || []).includes(c.id)).length})
            </button>
          )
        })}
      </div>

      <div style={{ ...card, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
          <div style={heading}>Resources</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <input type="search" aria-label="Search resources" placeholder="Search title, skill or provider"
              style={{ ...input, width: '240px', maxWidth: '100%' }} value={search} onChange={e => setSearch(e.target.value)} />
            <select aria-label="Filter by type" style={{ ...select, textTransform: 'capitalize' }} value={type} onChange={e => setType(e.target.value)}>
              <option value="">All types</option>
              {TYPES.map(t => <option key={t} value={t}>{labelText(t)}</option>)}
            </select>
            <label style={{ fontSize: '12px', color: C.body, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input type="checkbox" checked={showInactive} onChange={e => setShowInactive(e.target.checked)} /> Show inactive
            </label>
            <button style={btn('primary')} onClick={() => { setNotice(''); setModal('new') }}>+ Add resource</button>
          </div>
        </div>
        <div style={{ overflow: 'auto', maxHeight: '620px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '960px' }}>
            <thead><tr>{['Title', 'Skill', 'Type', 'Provider', 'Difficulty', 'Students', 'Source', 'Status', ''].map(h =>
              <th key={h} style={{ ...th, position: 'sticky', top: 0 }}>{h}</th>)}</tr></thead>
            <tbody>
              {shown.length === 0 ? (
                <tr><td colSpan={9} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No resources match.</td></tr>
              ) : shown.map(r => (
                <tr key={r.resource_id} style={{ opacity: r.is_active ? 1 : 0.6 }}>
                  <td style={{ ...td, color: C.ink, fontWeight: '600' }}>
                    {r.url ? <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ color: C.ink }}>{r.resource_title}</a> : r.resource_title}
                    <div style={{ fontSize: '11px', color: C.muted, fontWeight: '400', marginTop: '2px' }}>
                      {[r.cost, r.duration_hours != null && `${r.duration_hours} h`].filter(Boolean).join(' · ')}
                    </div>
                  </td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>{r.skill_name}</td>
                  <td style={{ ...td, textTransform: 'capitalize' }}>{r.resource_type}</td>
                  <td style={td}>{r.provider || '—'}</td>
                  <td style={{ ...td, textTransform: 'capitalize' }}>{r.difficulty}</td>
                  <td style={td} title="Started / completed by students">{r.student_count} / {r.completed_count}</td>
                  <td style={td}><SourcePill source={r.source} /></td>
                  <td style={td}><StatusPill active={r.is_active} /></td>
                  <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {r.source === 'admin' && r.can_edit && (
                      <button style={{ ...smallBtn(), marginRight: '6px' }} onClick={() => { setNotice(''); setModal(r) }}>Edit</button>
                    )}
                    {r.can_edit ? (
                      <button style={smallBtn(r.is_active ? 'danger' : 'secondary')} disabled={busy === r.resource_id} onClick={() => toggle(r)}>
                        {r.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    ) : <SharedNote />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <ResourceModal resource={modal === 'new' ? null : modal} skills={skills} allowed={myCourses} onClose={() => setModal(null)}
          onSaved={(r, edited) => { setModal(null); setNotice(`${r.resource_title} ${edited ? 'saved' : 'added'}.`); load() }} />
      )}
    </div>
  )
}
