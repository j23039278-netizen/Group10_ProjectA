// SEAGAS — Student Profile Page
import { useState, useEffect } from 'react'
import { studentAPI, fileAPI } from '../api/client'
import { label } from '../utils/labels'
import EvidenceFiles, { PendingFiles } from '../components/EvidenceFiles'
import { MAX_FILES } from '../components/evidenceRules'

const ROLES = ['Data Analyst','Data Scientist','Software Developer','Cybersecurity Analyst','Cloud Engineer','Web Developer']
const CATEGORIES = ['Technical','AI_Digital','Analytical','Soft']
const PROFICIENCY = ['beginner','intermediate','advanced']
const PROJECT_TYPES = ['academic','personal','internship','competition']
const EMPTY_PROJECT = { project_title: '', description: '', technologies: '', project_type: 'academic', year_completed: '' }
const EMPTY_CERT    = { cert_name: '', issuer: '', issue_date: '', expiry_date: '' }
const errMsg = (e, fallback) => {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return 'Please check the details: ' + d.map(x => x.msg).join('; ')
  return typeof d === 'string' ? d : fallback
}

export default function Profile() {
  const [profile,  setProfile]  = useState(null)
  const [skills,   setSkills]   = useState([])
  const [library,  setLibrary]  = useState([])
  const [projects, setProjects] = useState([])
  const [certs,    setCerts]    = useState([])
  const [tab,      setTab]      = useState('info')
  const [loading,  setLoading]  = useState(true)
  const [saving,   setSaving]   = useState(false)
  const [msg,      setMsg]      = useState('')

  // Profile form state
  const [form, setForm] = useState({
    programme: '', university: '', gpa: '', expected_graduation: '',
    year_of_study: '', target_role: '', career_interests: []
  })

  // Add skill state
  const [selSkill, setSelSkill]   = useState('')
  const [selLevel, setSelLevel]   = useState('intermediate')
  const [catFilter, setCatFilter] = useState('')

  // Add / edit project state (editProjId: the project being edited, null when adding)
  const [projForm, setProjForm] = useState(EMPTY_PROJECT)
  const [editProjId, setEditProjId] = useState(null)

  // Add / edit cert state
  const [certForm, setCertForm] = useState(EMPTY_CERT)
  const [editCertId, setEditCertId] = useState(null)
  const [itemError, setItemError]   = useState('')

  // Proof files picked in the Add / Edit forms; uploaded once the record is saved
  const [projFiles, setProjFiles]   = useState([])
  const [certFiles, setCertFiles]   = useState([])
  const [savingItem, setSavingItem] = useState(false)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    try {
      const [libRes, skillRes, projRes, certRes] = await Promise.all([
        studentAPI.getSkillLibrary(),
        studentAPI.getSkills(),
        studentAPI.getProjects(),
        studentAPI.getCerts(),
      ])
      setLibrary(libRes.data)
      setSkills(skillRes.data)
      setProjects(projRes.data)
      setCerts(certRes.data)

      try {
        const profRes = await studentAPI.getProfile()
        setProfile(profRes.data)
        setForm({
          programme:           profRes.data.programme || '',
          university:          profRes.data.university || '',
          gpa:                 profRes.data.gpa || '',
          expected_graduation: profRes.data.expected_graduation || '',
          year_of_study:       profRes.data.year_of_study || '',
          target_role:         profRes.data.target_role || '',
          career_interests:    profRes.data.career_interests || [],
        })
      } catch {}
    } finally {
      setLoading(false)
    }
  }

  const saveProfile = async () => {
    setSaving(true)
    try {
      if (profile) {
        await studentAPI.updateProfile(form)
      } else {
        await studentAPI.createProfile(form)
      }
      setMsg('Profile saved successfully!')
      loadAll()
    } catch (e) {
      setMsg('Error saving profile.')
    } finally {
      setSaving(false)
      setTimeout(() => setMsg(''), 3000)
    }
  }

  const addSkill = async () => {
    if (!selSkill) return
    try {
      await studentAPI.addSkill({ skill_id: selSkill, proficiency_level: selLevel })
      setSelSkill('')
      loadAll()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error adding skill')
    }
  }

  const removeSkill = async (skillId) => {
    try {
      await studentAPI.removeSkill(skillId)
      loadAll()
    } catch {}
  }

  // Upload the form's files one by one to the saved record; returns the ones that failed
  const uploadPending = async (files, upload) => {
    const failed = []
    for (const f of files) {
      try {
        await upload(f)
      } catch (e) {
        failed.push(`${f.name} (${errMsg(e, 'upload failed')})`)
      }
    }
    return failed
  }

  const saveProject = async () => {
    if (!projForm.project_title.trim()) return setItemError('Please enter the project title.')
    const body = {
      ...projForm,
      project_title: projForm.project_title.trim(),
      technologies: projForm.technologies.split(',').map(t => t.trim()).filter(Boolean),
      year_completed: projForm.year_completed ? parseInt(projForm.year_completed) : null,
    }
    setSavingItem(true)
    try {
      let id = editProjId
      if (id) await studentAPI.updateProject(id, body)
      else id = (await studentAPI.addProject(body)).data.project_id
      const failed = await uploadPending(projFiles, f => fileAPI.uploadToProject(id, f))
      cancelProject()
      if (failed.length) setItemError(`The project was saved, but these files were not attached: ${failed.join('; ')}`)
      loadAll()
    } catch (e) {
      setItemError(errMsg(e, 'Could not save the project.'))
    } finally {
      setSavingItem(false)
    }
  }

  const editProject = (p) => {
    setItemError('')
    setEditProjId(p.project_id)
    setProjForm({
      project_title: p.project_title || '', description: p.description || '',
      technologies: (p.technologies || []).join(', '), project_type: p.project_type || 'academic',
      year_completed: p.year_completed || '',
    })
  }

  const cancelProject = () => { setEditProjId(null); setProjForm(EMPTY_PROJECT); setProjFiles([]); setItemError('') }

  const deleteProject = async (p) => {
    if (!window.confirm(`Delete the project "${p.project_title}"?`)) return
    try {
      await studentAPI.deleteProject(p.project_id)
      if (editProjId === p.project_id) cancelProject()
      loadAll()
    } catch (e) {
      setItemError(errMsg(e, 'Could not delete the project.'))
    }
  }

  const saveCert = async () => {
    if (!certForm.cert_name.trim()) return setItemError('Please enter the certification name.')
    if (certForm.issue_date && certForm.expiry_date && certForm.expiry_date < certForm.issue_date)
      return setItemError('The expiry date cannot be before the issue date.')
    const body = {
      ...certForm,
      cert_name:   certForm.cert_name.trim(),
      issue_date:  certForm.issue_date  || null,
      expiry_date: certForm.expiry_date || null,
    }
    setSavingItem(true)
    try {
      let id = editCertId
      if (id) await studentAPI.updateCert(id, body)
      else id = (await studentAPI.addCert(body)).data.cert_id
      const failed = await uploadPending(certFiles, f => fileAPI.uploadToCert(id, f))
      cancelCert()
      if (failed.length) setItemError(`The certification was saved, but these files were not attached: ${failed.join('; ')}`)
      loadAll()
    } catch (e) {
      setItemError(errMsg(e, 'Could not save the certification.'))
    } finally {
      setSavingItem(false)
    }
  }

  const editCert = (c) => {
    setItemError('')
    setEditCertId(c.cert_id)
    setCertForm({ cert_name: c.cert_name || '', issuer: c.issuer || '',
                  issue_date: c.issue_date || '', expiry_date: c.expiry_date || '' })
  }

  const cancelCert = () => { setEditCertId(null); setCertForm(EMPTY_CERT); setCertFiles([]); setItemError('') }

  const deleteCert = async (c) => {
    if (!window.confirm(`Delete the certification "${c.cert_name}"?`)) return
    try {
      await studentAPI.deleteCert(c.cert_id)
      if (editCertId === c.cert_id) cancelCert()
      loadAll()
    } catch (e) {
      setItemError(errMsg(e, 'Could not delete the certification.'))
    }
  }

  const filteredLib = library.filter(s =>
    !catFilter || s.category === catFilter
  ).filter(s =>
    !skills.find(ms => ms.skill_name === s.skill_name)
  )

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  const inp = (val, onChange, placeholder, type='text') => (
    <input type={type} value={val} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#f5f6fa', boxSizing: 'border-box' }}
    />
  )

  const card = (children) => (
    <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
      {children}
    </div>
  )

  const cardTitle = (t) => (
    <div style={{ fontSize: '13px', fontWeight: '700', color: '#1a1f2e', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{t}</div>
  )

  const tabs = ['info','skills','projects','certifications']

  const errorBox = itemError && (
    <div role="alert" style={{ background: '#fee2e2', color: '#dc2626', padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{itemError}</div>
  )
  const rowBtn = (color) => ({ background: 'none', border: '1px solid #e4e6ef', borderRadius: '6px', padding: '4px 10px', fontSize: '12px', fontWeight: '600', color, cursor: 'pointer' })
  const secondaryBtn = { padding: '9px 20px', background: '#fff', color: '#4a5168', border: '1px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer', marginLeft: '8px' }

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>My Profile</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>Manage your employability profile</div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '2px solid #e4e6ef', marginBottom: '20px' }}>
        {tabs.map(t => (
          <button key={t} onClick={() => { setTab(t); setItemError('') }} style={{
            padding: '10px 18px', fontSize: '13px', fontWeight: tab === t ? '600' : '500',
            color: tab === t ? '#2d5be3' : '#4a5168', border: 'none', background: 'none',
            cursor: 'pointer', borderBottom: `2px solid ${tab === t ? '#2d5be3' : 'transparent'}`,
            marginBottom: '-2px', textTransform: 'capitalize'
          }}>{t}</button>
        ))}
      </div>

      {/* TAB: Info */}
      {tab === 'info' && card(
        <>
          {cardTitle('Academic Background')}
          {msg && <div style={{ background: '#dcfce7', color: '#16a34a', padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{msg}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>Programme</label>
              {inp(form.programme, v => setForm({...form, programme: v}), 'e.g. BCS Cyber Security')}
            </div>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>University</label>
              {inp(form.university, v => setForm({...form, university: v}), 'e.g. Swinburne University')}
            </div>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>GPA</label>
              {inp(form.gpa, v => setForm({...form, gpa: v}), 'e.g. 3.25', 'number')}
            </div>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>Expected Graduation</label>
              {inp(form.expected_graduation, v => setForm({...form, expected_graduation: v}), 'e.g. December 2027')}
            </div>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>Year of Study</label>
              <select value={form.year_of_study} onChange={e => setForm({...form, year_of_study: e.target.value})}
                style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                <option value="">Select year</option>
                {[1,2,3,4].map(y => <option key={y} value={y}>Year {y}</option>)}
              </select>
            </div>
            <div><label style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168', display: 'block', marginBottom: '5px' }}>Target Role</label>
              <select value={form.target_role} onChange={e => setForm({...form, target_role: e.target.value})}
                style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                <option value="">Select target role</option>
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <button onClick={saveProfile} disabled={saving} style={{
            marginTop: '16px', padding: '10px 24px', background: '#2d5be3',
            color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px',
            fontWeight: '600', cursor: 'pointer'
          }}>
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </>
      )}

      {/* TAB: Skills */}
      {tab === 'skills' && (
        <>
          {card(
            <>
              {cardTitle('Add Skill')}
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '12px' }}>
                <select value={catFilter} onChange={e => setCatFilter(e.target.value)}
                  style={{ padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                  <option value="">All Categories</option>
                  {CATEGORIES.map(c => <option key={c} value={c}>{label(c)}</option>)}
                </select>
                <select value={selSkill} onChange={e => setSelSkill(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                  <option value="">Select a skill...</option>
                  {filteredLib.map(s => <option key={s.skill_id} value={s.skill_id}>{s.skill_name} ({label(s.category)})</option>)}
                </select>
                <select value={selLevel} onChange={e => setSelLevel(e.target.value)}
                  style={{ padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                  {PROFICIENCY.map(p => <option key={p} value={p}>{label(p)}</option>)}
                </select>
                <button onClick={addSkill} style={{ padding: '8px 18px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
                  Add
                </button>
              </div>
            </>
          )}
          {card(
            <>
              {cardTitle(`My Skills (${skills.length})`)}
              {skills.length === 0
                ? <div style={{ color: '#8b92a8', fontSize: '13px' }}>No skills added yet.</div>
                : skills.map((s, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < skills.length-1 ? '1px solid #e4e6ef' : 'none' }}>
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: '500', color: '#1a1f2e' }}>{s.skill_name}</span>
                      <span style={{ fontSize: '11px', color: '#8b92a8', marginLeft: '8px' }}>{label(s.category)}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        padding: '3px 9px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
                        background: s.proficiency_level === 'advanced' ? '#dcfce7' : s.proficiency_level === 'intermediate' ? '#fef3c7' : '#fee2e2',
                        color: s.proficiency_level === 'advanced' ? '#16a34a' : s.proficiency_level === 'intermediate' ? '#d97706' : '#dc2626',
                      }}>{label(s.proficiency_level)}</span>
                      <button onClick={() => removeSkill(s.skill_id || s.student_skill_id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', fontSize: '14px' }}>✕</button>
                    </div>
                  </div>
                ))
              }
            </>
          )}
        </>
      )}

      {/* TAB: Projects */}
      {tab === 'projects' && (
        <>
          {card(
            <>
              {cardTitle(editProjId ? 'Edit Project' : 'Add Project')}
              {errorBox}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ gridColumn: '1/-1' }}>
                  {inp(projForm.project_title, v => setProjForm({...projForm, project_title: v}), 'Project title *')}
                </div>
                <div style={{ gridColumn: '1/-1' }}>
                  {inp(projForm.description, v => setProjForm({...projForm, description: v}), 'Description')}
                </div>
                <div>
                  {inp(projForm.technologies, v => setProjForm({...projForm, technologies: v}), 'Technologies (comma-separated)')}
                </div>
                <div>
                  {inp(projForm.year_completed, v => setProjForm({...projForm, year_completed: v}), 'Year completed', 'number')}
                </div>
                <div>
                  <select value={projForm.project_type} onChange={e => setProjForm({...projForm, project_type: e.target.value})}
                    style={{ width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                    {PROJECT_TYPES.map(t => <option key={t} value={t}>{label(t)}</option>)}
                  </select>
                </div>
                <div style={{ gridColumn: '1/-1' }}>
                  <label style={{ fontSize: '11px', color: '#8b92a8', display: 'block', marginBottom: '5px' }}>Proof (optional): photo or PDF</label>
                  <PendingFiles files={projFiles} onChange={setProjFiles} onError={setItemError}
                    slots={MAX_FILES - ((projects.find(x => x.project_id === editProjId)?.files || []).length)} />
                </div>
                <div>
                  <button onClick={saveProject} disabled={savingItem} style={{ padding: '9px 20px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: savingItem ? 'wait' : 'pointer' }}>
                    {savingItem ? 'Saving…' : editProjId ? 'Save Changes' : 'Add Project'}
                  </button>
                  {editProjId && <button onClick={cancelProject} style={secondaryBtn}>Cancel</button>}
                </div>
              </div>
            </>
          )}
          {card(
            <>
              {cardTitle(`My Projects (${projects.length})`)}
              {projects.length === 0
                ? <div style={{ color: '#8b92a8', fontSize: '13px' }}>No projects added yet.</div>
                : projects.map((p, i) => (
                  <div key={p.project_id || i} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '12px 0', borderBottom: i < projects.length-1 ? '1px solid #e4e6ef' : 'none', background: editProjId === p.project_id ? '#f5f8ff' : 'transparent' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e' }}>{p.project_title}</div>
                      <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>{p.description}</div>
                      <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '4px' }}>
                        {[p.technologies?.join(', '), label(p.project_type), p.year_completed].filter(Boolean).join(' · ')}
                      </div>
                      <EvidenceFiles files={p.files}
                        onUpload={async f => { await fileAPI.uploadToProject(p.project_id, f); setItemError(''); await loadAll() }}
                        onDelete={async f => { await fileAPI.remove(f.file_id); await loadAll() }}
                        onError={setItemError} />
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start', flexShrink: 0 }}>
                      <button onClick={() => editProject(p)} style={rowBtn('#2d5be3')}>Edit</button>
                      <button onClick={() => deleteProject(p)} style={rowBtn('#dc2626')}>Delete</button>
                    </div>
                  </div>
                ))
              }
            </>
          )}
        </>
      )}

      {/* TAB: Certifications */}
      {tab === 'certifications' && (
        <>
          {card(
            <>
              {cardTitle(editCertId ? 'Edit Certification' : 'Add Certification')}
              {errorBox}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>{inp(certForm.cert_name, v => setCertForm({...certForm, cert_name: v}), 'Certification name *')}</div>
                <div>{inp(certForm.issuer, v => setCertForm({...certForm, issuer: v}), 'Issuer (e.g. AWS, Microsoft)')}</div>
                <div><label style={{ fontSize: '11px', color: '#8b92a8' }}>Issue Date</label>
                  {inp(certForm.issue_date, v => setCertForm({...certForm, issue_date: v}), '', 'date')}
                </div>
                <div><label style={{ fontSize: '11px', color: '#8b92a8' }}>Expiry Date</label>
                  {inp(certForm.expiry_date, v => setCertForm({...certForm, expiry_date: v}), '', 'date')}
                </div>
                <div style={{ gridColumn: '1/-1' }}>
                  <label style={{ fontSize: '11px', color: '#8b92a8', display: 'block', marginBottom: '5px' }}>Proof (optional): photo or PDF</label>
                  <PendingFiles files={certFiles} onChange={setCertFiles} onError={setItemError}
                    slots={MAX_FILES - ((certs.find(x => x.cert_id === editCertId)?.files || []).length)} />
                </div>
                <div>
                  <button onClick={saveCert} disabled={savingItem} style={{ padding: '9px 20px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: savingItem ? 'wait' : 'pointer' }}>
                    {savingItem ? 'Saving…' : editCertId ? 'Save Changes' : 'Add Certification'}
                  </button>
                  {editCertId && <button onClick={cancelCert} style={secondaryBtn}>Cancel</button>}
                </div>
              </div>
            </>
          )}
          {card(
            <>
              {cardTitle(`My Certifications (${certs.length})`)}
              {certs.length === 0
                ? <div style={{ color: '#8b92a8', fontSize: '13px' }}>No certifications added yet.</div>
                : certs.map((c, i) => (
                  <div key={c.cert_id || i} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '12px 0', borderBottom: i < certs.length-1 ? '1px solid #e4e6ef' : 'none', background: editCertId === c.cert_id ? '#f5f8ff' : 'transparent' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e' }}>{c.cert_name}</div>
                      <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>{c.issuer}</div>
                      <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '2px' }}>
                        {c.issue_date && `Issued: ${c.issue_date}`} {c.expiry_date && `· Expires: ${c.expiry_date}`}
                      </div>
                      <EvidenceFiles files={c.files}
                        onUpload={async f => { await fileAPI.uploadToCert(c.cert_id, f); setItemError(''); await loadAll() }}
                        onDelete={async f => { await fileAPI.remove(f.file_id); await loadAll() }}
                        onError={setItemError} />
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start', flexShrink: 0 }}>
                      <button onClick={() => editCert(c)} style={rowBtn('#2d5be3')}>Edit</button>
                      <button onClick={() => deleteCert(c)} style={rowBtn('#dc2626')}>Delete</button>
                    </div>
                  </div>
                ))
              }
            </>
          )}
        </>
      )}
    </div>
  )
}