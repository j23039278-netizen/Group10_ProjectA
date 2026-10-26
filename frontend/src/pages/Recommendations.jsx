// SEAGAS — Recommendations Page with Development Tracking (FR-11)
// Author: Tee Ren Hang (Frontend) + Soh Way Miin Carl (Backend integration)
import { useState, useEffect, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { assessAPI, progressAPI } from '../api/client'
import { label } from '../utils/labels'

// Cost tiers, in the order the page shows them (cost_tier comes from recommendation/engine.py)
const TIERS = [
  { id: 'free',          title: 'Free',          note: 'Completely free',
    style: { bg: '#dcfce7', color: '#15803d', border: '#bbf7d0' } },
  { id: 'free_to_learn', title: 'Free to learn', note: 'Learning is free; a certificate or extra features cost money',
    style: { bg: '#e0f2fe', color: '#0369a1', border: '#bae6fd' } },
  { id: 'paid',          title: 'Paid',          note: 'Costs money (including free trials)',
    style: { bg: '#f1f5f9', color: '#475569', border: '#e2e8f0' } },
]
// Category order inside each tier
const CATEGORY_ORDER = [
  { id: 'Technical',  title: 'Technical skills' },
  { id: 'AI_Digital', title: 'AI / Digital skills' },
  { id: 'Analytical', title: 'Analytical skills' },
  { id: 'Soft',       title: 'Soft skills' },
  { id: 'Other',      title: 'Other' },
]
const CATEGORY_IDS = CATEGORY_ORDER.map(c => c.id)

export default function Recommendations() {
  const location = useLocation()
  const navigate = useNavigate()

  const [recs,        setRecs]        = useState([])
  const [history,     setHistory]     = useState([])
  const [selId,       setSelId]       = useState(location.state?.assessmentId || '')
  const [loading,     setLoading]     = useState(true)
  // progressMap: { [resource_id]: { status, started_at, completed_at, skill_added } }
  const [progressMap, setProgressMap] = useState({})
  // actionLoading: { [resource_id]: true } while API call in flight
  const [actionLoading, setActionLoading] = useState({})
  // dialog: { show, resourceId, resourceTitle, prompt }
  const [dialog,      setDialog]      = useState(null)
  // Cost tab being shown: 'free' (default) | 'free_to_learn' | 'paid'
  const [tier,        setTier]        = useState('free')

  // ── Load assessment history on mount ─────────────────────────
  useEffect(() => {
    assessAPI.history().then(r => {
      setHistory(r.data)
      const id = location.state?.assessmentId || (r.data[0]?.assessment_id || '')
      setSelId(id)
      if (id) loadRecs(id)
      else setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  // ── Load recommendations + progress for an assessment ────────
  const loadRecs = useCallback(async (id) => {
    setLoading(true)
    try {
      const [recsRes, progressRes] = await Promise.all([
        assessAPI.getRecs(id),
        progressAPI.getAssessmentProgress(id),
      ])
      setRecs(recsRes.data.recommendations)
      setProgressMap(progressRes.data.progress || {})
    } catch {}
    finally { setLoading(false) }
  }, [])

  // ── Handle Start button ───────────────────────────────────────
  const handleStart = async (resourceId) => {
    setActionLoading(p => ({ ...p, [resourceId]: true }))
    try {
      await progressAPI.start(resourceId, selId)
      setProgressMap(p => ({
        ...p,
        [resourceId]: { status: 'in_progress', started_at: new Date().toISOString(), completed_at: null, skill_added: false }
      }))
    } catch (e) {
      console.error('Start failed', e)
    } finally {
      setActionLoading(p => ({ ...p, [resourceId]: false }))
    }
  }

  // ── Handle Mark Complete button ───────────────────────────────
  const handleComplete = async (resourceId, resourceTitle) => {
    setActionLoading(p => ({ ...p, [resourceId]: true }))
    try {
      const res = await progressAPI.complete(resourceId)
      setProgressMap(p => ({
        ...p,
        [resourceId]: { ...p[resourceId], status: 'completed', completed_at: new Date().toISOString() }
      }))
      // Show dialog with prompt from backend
      setDialog({
        show: true,
        resourceId,
        resourceTitle,
        prompt: res.data.prompt,
      })
    } catch (e) {
      console.error('Complete failed', e)
    } finally {
      setActionLoading(p => ({ ...p, [resourceId]: false }))
    }
  }

  // ── Handle "Yes, update profile" in dialog ───────────────────
  const handleUpdateProfile = async () => {
    if (dialog?.resourceId) {
      try {
        await progressAPI.markSkillAdded(dialog.resourceId)
        setProgressMap(p => ({
          ...p,
          [dialog.resourceId]: { ...p[dialog.resourceId], skill_added: true }
        }))
      } catch {}
    }
    setDialog(null)
    navigate('/profile')
  }

  // ── Handle "Maybe Later" in dialog ───────────────────────────
  const handleMaybeLater = () => setDialog(null)

  // ── UI helpers ────────────────────────────────────────────────
  const typeIcon = {
    course:        '📚',
    certification: '🏆',
    project:       '🛠️',
    workshop:      '🎓',
    competition:   '🏅',
    internship:    '💼',
  }
  const typeColor = {
    course:        { bg: '#fef3c7', color: '#d97706' },
    certification: { bg: '#eef2fd', color: '#2d5be3' },
    project:       { bg: '#dcfce7', color: '#16a34a' },
    workshop:      { bg: '#ede9fe', color: '#7c3aed' },
    competition:   { bg: '#fce7f3', color: '#db2777' },
    internship:    { bg: '#f0fdf4', color: '#15803d' },
  }
  const gapColor = {
    gap:        { bg: '#fee2e2', color: '#dc2626' },
    developing: { bg: '#fef3c7', color: '#d97706' },
  }

  // ── Progress button for each resource ────────────────────────
  const ProgressButton = ({ resource }) => {
    const rid    = resource.resource_id
    const status = progressMap[rid]?.status || null
    const busy   = actionLoading[rid] || false

    if (status === 'completed') {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
          <span style={{
            padding: '7px 12px', background: '#dcfce7', color: '#16a34a',
            borderRadius: '7px', fontSize: '12px', fontWeight: '700',
            border: '1.5px solid #bbf7d0',
          }}>
            ✅ Completed
          </span>
        </div>
      )
    }

    if (status === 'in_progress') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '5px', flexShrink: 0 }}>
          <span style={{
            padding: '4px 10px', background: '#fef3c7', color: '#d97706',
            borderRadius: '20px', fontSize: '11px', fontWeight: '600',
            border: '1px solid #fde68a',
          }}>
            ⏳ In Progress
          </span>
          <button
            onClick={() => handleComplete(rid, resource.resource_title)}
            disabled={busy}
            style={{
              padding: '7px 12px', background: busy ? '#d1d5db' : '#16a34a',
              color: '#fff', borderRadius: '7px', fontSize: '12px',
              fontWeight: '600', border: 'none', cursor: busy ? 'not-allowed' : 'pointer',
            }}>
            {busy ? '...' : '✓ Mark Complete'}
          </button>
        </div>
      )
    }

    // Not started
    return (
      <button
        onClick={() => handleStart(rid)}
        disabled={busy}
        style={{
          padding: '7px 14px',
          background: busy ? '#d1d5db' : '#f0fdf4',
          color: busy ? '#9ca3af' : '#16a34a',
          border: `1.5px solid ${busy ? '#d1d5db' : '#bbf7d0'}`,
          borderRadius: '7px', fontSize: '12px',
          fontWeight: '600', cursor: busy ? 'not-allowed' : 'pointer',
          flexShrink: 0,
        }}>
        {busy ? '...' : '▶ Start'}
      </button>
    )
  }

  // ── One resource row (same look as before) ───────────────────
  const renderResource = (r, j, total) => (
  <div key={j} style={{
    display: 'flex', alignItems: 'flex-start', gap: '14px',
    padding: '14px', background: '#f5f6fa', borderRadius: '10px',
    marginBottom: j < total - 1 ? '10px' : '0',
    border: progressMap[r.resource_id]?.status === 'completed'
      ? '1.5px solid #bbf7d0'
      : progressMap[r.resource_id]?.status === 'in_progress'
      ? '1.5px solid #fde68a'
      : '1.5px solid transparent',
    transition: 'border-color 0.2s',
  }}>
    {/* Icon */}
    <div style={{
      width: '38px', height: '38px', borderRadius: '8px', flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '18px',
      background: typeColor[r.resource_type]?.bg || '#f5f6fa',
    }}>
      {typeIcon[r.resource_type] || '📖'}
    </div>

    {/* Details */}
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a1f2e', marginBottom: '3px' }}>
        {r.resource_title}
      </div>
      {r.description && (
        <div style={{ fontSize: '12px', color: '#4a5168', marginBottom: '6px' }}>{r.description}</div>
      )}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{
          padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
          background: typeColor[r.resource_type]?.bg || '#f5f6fa',
          color: typeColor[r.resource_type]?.color || '#4a5168',
        }}>
          {label(r.resource_type)}
        </span>
        {r.provider && (
          <span style={{ fontSize: '11px', color: '#8b92a8' }}>📍 {r.provider}</span>
        )}
        {r.cost && (
          <span style={{ fontSize: '11px', color: '#8b92a8' }}>💰 {r.cost}</span>
        )}
        {r.duration_hours && (
          <span style={{ fontSize: '11px', color: '#8b92a8' }}>⏱ ~{r.duration_hours} hrs</span>
        )}
        {r.difficulty && (
          <span style={{ fontSize: '11px', color: '#8b92a8', textTransform: 'capitalize' }}>
            📊 {r.difficulty}
          </span>
        )}
      </div>
    </div>

    {/* Action Buttons */}
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, alignSelf: 'center' }}>
      {/* Open link */}
      {r.url && (
        <a href={r.url} target="_blank" rel="noreferrer" style={{
          padding: '7px 14px', background: '#2d5be3', color: '#fff',
          borderRadius: '7px', fontSize: '12px', fontWeight: '600',
          textDecoration: 'none',
        }}>
          Open →
        </a>
      )}
      {/* Progress button */}
      <ProgressButton resource={r} />
    </div>
  </div>
  )

  // ── Sections: cost tier first, then category, then skill (gaps first) ──
  const sections = TIERS.map(t => {
    const categories = CATEGORY_ORDER.map(c => ({
      ...c,
      skills: recs
        .filter(rec => (CATEGORY_IDS.includes(rec.category) ? rec.category : 'Other') === c.id)
        .map(rec => ({ ...rec, resources: rec.resources.filter(r => (r.cost_tier || 'paid') === t.id) }))
        .filter(rec => rec.resources.length > 0),
    })).filter(c => c.skills.length > 0)
    const count = categories.reduce((n, c) => n + c.skills.reduce((m, rec) => m + rec.resources.length, 0), 0)
    return { ...t, categories, count }
  })
  const noResources = recs.filter(rec => rec.resources.length === 0)

  if (loading) return <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>

      {/* ── Completion Dialog ── */}
      {dialog?.show && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
          zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            background: '#fff', borderRadius: '16px', padding: '32px',
            maxWidth: '420px', width: '90%', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }}>
            {/* Header */}
            <div style={{ fontSize: '32px', textAlign: 'center', marginBottom: '12px' }}>🎉</div>
            <div style={{ fontSize: '17px', fontWeight: '700', color: '#1a1f2e', textAlign: 'center', marginBottom: '8px' }}>
              Great job completing
            </div>
            <div style={{
              fontSize: '13px', fontWeight: '600', color: '#2d5be3',
              textAlign: 'center', marginBottom: '16px',
              padding: '6px 12px', background: '#eef2fd', borderRadius: '8px',
            }}>
              {dialog.resourceTitle}
            </div>

            {/* Prompt message */}
            <div style={{
              fontSize: '13px', color: '#4a5168', textAlign: 'center',
              marginBottom: '24px', lineHeight: '1.6',
            }}>
              {dialog.prompt?.message || 'Would you like to update your profile?'}
            </div>

            {/* What to add hint */}
            <div style={{
              background: '#f5f6fa', borderRadius: '10px', padding: '12px 16px',
              marginBottom: '20px', fontSize: '12px', color: '#4a5168',
            }}>
              <div style={{ fontWeight: '600', marginBottom: '6px', color: '#1a1f2e' }}>
                💡 You can add to your profile:
              </div>
              {dialog.prompt?.type === 'certification' && (
                <div>🏆 Add <strong>{dialog.prompt.skill_name}</strong> certification under Certifications</div>
              )}
              {dialog.prompt?.type === 'project' && (
                <div>🛠️ Add this as a project + add <strong>{dialog.prompt.skill_name}</strong> to your Skills</div>
              )}
              {dialog.prompt?.type === 'skill' && (
                <div>✨ Add <strong>{dialog.prompt.skill_name}</strong> to your Skills list</div>
              )}
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                onClick={handleUpdateProfile}
                style={{
                  padding: '12px', background: '#2d5be3', color: '#fff',
                  border: 'none', borderRadius: '10px', fontSize: '13px',
                  fontWeight: '600', cursor: 'pointer', width: '100%',
                }}>
                ✏️ Yes, update my profile
              </button>
              <button
                onClick={handleMaybeLater}
                style={{
                  padding: '12px', background: '#f5f6fa', color: '#4a5168',
                  border: '1.5px solid #e4e6ef', borderRadius: '10px',
                  fontSize: '13px', fontWeight: '600', cursor: 'pointer', width: '100%',
                }}>
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Page Header ── */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: '#1a1f2e' }}>Personalised Recommendations</div>
        <div style={{ fontSize: '13px', color: '#4a5168', marginTop: '4px' }}>
          Activities to close your skill gaps
        </div>
      </div>

      {/* ── Assessment Selector ── */}
      {history.length > 0 && (
        <div style={{
          background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px',
          padding: '16px 24px', marginBottom: '16px',
          display: 'flex', alignItems: 'center', gap: '12px',
        }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: '#4a5168' }}>Assessment:</label>
          <select
            value={selId}
            onChange={e => { setSelId(e.target.value); loadRecs(e.target.value) }}
            style={{
              flex: 1, padding: '8px 12px', border: '1.5px solid #e4e6ef',
              borderRadius: '8px', fontSize: '13px', background: '#f5f6fa',
            }}>
            {history.map(h => (
              <option key={h.assessment_id} value={h.assessment_id}>
                {h.role_name || 'Custom JD'} — {h.readiness_score}% — {new Date(h.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* ── Progress Summary Bar ── */}
      {Object.keys(progressMap).length > 0 && (
        <div style={{
          background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px',
          padding: '14px 24px', marginBottom: '16px',
          display: 'flex', gap: '24px', alignItems: 'center',
        }}>
          <div style={{ fontSize: '12px', fontWeight: '600', color: '#4a5168' }}>Your progress:</div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: '600' }}>
              ✅ {Object.values(progressMap).filter(p => p.status === 'completed').length} completed
            </span>
            <span style={{ fontSize: '12px', color: '#d97706', fontWeight: '600' }}>
              ⏳ {Object.values(progressMap).filter(p => p.status === 'in_progress').length} in progress
            </span>
            <span style={{ fontSize: '12px', color: '#8b92a8', fontWeight: '600' }}>
              ○ {Object.keys(progressMap).length === 0 ? '—' :
                (recs.reduce((acc, r) => acc + r.resources.length, 0) - Object.keys(progressMap).length)} not started
            </span>
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {recs.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '80px', color: '#8b92a8' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>💡</div>
          <div>No recommendations yet. Run an assessment first.</div>
        </div>
      )}

      {/* ── Recommendations: one cost tier at a time (Free by default), grouped by category ── */}
      {recs.length > 0 && (
        <div role="tablist" aria-label="Cost" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
          {sections.map(sec => {
            const active = sec.id === tier
            return (
              <button key={sec.id} role="tab" aria-selected={active} onClick={() => setTier(sec.id)}
                style={{ padding: '8px 16px', borderRadius: '20px', fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                         background: active ? sec.style.color : '#fff', color: active ? '#fff' : sec.style.color,
                         border: `1.5px solid ${active ? sec.style.color : sec.style.border}` }}>
                {sec.title} ({sec.count})
              </button>
            )
          })}
        </div>
      )}

      {/* Nothing in the chosen tier: point to the tiers that have something */}
      {recs.length > 0 && sections.find(sec => sec.id === tier)?.count === 0 && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '24px', marginBottom: '12px',
                      textAlign: 'center', fontSize: '13px', color: '#4a5168' }}>
          No {sections.find(sec => sec.id === tier).title.toLowerCase()} resources for these skill gaps.
          {sections.filter(sec => sec.count > 0).map(sec => (
            <button key={sec.id} onClick={() => setTier(sec.id)}
              style={{ marginLeft: '8px', border: 'none', background: 'none', color: '#2d5be3', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}>
              See {sec.title} ({sec.count}) →
            </button>
          ))}
        </div>
      )}

      {sections.filter(sec => sec.id === tier && sec.count > 0).map(sec => (
        <section key={sec.id} role="tabpanel" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', flexWrap: 'wrap', marginBottom: '12px',
                        paddingBottom: '8px', borderBottom: `2px solid ${sec.style.border}` }}>
            <span style={{ fontSize: '18px', fontWeight: '700', color: sec.style.color }}>{sec.title}</span>
            <span style={{ fontSize: '12px', color: '#8b92a8' }}>{sec.note} · {sec.count} resource{sec.count === 1 ? '' : 's'}</span>
          </div>

          {sec.categories.map(cat => (
            <div key={cat.id} style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#4a5168', textTransform: 'uppercase',
                            letterSpacing: '0.5px', margin: '0 0 8px 2px' }}>
                {cat.title}
              </div>
              {cat.skills.map(rec => (
                <div key={rec.skill_id} style={{
                  background: '#fff', border: '1px solid #e4e6ef',
                  borderRadius: '12px', padding: '20px', marginBottom: '12px',
                }}>
                  {/* Skill Gap Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <span style={{
                      padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
                      background: gapColor[rec.gap_type]?.bg || '#fee2e2',
                      color: gapColor[rec.gap_type]?.color || '#dc2626',
                    }}>
                      {rec.gap_type === 'gap' ? '✖ Skill Gap' : '◆ Developing'}
                    </span>
                    <span style={{ fontSize: '15px', fontWeight: '700', color: '#1a1f2e' }}>{rec.skill_name}</span>
                  </div>
                  {rec.resources.map((r, j) => renderResource(r, j, rec.resources.length))}
                </div>
              ))}
            </div>
          ))}
        </section>
      ))}

      {/* Skills with no resource in the library yet */}
      {noResources.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e4e6ef', borderRadius: '12px', padding: '16px 20px', marginBottom: '12px',
                      fontSize: '13px', color: '#4a5168' }}>
          <b>No resources in our library yet for:</b> {noResources.map(r => r.skill_name).join(', ')}. Try searching online for courses on these skills.
        </div>
      )}

      {/* ── Note ── */}
      {recs.length > 0 && (
        <div style={{
          background: '#eef2fd', border: '1px solid #c7d7f8',
          borderRadius: '10px', padding: '14px 18px', marginTop: '8px',
        }}>
          <div style={{ fontSize: '12px', color: '#2d5be3', fontWeight: '600', marginBottom: '3px' }}>
            ℹ️ About these recommendations
          </div>
          <div style={{ fontSize: '12px', color: '#4a5168' }}>
            These are AI-assisted suggestions based on your skill gaps. Track your progress using the Start and Mark Complete buttons. Consult your academic advisor for personalised career guidance.
          </div>
        </div>
      )}
    </div>
  )
}
