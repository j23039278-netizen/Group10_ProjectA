// SEAGAS — Student Profile Page
import { useState, useEffect } from 'react'
import { studentAPI } from '../api/client'

const ROLES = ['Data Analyst','Data Scientist','Software Developer','Cybersecurity Analyst','Cloud Engineer','Web Developer']
const CATEGORIES = ['Technical','AI_Digital','Analytical','Soft']
const PROFICIENCY = ['beginner','intermediate','advanced']

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

  // Add project state
  const [projForm, setProjForm] = useState({ project_title: '', description: '', technologies: '', project_type: 'academic', year_completed: '' })

  // Add cert state
  const [certForm, setCertForm] = useState({ cert_name: '', issuer: '', issue_date: '', expiry_date: '' })

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

  const addProject = async () => {
    if (!projForm.project_title) return
    try {
      await studentAPI.addProject({
        ...projForm,
        technologies: projForm.technologies.split(',').map(t => t.trim()).filter(Boolean),
        year_completed: projForm.year_completed ? parseInt(projForm.year_completed) : null,
      })
      setProjForm({ project_title: '', description: '', technologies: '', project_type: 'academic', year_completed: '' })
      loadAll()
    } catch {}
  }

  const addCert = async () => {
    if (!certForm.cert_name) return
    try {
      await studentAPI.addCert({
        ...certForm,
        issue_date:   certForm.issue_date   || null,
        expiry_date:  certForm.expiry_date  || null,
      })
      setCertForm({ cert_name: '', issuer: '', issue_date: '', expiry_date: '' })
      loadAll()
    } catch {}
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

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>My Profile</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>Manage your employability profile</div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '2px solid #e4e6ef', marginBottom: '20px' }}>
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
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
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <select value={selSkill} onChange={e => setSelSkill(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                  <option value="">Select a skill...</option>
                  {filteredLib.map(s => <option key={s.skill_id} value={s.skill_id}>{s.skill_name} ({s.category})</option>)}
                </select>
                <select value={selLevel} onChange={e => setSelLevel(e.target.value)}
                  style={{ padding: '8px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', background: '#f5f6fa' }}>
                  {PROFICIENCY.map(p => <option key={p} value={p}>{p}</option>)}
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
                      <span style={{ fontSize: '11px', color: '#8b92a8', marginLeft: '8px' }}>{s.category}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        padding: '3px 9px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
                        background: s.proficiency_level === 'advanced' ? '#dcfce7' : s.proficiency_level === 'intermediate' ? '#fef3c7' : '#fee2e2',
                        color: s.proficiency_level === 'advanced' ? '#16a34a' : s.proficiency_level === 'intermediate' ? '#d97706' : '#dc2626',
                      }}>{s.proficiency_level}</span>
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
              {cardTitle('Add Project')}
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
                    {['academic','personal','internship','competition'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <button onClick={addProject} style={{ padding: '9px 20px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
                    Add Project
                  </button>
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
                  <div key={i} style={{ padding: '12px 0', borderBottom: i < projects.length-1 ? '1px solid #e4e6ef' : 'none' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e' }}>{p.project_title}</div>
                    <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>{p.description}</div>
                    <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '4px' }}>
                      {p.technologies?.join(', ')} · {p.project_type} · {p.year_completed}
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
              {cardTitle('Add Certification')}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>{inp(certForm.cert_name, v => setCertForm({...certForm, cert_name: v}), 'Certification name *')}</div>
                <div>{inp(certForm.issuer, v => setCertForm({...certForm, issuer: v}), 'Issuer (e.g. AWS, Microsoft)')}</div>
                <div><label style={{ fontSize: '11px', color: '#8b92a8' }}>Issue Date</label>
                  {inp(certForm.issue_date, v => setCertForm({...certForm, issue_date: v}), '', 'date')}
                </div>
                <div><label style={{ fontSize: '11px', color: '#8b92a8' }}>Expiry Date</label>
                  {inp(certForm.expiry_date, v => setCertForm({...certForm, expiry_date: v}), '', 'date')}
                </div>
                <div>
                  <button onClick={addCert} style={{ padding: '9px 20px', background: '#2d5be3', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
                    Add Certification
                  </button>
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
                  <div key={i} style={{ padding: '12px 0', borderBottom: i < certs.length-1 ? '1px solid #e4e6ef' : 'none' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e' }}>{c.cert_name}</div>
                    <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px' }}>{c.issuer}</div>
                    <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '2px' }}>
                      {c.issue_date && `Issued: ${c.issue_date}`} {c.expiry_date && `· Expires: ${c.expiry_date}`}
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