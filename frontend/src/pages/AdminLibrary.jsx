// SEAGAS — Admin: Skills & Role Library
// Lists every skill and job role template. Admins can add skills and roles, edit
// the ones they added, and switch any of them on or off. The 138 skills and 6
// roles from data/skills/skills_library.csv and the seed files are maintained
// there (start_backend.bat re-applies the seeds), so they are only switched on/off here.
import { useState, useEffect } from 'react'
import { adminAPI } from '../api/admin'
import { C, card, th, td, input, label, btn, smallBtn, heading, errorText } from './admin/adminStyles'
import { Modal, Alert, StatusPill, SourcePill } from './admin/AdminUi'

const CATEGORIES = [
  { id: 'Technical',  label: 'Technical' },
  { id: 'AI_Digital', label: 'AI / Digital' },
  { id: 'Analytical', label: 'Analytical' },
  { id: 'Soft',       label: 'Soft skill' },
]
const CATEGORY_LABEL = Object.fromEntries(CATEGORIES.map(c => [c.id, c.label]))
const LEVELS = ['entry', 'junior', 'mid', 'senior']
const IMPORTANCE = ['required', 'preferred', 'bonus']
const select = { ...input, width: 'auto' }

// ── Add / edit a skill ───────────────────────────────────────
function SkillModal({ skill, onClose, onSaved }) {
  const editing = !!skill
  const [form, setForm] = useState({
    skill_name: skill?.skill_name || '', category: skill?.category || 'Technical',
    subcategory: skill?.subcategory || '', aliases: (skill?.aliases || []).join(', '),
    description: skill?.description || '',
  })
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!editing && !form.skill_name.trim()) return setError('Please enter the skill name.')
    const body = {
      category: form.category, subcategory: form.subcategory.trim() || null,
      aliases: form.aliases.split(',').map(a => a.trim()).filter(Boolean),
      description: form.description.trim() || null,
    }
    setSaving(true)
    setError('')
    try {
      const res = editing
        ? await adminAPI.updateSkill(skill.skill_id, body)
        : await adminAPI.createSkill({ ...body, skill_name: form.skill_name.trim() })
      onSaved(res.data, editing)
    } catch (err) {
      setError(errorText(err, 'Could not save the skill.'))
      setSaving(false)
    }
  }

  return (
    <Modal title={editing ? `Edit ${skill.skill_name}` : 'Add skill'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {error && <Alert>{error}</Alert>}
        {!editing && (
          <div style={{ marginBottom: '12px' }}>
            <label style={label} htmlFor="sk-name">Skill name</label>
            <input id="sk-name" style={input} value={form.skill_name} onChange={set('skill_name')} placeholder="e.g. Kubernetes" autoFocus />
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
          <div>
            <label style={label} htmlFor="sk-cat">Category</label>
            <select id="sk-cat" style={input} value={form.category} onChange={set('category')}>
              {CATEGORIES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label style={label} htmlFor="sk-sub">Subcategory</label>
            <input id="sk-sub" style={input} value={form.subcategory} onChange={set('subcategory')} placeholder="e.g. DevOps" />
          </div>
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="sk-alias">Aliases (comma separated)</label>
          <input id="sk-alias" style={input} value={form.aliases} onChange={set('aliases')} placeholder="e.g. K8s, Kube" />
          <div style={{ fontSize: '11px', color: C.muted, marginTop: '4px' }}>
            Other names for the same skill. The NLP uses them to find this skill in job descriptions.
          </div>
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="sk-desc">Description</label>
          <textarea id="sk-desc" rows={3} style={{ ...input, resize: 'vertical', fontFamily: 'inherit' }} value={form.description} onChange={set('description')} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Saving…' : editing ? 'Save' : 'Add skill'}</button>
        </div>
      </form>
    </Modal>
  )
}

// ── Add / edit a role's details ──────────────────────────────
function RoleModal({ role, onClose, onSaved }) {
  const editing = !!role
  const [form, setForm] = useState({
    role_name: role?.role_name || '', industry_level: role?.industry_level || 'junior',
    description: role?.description || '',
  })
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.role_name.trim()) return setError('Please enter the role name.')
    const body = { role_name: form.role_name.trim(), industry_level: form.industry_level,
                   description: form.description.trim() || null }
    setSaving(true)
    setError('')
    try {
      const res = editing ? await adminAPI.updateRole(role.role_id, body) : await adminAPI.createRole(body)
      onSaved(res.data, editing)
    } catch (err) {
      setError(errorText(err, 'Could not save the role.'))
      setSaving(false)
    }
  }

  return (
    <Modal title={editing ? `Edit ${role.role_name}` : 'Add job role'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        {error && <Alert>{error}</Alert>}
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="ro-name">Role name</label>
          <input id="ro-name" style={input} value={form.role_name} onChange={set('role_name')} placeholder="e.g. DevOps Engineer" autoFocus />
        </div>
        <div style={{ marginBottom: '12px' }}>
          <label style={label} htmlFor="ro-level">Level</label>
          <select id="ro-level" style={input} value={form.industry_level} onChange={set('industry_level')}>
            {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <div style={{ marginBottom: '18px' }}>
          <label style={label} htmlFor="ro-desc">Description</label>
          <textarea id="ro-desc" rows={3} style={{ ...input, resize: 'vertical', fontFamily: 'inherit' }} value={form.description} onChange={set('description')} />
        </div>
        {!editing && (
          <div style={{ fontSize: '12px', color: C.muted, marginBottom: '18px' }}>
            After adding the role, use <b>Skills</b> to choose the skills it requires. Students can only be assessed against it once it has skills.
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button type="button" style={btn('secondary')} onClick={onClose}>Cancel</button>
          <button type="submit" style={btn('primary')} disabled={saving}>{saving ? 'Saving…' : editing ? 'Save' : 'Add role'}</button>
        </div>
      </form>
    </Modal>
  )
}

// ── A role's required skills ─────────────────────────────────
function RoleSkillsModal({ role, allSkills, onClose, onSaved }) {
  const editable = role.source === 'admin'
  const [rows, setRows]     = useState(null)
  const [pick, setPick]     = useState('')
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    adminAPI.roleSkills(role.role_id)
      .then(r => setRows(r.data.skills.map(s => ({ skill_id: s.skill_id, skill_name: s.skill_name, importance: s.importance }))))
      .catch(err => { setError(errorText(err, 'Could not load the skills.')); setRows([]) })
  }, [role.role_id])

  const chosen = new Set((rows || []).map(r => r.skill_id))
  const options = allSkills.filter(s => s.is_active && !chosen.has(s.skill_id))

  const add = () => {
    const s = allSkills.find(x => x.skill_id === pick)
    if (!s) return
    setRows(r => [...r, { skill_id: s.skill_id, skill_name: s.skill_name, importance: 'required' }])
    setPick('')
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      await adminAPI.setRoleSkills(role.role_id, rows.map(r => ({ skill_id: r.skill_id, importance: r.importance })))
      onSaved()
    } catch (err) {
      setError(errorText(err, 'Could not save the skills.'))
      setSaving(false)
    }
  }

  return (
    <Modal title={`${role.role_name}: required skills`} onClose={onClose} width="560px">
      {error && <Alert>{error}</Alert>}
      {!editable && (
        <div style={{ fontSize: '12px', color: C.muted, background: '#f5f6fa', padding: '10px 12px', borderRadius: '8px', marginBottom: '14px' }}>
          This role comes from the seed files (database/seed_job_role_skills.sql), so its skills are changed there, not here.
        </div>
      )}
      {rows === null ? (
        <div style={{ color: C.muted, padding: '20px 0' }}>Loading…</div>
      ) : (
        <>
          <div style={{ maxHeight: '320px', overflowY: 'auto', marginBottom: '12px' }}>
            {rows.length === 0 && <div style={{ color: C.muted, fontSize: '13px', padding: '10px 0' }}>No skills yet.</div>}
            {rows.map((r, i) => (
              <div key={r.skill_id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '1px solid #f0f1f5' }}>
                <div style={{ flex: 1, fontSize: '13px', color: C.ink }}>{r.skill_name}</div>
                {editable ? (
                  <>
                    <select aria-label={`Importance of ${r.skill_name}`} style={{ ...select, padding: '5px 8px' }} value={r.importance}
                      onChange={e => setRows(list => list.map((x, j) => j === i ? { ...x, importance: e.target.value } : x))}>
                      {IMPORTANCE.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                    <button style={smallBtn('danger')} onClick={() => setRows(list => list.filter((_, j) => j !== i))}>Remove</button>
                  </>
                ) : (
                  <span style={{ fontSize: '12px', color: C.muted }}>{r.importance}</span>
                )}
              </div>
            ))}
          </div>
          {editable && (
            <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
              <select aria-label="Skill to add" style={{ ...input, flex: 1 }} value={pick} onChange={e => setPick(e.target.value)}>
                <option value="">Choose a skill to add…</option>
                {options.map(s => <option key={s.skill_id} value={s.skill_id}>{s.skill_name} ({CATEGORY_LABEL[s.category]})</option>)}
              </select>
              <button type="button" style={btn('secondary')} disabled={!pick} onClick={add}>Add</button>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <button type="button" style={btn('secondary')} onClick={onClose}>{editable ? 'Cancel' : 'Close'}</button>
            {editable && <button type="button" style={btn('primary')} disabled={saving} onClick={save}>{saving ? 'Saving…' : 'Save skills'}</button>}
          </div>
        </>
      )}
    </Modal>
  )
}

// ── Page ─────────────────────────────────────────────────────
export default function AdminLibrary() {
  const [skills, setSkills]       = useState([])
  const [roles, setRoles]         = useState([])
  const [search, setSearch]       = useState('')
  const [category, setCategory]   = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [notice, setNotice]       = useState('')
  const [skillModal, setSkillModal] = useState(null)   // null | 'new' | skill
  const [roleModal, setRoleModal]   = useState(null)   // null | 'new' | role
  const [roleSkills, setRoleSkills] = useState(null)   // role whose skills are open
  const [busy, setBusy]           = useState(null)

  const load = () => Promise.all([adminAPI.skills(), adminAPI.roles()])
    .then(([s, r]) => { setSkills(s.data); setRoles(r.data); setError('') })
    .catch(err => setError(errorText(err, 'Could not load the library.')))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const toggle = async (kind, item) => {
    const id = kind === 'skill' ? item.skill_id : item.role_id
    const name = kind === 'skill' ? item.skill_name : item.role_name
    setBusy(id)
    setNotice('')
    try {
      await (kind === 'skill' ? adminAPI.updateSkill(id, { is_active: !item.is_active })
                              : adminAPI.updateRole(id, { is_active: !item.is_active }))
      setNotice(`${name} is now ${item.is_active ? 'inactive: students no longer see it' : 'active'}.`)
      await load()
    } catch (err) {
      setError(errorText(err, 'Could not change it.'))
    } finally {
      setBusy(null)
    }
  }

  const q = search.trim().toLowerCase()
  const shown = skills.filter(s =>
    (showInactive || s.is_active) &&
    (!category || s.category === category) &&
    (!q || s.skill_name.toLowerCase().includes(q) ||
           (s.subcategory || '').toLowerCase().includes(q) ||
           (s.aliases || []).some(a => a.toLowerCase().includes(q)))
  )
  const activeSkills = skills.filter(s => s.is_active).length

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Skills &amp; Role Library</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px', maxWidth: '760px' }}>
          {activeSkills} active skills and {roles.filter(r => r.is_active).length} active job roles.
          Entries marked <SourcePill source="admin" /> were added here and can be edited.
          Seed entries come from data/skills/skills_library.csv and the seed files: edit those there; here they can only be switched on or off.
        </div>
      </div>

      {notice && <Alert type="success">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}

      {/* Job roles */}
      <div style={{ ...card, padding: '20px 24px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', gap: '12px', flexWrap: 'wrap' }}>
          <div style={heading}>Job Role Templates</div>
          <button style={btn('primary')} onClick={() => { setNotice(''); setRoleModal('new') }}>+ Add role</button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
            <thead><tr>{['Role', 'Level', 'Skills', 'Required', 'Source', 'Status', ''].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
            <tbody>
              {roles.map(r => (
                <tr key={r.role_id} style={{ opacity: r.is_active ? 1 : 0.6 }}>
                  <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{r.role_name}</td>
                  <td style={{ ...td, textTransform: 'capitalize' }}>{r.industry_level || '—'}</td>
                  <td style={td}>{r.skill_count}</td>
                  <td style={td}>{r.required_count}</td>
                  <td style={td}><SourcePill source={r.source} /></td>
                  <td style={td}><StatusPill active={r.is_active} /></td>
                  <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <button style={{ ...smallBtn(), marginRight: '6px' }} onClick={() => { setNotice(''); setRoleSkills(r) }}>Skills</button>
                    {r.source === 'admin' && (
                      <button style={{ ...smallBtn(), marginRight: '6px' }} onClick={() => { setNotice(''); setRoleModal(r) }}>Edit</button>
                    )}
                    <button style={smallBtn(r.is_active ? 'danger' : 'secondary')} disabled={busy === r.role_id} onClick={() => toggle('role', r)}>
                      {r.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Skills */}
      <div style={{ ...card, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
          <div style={heading}>Skills Library</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <input type="search" aria-label="Search skills" placeholder="Search skill, subcategory or alias"
              style={{ ...input, width: '240px', maxWidth: '100%' }} value={search} onChange={e => setSearch(e.target.value)} />
            <select aria-label="Filter by category" style={select} value={category} onChange={e => setCategory(e.target.value)}>
              <option value="">All categories</option>
              {CATEGORIES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
            </select>
            <label style={{ fontSize: '12px', color: C.body, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input type="checkbox" checked={showInactive} onChange={e => setShowInactive(e.target.checked)} /> Show inactive
            </label>
            <button style={btn('primary')} onClick={() => { setNotice(''); setSkillModal('new') }}>+ Add skill</button>
          </div>
        </div>
        <div style={{ overflow: 'auto', maxHeight: '560px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '860px' }}>
            <thead><tr>{['Skill', 'Category', 'Subcategory', 'Aliases', 'Roles', 'Source', 'Status', ''].map(h =>
              <th key={h} style={{ ...th, position: 'sticky', top: 0 }}>{h}</th>)}</tr></thead>
            <tbody>
              {shown.length === 0 ? (
                <tr><td colSpan={8} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No skills match.</td></tr>
              ) : shown.map(s => (
                <tr key={s.skill_id} style={{ opacity: s.is_active ? 1 : 0.6 }}>
                  <td style={{ ...td, color: C.ink, fontWeight: '600', whiteSpace: 'nowrap' }}>{s.skill_name}</td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>{CATEGORY_LABEL[s.category] || s.category}</td>
                  <td style={td}>{s.subcategory || '—'}</td>
                  <td style={{ ...td, color: C.muted }}>{(s.aliases || []).join(', ') || '—'}</td>
                  <td style={td}>{s.role_count}</td>
                  <td style={td}><SourcePill source={s.source} /></td>
                  <td style={td}><StatusPill active={s.is_active} /></td>
                  <td style={{ ...td, textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {s.source === 'admin' && (
                      <button style={{ ...smallBtn(), marginRight: '6px' }} onClick={() => { setNotice(''); setSkillModal(s) }}>Edit</button>
                    )}
                    <button style={smallBtn(s.is_active ? 'danger' : 'secondary')} disabled={busy === s.skill_id} onClick={() => toggle('skill', s)}>
                      {s.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {skillModal && (
        <SkillModal skill={skillModal === 'new' ? null : skillModal} onClose={() => setSkillModal(null)}
          onSaved={(s, edited) => { setSkillModal(null); setNotice(`${s.skill_name} ${edited ? 'saved' : 'added'}.`); load() }} />
      )}
      {roleModal && (
        <RoleModal role={roleModal === 'new' ? null : roleModal} onClose={() => setRoleModal(null)}
          onSaved={(r, edited) => {
            setRoleModal(null)
            setNotice(edited ? `${r.role_name} saved.` : `${r.role_name} added. Use Skills to choose its required skills.`)
            load()
          }} />
      )}
      {roleSkills && (
        <RoleSkillsModal role={roleSkills} allSkills={skills} onClose={() => setRoleSkills(null)}
          onSaved={() => { setNotice(`Skills saved for ${roleSkills.role_name}.`); setRoleSkills(null); load() }} />
      )}
    </div>
  )
}
