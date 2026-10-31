// SEAGAS — Export CV: a one-page skills CV built from the student's profile.
// "Save as PDF" opens the browser's print dialog; only the CV sheet is printed.
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI, studentAPI, progressAPI, experienceAPI } from '../api/client'
import { experienceTypeLabel, period } from '../utils/experience'
import { courseLabel } from '../utils/courses'
import { SKILL_CATEGORIES, levelDots } from '../utils/skillCategories'

const LEVEL = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' }) : ''
const cap = (s) => s ? s[0].toUpperCase() + s.slice(1) : ''

// Print only the CV sheet, on A4, without the portal around it
const PRINT_CSS = `
@media print {
  @page { size: A4; margin: 14mm; }
  body * { visibility: hidden !important; }
  .cv-sheet, .cv-sheet * { visibility: visible !important; }
  .cv-sheet { position: absolute; left: 0; top: 0; width: 100%; box-shadow: none !important; border: none !important; padding: 0 !important; }
  .cv-section { break-inside: avoid; }
}`

export default function CvExport() {
  const navigate = useNavigate()
  const [data, setData]   = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.allSettled([authAPI.me(), studentAPI.getProfile(), studentAPI.getSkills(),
                        studentAPI.getProjects(), studentAPI.getCerts(), progressAPI.getMy('completed'), experienceAPI.list()])
      .then(([me, profile, skills, projects, certs, done, experiences]) => {
        if (me.status !== 'fulfilled') return setError('Could not load your details. Please sign in again.')
        const val = (r, fallback) => (r.status === 'fulfilled' ? r.value.data : fallback)
        setData({
          me: me.value.data, profile: val(profile, {}), skills: val(skills, []),
          projects: val(projects, []), certs: val(certs, []),
          activities: val(done, {}).progress || [],
          experiences: val(experiences, []),
        })
      })
  }, [])

  if (error) return <div style={{ padding: '40px', color: '#dc2626' }}>{error}</div>
  if (!data) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  const { me, profile, skills, projects, certs, activities, experiences } = data
  const h2 = { fontSize: '13px', fontWeight: '700', color: '#2d5be3', textTransform: 'uppercase', letterSpacing: '0.6px',
               borderBottom: '1.5px solid #dbe3fb', paddingBottom: '4px', margin: '18px 0 8px' }
  const small = { fontSize: '12px', color: '#4a5168' }
  const results = [profile.gpa != null && `GPA ${profile.gpa}`, profile.cgpa != null && `CGPA ${profile.cgpa}`].filter(Boolean)

  return (
    <div style={{ padding: '28px 32px' }}>
      <style>{PRINT_CSS}</style>

      <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Export CV</div>
          <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
            Your current skills and records on one page. Click <b>Save as PDF</b> and choose &quot;Save as PDF&quot; as the printer.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => navigate('/profile')} style={{ padding: '9px 16px', fontSize: '13px', fontWeight: '600', border: '1px solid #e4e6ef', borderRadius: '8px', background: '#fff', color: '#4a5168', cursor: 'pointer' }}>
            ← Back to profile
          </button>
          <button onClick={() => window.print()} style={{ padding: '9px 16px', fontSize: '13px', fontWeight: '600', border: 'none', borderRadius: '8px', background: '#2d5be3', color: '#fff', cursor: 'pointer' }}>
            Save as PDF
          </button>
        </div>
      </div>

      <div className="cv-sheet" style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '36px 40px',
                                          maxWidth: '820px', margin: '0 auto', color: '#1a1f2e', fontFamily: '"Segoe UI", Arial, sans-serif' }}>
        {/* Header */}
        <div style={{ fontSize: '26px', fontWeight: '700' }}>{me.full_name}</div>
        <div style={{ fontSize: '14px', color: '#2d5be3', fontWeight: '600', marginTop: '2px' }}>
          {profile.target_role ? `Aspiring ${profile.target_role}` : courseLabel(me.course)}
        </div>
        <div style={{ ...small, marginTop: '6px', lineHeight: 1.6 }}>
          {me.email}
          {me.student_number && <> · Student ID {me.student_number}</>}
          <br />
          {[profile.programme || courseLabel(me.course), profile.university,
            profile.year_of_study && `Year ${profile.year_of_study}`,
            profile.expected_graduation && `Expected graduation ${profile.expected_graduation}`,
            results.length && results.join(' · ')].filter(Boolean).join(' · ')}
        </div>

        {/* Skills by category */}
        <div className="cv-section">
          <div style={h2}>Skills</div>
          {skills.length === 0 ? <div style={small}>No skills added yet.</div> : SKILL_CATEGORIES.map(cat => {
            const list = skills.filter(s => s.category === cat.id)
            if (!list.length) return null
            return (
              <div key={cat.id} style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: cat.color, marginBottom: '4px' }}>{cat.title}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {list.map(s => (
                    <span key={s.skill_id} title={LEVEL[s.proficiency_level]}
                      style={{ fontSize: '12px', padding: '3px 9px', borderRadius: '999px', border: `1px solid ${cat.border}`, background: cat.bg }}>
                      {s.skill_name}{' '}
                      <span style={{ color: cat.color, letterSpacing: '1px' }}>{levelDots(s.proficiency_level)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
          {skills.length > 0 && <div style={{ fontSize: '10px', color: '#8b92a8', marginTop: '4px' }}>●○○ Beginner · ●●○ Intermediate · ●●● Advanced</div>}
        </div>

        {/* Work experience */}
        {experiences.length > 0 && (
          <div className="cv-section">
            <div style={h2}>Experience</div>
            {experiences.map(x => (
              <div key={x.experience_id} style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600' }}>
                  {x.job_title} <span style={{ fontWeight: '400' }}>· {x.company}{x.location ? `, ${x.location}` : ''}</span>
                </div>
                <div style={{ ...small, color: '#8b92a8' }}>{experienceTypeLabel(x.experience_type)} · {period(x.start_date, x.end_date)}</div>
                {x.description && <div style={small}>{x.description}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Projects */}
        {projects.length > 0 && (
          <div className="cv-section">
            <div style={h2}>Projects</div>
            {projects.map(p => (
              <div key={p.project_id} style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600' }}>
                  {p.project_title}
                  <span style={{ fontWeight: '400', color: '#8b92a8' }}>{[cap(p.project_type), p.year_completed].filter(Boolean).length ? ` · ${[cap(p.project_type), p.year_completed].filter(Boolean).join(' · ')}` : ''}</span>
                </div>
                {p.description && <div style={small}>{p.description}</div>}
                {p.technologies && <div style={{ ...small, color: '#8b92a8' }}>Technologies: {Array.isArray(p.technologies) ? p.technologies.join(', ') : p.technologies}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Certifications */}
        {certs.length > 0 && (
          <div className="cv-section">
            <div style={h2}>Certifications</div>
            {certs.map(c => (
              <div key={c.cert_id} style={{ fontSize: '13px', marginBottom: '4px' }}>
                <b>{c.cert_name}</b>
                <span style={{ color: '#4a5168' }}>{c.issuer ? ` · ${c.issuer}` : ''}{c.issue_date ? ` · ${fmtDate(c.issue_date)}` : ''}</span>
              </div>
            ))}
          </div>
        )}

        {/* Completed learning activities */}
        {activities.length > 0 && (
          <div className="cv-section">
            <div style={h2}>Completed learning</div>
            {activities.map(a => (
              <div key={a.progress_id} style={{ fontSize: '13px', marginBottom: '4px' }}>
                <b>{a.resource_title}</b>
                <span style={{ color: '#4a5168' }}>{a.provider ? ` · ${a.provider}` : ''}{a.skill_name ? ` · ${a.skill_name}` : ''}{a.completed_at ? ` · ${fmtDate(a.completed_at)}` : ''}</span>
              </div>
            ))}
          </div>
        )}

        <div style={{ fontSize: '10px', color: '#8b92a8', marginTop: '22px', borderTop: '1px solid #eef0f5', paddingTop: '8px' }}>
          Generated from SEAGAS on {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}. Skill levels are self-reported.
        </div>
      </div>
    </div>
  )
}
