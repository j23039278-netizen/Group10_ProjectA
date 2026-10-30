// SEAGAS — Upload a CV and add the skills found in it (Profile → Skills tab).
// Only skills in the skills library are found. Skills outside the student's course list are
// shown but cannot be added; nothing is added until the student ticks it and confirms.
import { useState, useEffect, useRef } from 'react'
import { cvAPI } from '../api/client'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef', blue: '#2d5be3',
            green: '#16a34a', red: '#dc2626', amber: '#d97706' }
const LEVELS = ['beginner', 'intermediate', 'advanced']
const btn = (primary) => ({ padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', cursor: 'pointer',
  border: primary ? 'none' : `1px solid ${C.line}`, background: primary ? C.blue : '#fff', color: primary ? '#fff' : C.body })
const errText = (e, fallback) => {
  const d = e.response?.data?.detail
  if (!e.response) return 'Cannot reach the server. Please make sure the backend is running.'
  return typeof d === 'string' ? d : fallback
}

export default function CvUpload({ onSkillsAdded }) {
  const input = useRef(null)
  const [cv, setCv]         = useState(null)       // stored CV with the skills found in it
  const [picked, setPicked] = useState({})         // skill_id -> proficiency level
  const [busy, setBusy]     = useState('')
  const [error, setError]   = useState('')
  const [notice, setNotice] = useState('')

  const show = (data) => {
    setCv(data)
    // Tick every skill that can be added
    setPicked(Object.fromEntries(data.skills.filter(s => s.in_course && !s.already_added)
      .map(s => [s.skill_id, 'intermediate'])))
  }

  useEffect(() => {
    cvAPI.get().then(r => show(r.data)).catch(() => {})
  }, [])

  const upload = async (file) => {
    if (!file) return
    setBusy('upload'); setError(''); setNotice('')
    try {
      show((await cvAPI.upload(file)).data)
    } catch (e) {
      setError(errText(e, 'Could not read the CV.'))
    } finally {
      setBusy('')
      if (input.current) input.current.value = ''
    }
  }

  const addSkills = async () => {
    const skills = Object.entries(picked).map(([skill_id, proficiency_level]) => ({ skill_id, proficiency_level }))
    if (!skills.length) return
    setBusy('add'); setError(''); setNotice('')
    try {
      const r = await cvAPI.addSkills(skills)
      setNotice(r.data.added.length
        ? `Added ${r.data.added.length} skill${r.data.added.length === 1 ? '' : 's'}: ${r.data.added.join(', ')}.`
        : 'No new skills were added.')
      show((await cvAPI.get()).data)
      onSkillsAdded?.()
    } catch (e) {
      setError(errText(e, 'Could not add the skills.'))
    } finally {
      setBusy('')
    }
  }

  const download = async () => {
    const r = await cvAPI.download()
    const url = URL.createObjectURL(r.data)
    const a = document.createElement('a')
    a.href = url
    a.download = cv.file_name
    a.click()
    URL.revokeObjectURL(url)
  }

  const remove = async () => {
    if (!window.confirm('Remove your CV? Skills you already added stay on your profile.')) return
    try {
      await cvAPI.remove()
      setCv(null); setPicked({}); setNotice('CV removed. Skills you already added stay on your profile.')
    } catch (e) {
      setError(errText(e, 'Could not remove the CV.'))
    }
  }

  const toggle = (id) => setPicked(p => {
    const n = { ...p }
    if (n[id]) delete n[id]; else n[id] = 'intermediate'
    return n
  })

  const addable = cv?.skills.filter(s => s.in_course && !s.already_added) || []

  return (
    <div style={{ background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
      <div style={{ fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Add skills from your CV
      </div>
      <div style={{ fontSize: '13px', color: C.body, marginBottom: '12px' }}>
        Upload your CV (PDF or Word .docx, max 5 MB). We look for skills that are in the SEAGAS skill list; tick the ones you
        really have, choose your level, and add them. Nothing is added until you confirm.
      </div>

      {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{error}</div>}
      {notice && <div role="status" style={{ background: '#dcfce7', color: C.green, padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{notice}</div>}

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input ref={input} type="file" accept=".pdf,.docx" aria-label="CV file" style={{ display: 'none' }}
          onChange={e => upload(e.target.files[0])} />
        <button style={btn(true)} disabled={!!busy} onClick={() => input.current.click()}>
          {busy === 'upload' ? 'Reading your CV…' : cv ? 'Upload a new CV' : 'Upload CV'}
        </button>
        {cv && (
          <>
            <span style={{ fontSize: '13px', color: C.body }}>
              <b style={{ color: C.ink }}>{cv.file_name}</b> · uploaded {new Date(cv.uploaded_at).toLocaleDateString('en-GB')}
            </span>
            <button style={{ ...btn(false), padding: '5px 10px', fontSize: '12px' }} onClick={download}>Download</button>
            <button style={{ ...btn(false), padding: '5px 10px', fontSize: '12px', color: C.red }} onClick={remove}>Remove</button>
          </>
        )}
      </div>

      {cv && (
        <div style={{ marginTop: '16px' }}>
          {cv.note && <div style={{ fontSize: '12px', color: C.amber, marginBottom: '8px' }}>{cv.note}</div>}
          {cv.skills.length === 0 ? (
            <div style={{ fontSize: '13px', color: C.muted }}>
              No skills from the SEAGAS skill list were found in this CV. You can still add skills below.
            </div>
          ) : (
            <>
              <div style={{ fontSize: '12px', color: C.muted, marginBottom: '8px' }}>
                {cv.skills.length} skill{cv.skills.length === 1 ? '' : 's'} found. Skills that are not in our skill list are not picked up.
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {cv.skills.map(s => {
                  const canAdd = s.in_course && !s.already_added
                  const on = !!picked[s.skill_id]
                  return (
                    <div key={s.skill_id} style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', padding: '8px 10px',
                                                  border: `1px solid ${on ? '#c7d4fb' : C.line}`, borderRadius: '8px', background: on ? '#eef2fd' : '#fafbfc',
                                                  opacity: canAdd ? 1 : 0.65 }}>
                      <input type="checkbox" aria-label={`Add ${s.skill_name}`} checked={on} disabled={!canAdd} onChange={() => toggle(s.skill_id)} />
                      <div style={{ flex: '1 1 240px', minWidth: 0 }}>
                        <div style={{ fontSize: '13px', fontWeight: '600', color: C.ink }}>
                          {s.skill_name} <span style={{ fontWeight: '500', color: C.muted, fontSize: '11px' }}>· {s.category.replace('_', ' / ')}</span>
                        </div>
                        <div style={{ fontSize: '11px', color: C.muted, overflowWrap: 'anywhere' }} title="Where it appears in your CV">“{s.context}”</div>
                      </div>
                      {s.already_added ? <span style={{ fontSize: '12px', color: C.green, fontWeight: '600' }}>Already on your profile</span>
                        : !s.in_course ? <span style={{ fontSize: '12px', color: C.muted }}>Not in your course&apos;s skill list</span>
                        : (
                          <select aria-label={`Level for ${s.skill_name}`} value={picked[s.skill_id] || 'intermediate'} disabled={!on}
                            onChange={e => setPicked(p => ({ ...p, [s.skill_id]: e.target.value }))}
                            style={{ padding: '6px 8px', border: `1px solid ${C.line}`, borderRadius: '6px', fontSize: '12px', textTransform: 'capitalize' }}>
                            {LEVELS.map(l => <option key={l} value={l}>{l[0].toUpperCase() + l.slice(1)}</option>)}
                          </select>
                        )}
                    </div>
                  )
                })}
              </div>
              {addable.length > 0 && (
                <button style={{ ...btn(true), marginTop: '12px', opacity: Object.keys(picked).length ? 1 : 0.6 }}
                  disabled={!Object.keys(picked).length || busy === 'add'} onClick={addSkills}>
                  {busy === 'add' ? 'Adding…' : `Add ${Object.keys(picked).length} selected skill${Object.keys(picked).length === 1 ? '' : 's'}`}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
