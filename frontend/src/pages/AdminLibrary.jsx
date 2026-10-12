// SEAGAS — Admin: Skills & Role Library (read-only)
// The library is maintained in data/skills/skills_library.csv and loaded by the seed files,
// so this page shows what is in the database rather than editing it.
import { useState, useEffect } from 'react'
import { adminAPI } from '../api/client'

const C = { ink: '#1a1f2e', body: '#4a5168', muted: '#8b92a8', line: '#e4e6ef' }
const card  = { background: '#fff', border: `1px solid ${C.line}`, borderRadius: '12px', padding: '20px 24px' }
const th    = { textAlign: 'left', fontSize: '11px', fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: '0.5px', padding: '10px 12px', borderBottom: `1px solid ${C.line}`, position: 'sticky', top: 0, background: '#fff' }
const td    = { padding: '9px 12px', fontSize: '13px', color: C.body, borderBottom: '1px solid #f0f1f5', verticalAlign: 'top' }
const input = { padding: '9px 11px', fontSize: '13px', border: `1px solid ${C.line}`, borderRadius: '8px', outline: 'none', color: C.ink, background: '#fff' }
const heading = { fontSize: '13px', fontWeight: '700', color: C.ink, textTransform: 'uppercase', letterSpacing: '0.5px' }

const CATEGORY_LABEL = { Technical: 'Technical', AI_Digital: 'AI / Digital', Analytical: 'Analytical', Soft: 'Soft skill' }

export default function AdminLibrary() {
  const [skills, setSkills]     = useState([])
  const [roles, setRoles]       = useState([])
  const [search, setSearch]     = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  useEffect(() => {
    Promise.all([adminAPI.skills(), adminAPI.roles()])
      .then(([s, r]) => { setSkills(s.data); setRoles(r.data) })
      .catch(err => setError(err.response ? 'Could not load the library.' : 'Cannot reach the server. Please make sure the backend is running.'))
      .finally(() => setLoading(false))
  }, [])

  const q = search.trim().toLowerCase()
  const shown = skills.filter(s =>
    (!category || s.category === category) &&
    (!q || s.skill_name.toLowerCase().includes(q) ||
           (s.subcategory || '').toLowerCase().includes(q) ||
           (s.aliases || []).some(a => a.toLowerCase().includes(q)))
  )

  if (loading) return <div style={{ padding: '40px', color: C.muted }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: C.ink }}>Skills &amp; Role Library</div>
        <div style={{ fontSize: '13px', color: C.body, marginTop: '4px' }}>
          {skills.length} skills and {roles.length} job role templates in the database. Edit them in data/skills/skills_library.csv and the seed files.
        </div>
      </div>

      {error && <div role="alert" style={{ padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px', background: '#fee2e2', color: '#dc2626' }}>{error}</div>}

      {/* Job roles */}
      <div style={{ ...card, marginBottom: '16px' }}>
        <div style={{ ...heading, marginBottom: '12px' }}>Job Role Templates</div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{['Role', 'Level', 'Skills', 'Required'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
            <tbody>
              {roles.map(r => (
                <tr key={r.role_id}>
                  <td style={{ ...td, color: C.ink, fontWeight: '600' }}>{r.role_name}</td>
                  <td style={{ ...td, textTransform: 'capitalize' }}>{r.industry_level || '—'}</td>
                  <td style={td}>{r.skill_count}</td>
                  <td style={td}>{r.required_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Skills */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
          <div style={heading}>Skills Library</div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <input type="search" aria-label="Search skills" placeholder="Search skill, subcategory or alias"
              style={{ ...input, width: '240px', maxWidth: '100%' }} value={search} onChange={e => setSearch(e.target.value)} />
            <select aria-label="Filter by category" style={input} value={category} onChange={e => setCategory(e.target.value)}>
              <option value="">All categories</option>
              {Object.entries(CATEGORY_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
        <div style={{ overflow: 'auto', maxHeight: '560px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '720px' }}>
            <thead><tr>{['Skill', 'Category', 'Subcategory', 'Aliases', 'Used by roles', 'Source'].map(h => <th key={h} style={th}>{h}</th>)}</tr></thead>
            <tbody>
              {shown.length === 0 ? (
                <tr><td colSpan={6} style={{ ...td, textAlign: 'center', color: C.muted, padding: '32px' }}>No skills match.</td></tr>
              ) : shown.map(s => (
                <tr key={s.skill_id}>
                  <td style={{ ...td, color: C.ink, fontWeight: '600', whiteSpace: 'nowrap' }}>{s.skill_name}</td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>{CATEGORY_LABEL[s.category] || s.category}</td>
                  <td style={td}>{s.subcategory || '—'}</td>
                  <td style={{ ...td, color: C.muted }}>{(s.aliases || []).join(', ') || '—'}</td>
                  <td style={td}>{s.role_count}</td>
                  <td style={td}>{s.source || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
