// SEAGAS — My Profile → Experience: internships, jobs, freelance work and volunteering.
// Paid experience counts towards the Industry Experience score of an assessment.
import { useState, useEffect } from 'react'
import { experienceAPI } from '../api/client'
import { EXPERIENCE_TYPES, experienceTypeLabel, period } from '../utils/experience'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef', blue: '#2d5be3', green: '#16a34a', red: '#dc2626' }
const EMPTY = { job_title: '', company: '', experience_type: 'internship', location: '', start_date: '', end_date: '', description: '' }
const today = () => new Date().toISOString().slice(0, 10)

const errMsg = (e, fallback) => {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map(x => x.msg.replace(/^Value error, /, '')).join(' ')
  return typeof d === 'string' ? d : fallback
}

export default function ExperienceTab() {
  const [items, setItems]     = useState([])
  const [form, setForm]       = useState(EMPTY)
  const [current, setCurrent] = useState(false)       // still working there: no end date
  const [editId, setEditId]   = useState(null)
  const [error, setError]     = useState('')
  const [notice, setNotice]   = useState('')
  const [saving, setSaving]   = useState(false)

  const load = () => experienceAPI.list().then(r => setItems(r.data)).catch(() => setError('Could not load your experience.'))
  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))
  const reset = () => { setForm(EMPTY); setCurrent(false); setEditId(null) }

  const save = async () => {
    setError(''); setNotice('')
    if (!form.job_title.trim() || !form.company.trim()) return setError('Enter the job title and the company or organisation.')
    if (!form.start_date) return setError('Choose the start date.')
    if (!current && !form.end_date) return setError('Choose the end date, or tick "I still work here".')
    const body = { ...form, end_date: current ? null : form.end_date, location: form.location || null, description: form.description || null }
    setSaving(true)
    try {
      if (editId) await experienceAPI.update(editId, body)
      else await experienceAPI.add(body)
      setNotice(editId ? 'Experience updated.' : 'Experience added.')
      reset()
      load()
    } catch (e) {
      setError(errMsg(e, 'Could not save the experience.'))
    } finally {
      setSaving(false)
    }
  }

  const edit = (x) => {
    setForm({ job_title: x.job_title, company: x.company, experience_type: x.experience_type, location: x.location || '',
              start_date: x.start_date, end_date: x.end_date || '', description: x.description || '' })
    setCurrent(!x.end_date)
    setEditId(x.experience_id)
    setError(''); setNotice('')
  }

  const remove = async (x) => {
    if (!window.confirm(`Delete "${x.job_title}" at ${x.company}?`)) return
    try {
      await experienceAPI.remove(x.experience_id)
      if (editId === x.experience_id) reset()
      load()
    } catch (e) {
      setError(errMsg(e, 'Could not delete the experience.'))
    }
  }

  const input = { width: '100%', padding: '9px 12px', border: '1.5px solid #e4e6ef', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#f5f6fa', boxSizing: 'border-box' }
  const lbl = { fontSize: '12px', fontWeight: '600', color: C.body, display: 'block', marginBottom: '5px' }
  const cardStyle = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '24px', marginBottom: '16px' }

  return (
    <>
      <div style={cardStyle}>
        <div style={{ fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {editId ? 'Edit experience' : 'Add experience'}
        </div>
        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '14px' }}>
          Internships, part-time or full-time jobs, freelance work and volunteering. Paid work and internships count towards the
          Industry Experience part of your readiness score.
        </div>
        {error && <div role="alert" style={{ background: '#fee2e2', color: C.red, padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{error}</div>}
        {notice && <div role="status" style={{ background: '#dcfce7', color: C.green, padding: '10px', borderRadius: '8px', marginBottom: '12px', fontSize: '13px' }}>{notice}</div>}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          <div><label style={lbl} htmlFor="ex-title">Job title</label>
            <input id="ex-title" style={input} value={form.job_title} onChange={set('job_title')} maxLength={150} placeholder="e.g. Data Analyst Intern" /></div>
          <div><label style={lbl} htmlFor="ex-company">Company / organisation</label>
            <input id="ex-company" style={input} value={form.company} onChange={set('company')} maxLength={150} placeholder="e.g. Acme Sdn Bhd" /></div>
          <div><label style={lbl} htmlFor="ex-type">Type</label>
            <select id="ex-type" style={input} value={form.experience_type} onChange={set('experience_type')}>
              {EXPERIENCE_TYPES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select></div>
          <div><label style={lbl} htmlFor="ex-loc">Location (optional)</label>
            <input id="ex-loc" style={input} value={form.location} onChange={set('location')} maxLength={150} placeholder="e.g. Kuala Lumpur" /></div>
          <div><label style={lbl} htmlFor="ex-start">Start date</label>
            <input id="ex-start" type="date" style={input} value={form.start_date} max={today()} onChange={set('start_date')} /></div>
          <div><label style={lbl} htmlFor="ex-end">End date</label>
            <input id="ex-end" type="date" style={{ ...input, opacity: current ? 0.5 : 1 }} value={current ? '' : form.end_date}
              min={form.start_date || undefined} disabled={current} onChange={set('end_date')} />
            <label style={{ fontSize: '12px', color: C.body, display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', cursor: 'pointer' }}>
              <input type="checkbox" checked={current} onChange={e => setCurrent(e.target.checked)} /> I still work here
            </label></div>
        </div>
        <div style={{ marginTop: '12px' }}>
          <label style={lbl} htmlFor="ex-desc">What you did (optional)</label>
          <textarea id="ex-desc" rows={3} maxLength={3000} style={{ ...input, fontFamily: 'inherit', resize: 'vertical' }} value={form.description}
            onChange={set('description')} placeholder="e.g. Built Power BI dashboards for the sales team and cleaned monthly order data with SQL." />
        </div>
        <div style={{ marginTop: '14px', display: 'flex', gap: '8px' }}>
          <button onClick={save} disabled={saving} style={{ padding: '10px 22px', background: C.blue, color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
            {saving ? 'Saving…' : editId ? 'Save changes' : '+ Add experience'}
          </button>
          {editId && <button onClick={reset} style={{ padding: '10px 18px', background: '#fff', color: C.body, border: `1px solid ${C.line}`, borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>Cancel</button>}
        </div>
      </div>

      <div style={cardStyle}>
        <div style={{ fontSize: '13px', fontWeight: '700', color: C.ink, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          My experience ({items.length})
        </div>
        {items.length === 0 ? <div style={{ fontSize: '13px', color: C.muted }}>No experience added yet.</div> : items.map(x => (
          <div key={x.experience_id} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '12px 0', borderTop: '1px solid #f0f1f5', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 300px', minWidth: 0 }}>
              <div style={{ fontSize: '14px', fontWeight: '600', color: C.ink }}>
                {x.job_title} <span style={{ fontWeight: '500', color: C.body }}>· {x.company}</span>
              </div>
              <div style={{ fontSize: '12px', color: C.muted, marginTop: '2px' }}>
                {experienceTypeLabel(x.experience_type)} · {period(x.start_date, x.end_date)}{x.location ? ` · ${x.location}` : ''}
              </div>
              {x.description && <div style={{ fontSize: '13px', color: C.body, marginTop: '6px', whiteSpace: 'pre-wrap' }}>{x.description}</div>}
            </div>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-start' }}>
              <button onClick={() => edit(x)} style={{ background: 'none', border: `1px solid ${C.line}`, borderRadius: '6px', padding: '4px 10px', fontSize: '12px', fontWeight: '600', color: C.blue, cursor: 'pointer' }}>Edit</button>
              <button onClick={() => remove(x)} style={{ background: 'none', border: `1px solid ${C.line}`, borderRadius: '6px', padding: '4px 10px', fontSize: '12px', fontWeight: '600', color: C.red, cursor: 'pointer' }}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
