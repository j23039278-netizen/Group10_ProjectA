// SEAGAS — Recommendations Page with Development Tracking (FR-11)
// Author: Tee Ren Hang (Frontend) + Soh Way Miin Carl (Backend integration)
import { useState, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { assessmentLabel } from '../utils/assessments'
import AssessmentDetails from '../components/AssessmentDetails'
import { assessAPI, progressAPI } from '../api/client'
import { label } from '../utils/labels'
import { firstStepsTotal, resourceGainText, upToText } from '../utils/importance'
import CompleteActivity from '../components/CompleteActivity'
import EvidenceFiles from '../components/EvidenceFiles'
import ImportanceLabel from '../components/ImportanceLabel'

// Cost tiers, in the order the page shows them (cost_tier comes from recommendation/engine.py)
const TIERS = [
  { id: 'free',          title: 'Free',          note: 'Completely free',
    style: { bg: 'var(--s-good-soft, #dcfce7)', color: 'var(--s-good, #15803d)', border: 'var(--s-good-line, #bbf7d0)' } },
  { id: 'free_to_learn', title: 'Free to learn', note: 'Learning is free; a certificate or extra features cost money',
    style: { bg: 'var(--s-surface-2, #e0f2fe)', color: 'var(--s-ink-2, #0369a1)', border: 'var(--s-line, #bae6fd)' } },
  { id: 'paid',          title: 'Paid',          note: 'Costs money (including free trials)',
    style: { bg: 'var(--s-surface-2, #f1f5f9)', color: 'var(--s-body, #475569)', border: 'var(--s-line, #e2e8f0)' } },
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

  const [recs,        setRecs]        = useState([])
  // "Do these first": up to 3 skills, each with the resource worth doing first
  const [firstSteps,  setFirstSteps]  = useState([])
  const [history,     setHistory]     = useState([])
  const [selId,       setSelId]       = useState(location.state?.assessmentId || '')
  const [loading,     setLoading]     = useState(true)
  // progressMap: { [resource_id]: { status, started_at, completed_at, skill_added } }
  const [progressMap, setProgressMap] = useState({})
  // actionLoading: { [resource_id]: true } while API call in flight
  const [actionLoading, setActionLoading] = useState({})
  // What completing an activity did to the student's skills
  const [notice,      setNotice]      = useState('')
  // Cost tab being shown: 'free' (default) | 'free_to_learn' | 'paid'
  const [tier,        setTier]        = useState('free')
  // Activity whose "Complete" dialog is open (evidence is required to complete)
  const [completing,  setCompleting]  = useState(null)

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
      setFirstSteps(recsRes.data.first_steps || [])
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

  // Reload progress + evidence for the selected assessment (after evidence changes)
  const reloadProgress = async () => {
    const res = await progressAPI.getAssessmentProgress(selId)
    setProgressMap(res.data.progress || {})
  }

  // A completed activity changes what to do first; the list below stays as it is
  const reloadFirstSteps = async () => {
    try {
      const res = await assessAPI.getRecs(selId)
      setFirstSteps(res.data.first_steps || [])
    } catch { /* the activity is completed either way; the card updates on the next load */ }
  }

  // ── Activity completed in the Complete dialog (evidence attached) ──
  const handleCompleted = async (resource, res) => {
    setCompleting(null)
    await reloadProgress()
    await reloadFirstSteps()
    setNotice(`"${resource.resource_title}" is completed. ${res.data.notice} Run the assessment again to see your new score.`)
  }

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
    course:        { bg: 'var(--s-warn-soft, #fef3c7)', color: 'var(--s-warn, #d97706)' },
    certification: { bg: 'var(--s-accent-soft, #eef2fd)', color: 'var(--s-accent, #2d5be3)' },
    project:       { bg: 'var(--s-good-soft, #dcfce7)', color: 'var(--s-good, #16a34a)' },
    workshop:      { bg: 'var(--s-surface-2, #ede9fe)', color: 'var(--s-ink, #7c3aed)' },
    competition:   { bg: 'var(--s-accent-soft, #fce7f3)', color: 'var(--s-accent, #db2777)' },
    internship:    { bg: 'var(--s-good-soft, #f0fdf4)', color: 'var(--s-good, #15803d)' },
  }
  const gapColor = {
    gap:        { bg: 'var(--s-bad-soft, #fee2e2)', color: 'var(--s-bad, #dc2626)' },
    developing: { bg: 'var(--s-warn-soft, #fef3c7)', color: 'var(--s-warn, #d97706)' },
  }

  // Every action button has the same shape, so a row of them lines up
  const actionBtn = (bg, color, border = bg) => ({
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
    height: '36px', padding: '0 16px', boxSizing: 'border-box', whiteSpace: 'nowrap',
    background: bg, color, border: `1.5px solid ${border}`, borderRadius: '8px',
    fontSize: '13px', fontWeight: '600', textDecoration: 'none', cursor: 'pointer',
  })
  const fmtStarted = (d) => d ? new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : ''

  // ── Progress button for each resource ────────────────────────
  const ProgressButton = ({ resource }) => {
    const rid    = resource.resource_id
    const status = progressMap[rid]?.status || null
    const busy   = actionLoading[rid] || false

    if (status === 'completed') {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
          <span style={{ ...actionBtn('#dcfce7', '#15803d', '#86efac'), cursor: 'default' }}>
            ✓ Completed
          </span>
        </div>
      )
    }

    if (status === 'in_progress') {
      return (
        <button onClick={() => setCompleting(resource)} disabled={busy}
          style={actionBtn(busy ? 'var(--s-disabled, #d1d5db)' : '#111111', '#ffffff')}>
          {busy ? '…' : '✓ Mark Complete'}
        </button>
      )
    }

    // Not started
    return (
      <button onClick={() => handleStart(rid)} disabled={busy}
        style={actionBtn('#ffffff', '#111111', busy ? 'var(--s-disabled, #d1d5db)' : '#111111')}>
        {busy ? '…' : '▶ Start'}
      </button>
    )
  }

  // ── One resource row (same look as before) ───────────────────
  const renderResource = (r, j, total) => (
  <div key={j} style={{
    display: 'flex', alignItems: 'flex-start', gap: '14px',
    padding: '14px', borderRadius: '10px',
    marginBottom: j < total - 1 ? '10px' : '0',
    background: progressMap[r.resource_id]?.status === 'completed' ? '#f0fdf4'
      : progressMap[r.resource_id]?.status === 'in_progress' ? '#fffbeb' : 'var(--s-bg, #f5f6fa)',
    border: progressMap[r.resource_id]?.status === 'completed' ? '1.5px solid #bbf7d0'
      : progressMap[r.resource_id]?.status === 'in_progress' ? '1.5px solid #facc15' : '1.5px solid transparent',
    transition: 'border-color 0.2s, background-color 0.2s',
  }}>
    {/* Icon */}
    <div style={{
      width: '38px', height: '38px', borderRadius: '8px', flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '18px',
      background: typeColor[r.resource_type]?.bg || 'var(--s-bg, #f5f6fa)',
    }}>
      {typeIcon[r.resource_type] || '📖'}
    </div>

    {/* Details */}
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '3px' }}>
        <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--s-ink, #1a1f2e)' }}>{r.resource_title}</span>
        {progressMap[r.resource_id]?.status === 'in_progress' && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', padding: '2px 9px', borderRadius: '20px',
                         fontSize: '11px', fontWeight: '700', background: '#fef08a', color: '#713f12' }}>
            <span aria-hidden="true" style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ca8a04' }} />
            In progress{progressMap[r.resource_id]?.started_at ? ` · started ${fmtStarted(progressMap[r.resource_id].started_at)}` : ''}
          </span>
        )}
      </div>
      {r.description && (
        <div style={{ fontSize: '12px', color: 'var(--s-body, #4a5168)', marginBottom: '6px' }}>{r.description}</div>
      )}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{
          padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
          background: typeColor[r.resource_type]?.bg || 'var(--s-bg, #f5f6fa)',
          color: typeColor[r.resource_type]?.color || 'var(--s-body, #4a5168)',
        }}>
          {label(r.resource_type)}
        </span>
        {r.provider && (
          <span style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>📍 {r.provider}</span>
        )}
        {r.cost && (
          <span style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>💰 {r.cost}</span>
        )}
        {r.duration_hours && (
          <span style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>⏱ ~{r.duration_hours} hrs</span>
        )}
        {r.difficulty && (
          <span style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)', textTransform: 'capitalize' }}>
            📊 {r.difficulty}
          </span>
        )}
        {/* What completing it adds; already counted once it is completed */}
        {resourceGainText(r.gain_if_completed) && progressMap[r.resource_id]?.status !== 'completed' && (
          <span style={{ fontSize: '11px', fontWeight: '700', color: r.gain_if_completed > 0 ? '#16a34a' : '#8b92a8' }}>
            {resourceGainText(r.gain_if_completed)}
          </span>
        )}
      </div>
      {/* Evidence the student attached to this activity */}
      {progressMap[r.resource_id]?.evidence?.length > 0 && (
        <EvidenceFiles files={progressMap[r.resource_id].evidence} />
      )}
    </div>

    {/* Action Buttons */}
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, alignSelf: 'center' }}>
      {/* Open link */}
      {r.url && (
        <a href={r.url} target="_blank" rel="noreferrer"
          style={progressMap[r.resource_id]?.status === 'in_progress'
            ? actionBtn('#ffffff', 'var(--s-accent, #c8102e)', 'var(--s-accent, #c8102e)')
            : actionBtn('var(--s-accent, #c8102e)', '#ffffff')}>
          Open →
        </a>
      )}
      {/* Progress button */}
      <ProgressButton resource={r} />
    </div>
  </div>
  )

  // ── Sections: cost tier first, then category, then skill (in the engine's priority order) ──
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

  if (loading) return <div style={{ padding: '40px', color: 'var(--s-muted, #8b92a8)' }}>Loading...</div>

  return (
    <div style={{ padding: '28px 32px' }}>

      {/* ── Complete activity: attach evidence first ── */}
      {completing && (
        <CompleteActivity resource={completing}
          evidence={progressMap[completing.resource_id]?.evidence || []}
          onChanged={reloadProgress}
          onCompleted={res => handleCompleted(completing, res)}
          onClose={() => setCompleting(null)} />
      )}

      {notice && <div role="status" style={{ background: 'var(--s-good-soft, #dcfce7)', color: 'var(--s-good, #16a34a)', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginBottom: '14px' }}>{notice}</div>}

      {/* ── Page Header ── */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '26px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>Personalised Recommendations</div>
        <div style={{ fontSize: '13px', color: 'var(--s-body, #4a5168)', marginTop: '4px' }}>
          Activities to close your skill gaps
        </div>
      </div>

      {/* ── Assessment Selector ── */}
      {history.length > 0 && (
        <div style={{
          background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '12px', boxShadow: 'var(--s-card-shadow, none)',
          padding: '16px 24px', marginBottom: '16px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--s-body, #4a5168)' }}>Assessment:</label>
          <select
            value={selId}
            onChange={e => { setSelId(e.target.value); loadRecs(e.target.value) }}
            style={{
              flex: 1, minWidth: 0, padding: '8px 12px', border: '1.5px solid var(--s-line, #e4e6ef)',
              borderRadius: '8px', fontSize: '13px', background: 'var(--s-bg, #f5f6fa)',
            }}>
            {history.map(h => (
              <option key={h.assessment_id} value={h.assessment_id}>
                {assessmentLabel(h)}
              </option>
            ))}
          </select>
          </div>
          <AssessmentDetails assessment={history.find(h => h.assessment_id === selId)} />
        </div>
      )}

      {/* ── Do these first: not affected by the cost tab ── */}
      {firstSteps.length > 0 && (
        <section aria-label="Do these first" style={{
          background: '#fff', border: '2px solid #2d5be3', borderRadius: '12px',
          padding: '20px', marginBottom: '16px',
        }}>
          <div style={{ fontSize: '16px', fontWeight: '700', color: '#1a1f2e' }}>Do these first</div>
          <div style={{ fontSize: '13px', color: '#1a1f2e', marginTop: '4px' }}>
            Completing these adds about <b>{firstStepsTotal(firstSteps)} points</b> to your score.
          </div>
          <div style={{ fontSize: '12px', color: '#4a5168', marginTop: '2px', marginBottom: '14px' }}>
            A beginner course makes a skill Developing, which earns half. An intermediate activity, project, certification or internship can make it Strong.
          </div>
          {firstSteps.map(step => (
            <div key={step.skill_id} style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '6px' }}>
                <span style={{ fontSize: '14px', fontWeight: '700', color: '#1a1f2e' }}>{step.skill_name}</span>
                <ImportanceLabel item={step} />
              </div>
              {renderResource(step.resource, 0, 1)}
            </div>
          ))}
        </section>
      )}

      {/* ── Progress Summary Bar ── */}
      {Object.keys(progressMap).length > 0 && (
        <div style={{
          background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '12px', boxShadow: 'var(--s-card-shadow, none)',
          padding: '14px 24px', marginBottom: '16px',
          display: 'flex', gap: '24px', alignItems: 'center',
        }}>
          <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--s-body, #4a5168)' }}>Your progress:</div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span style={{ fontSize: '12px', color: 'var(--s-good, #16a34a)', fontWeight: '600' }}>
              ✅ {Object.values(progressMap).filter(p => p.status === 'completed').length} completed
            </span>
            <span style={{ fontSize: '12px', color: 'var(--s-warn, #d97706)', fontWeight: '600' }}>
              ⏳ {Object.values(progressMap).filter(p => p.status === 'in_progress').length} in progress
            </span>
            <span style={{ fontSize: '12px', color: 'var(--s-muted, #8b92a8)', fontWeight: '600' }}>
              ○ {Object.keys(progressMap).length === 0 ? '—' :
                (recs.reduce((acc, r) => acc + r.resources.length, 0) - Object.keys(progressMap).length)} not started
            </span>
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {recs.length === 0 && !loading && (
        <div style={{ textAlign: 'center', padding: '80px', color: 'var(--s-muted, #8b92a8)' }}>
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
        <div style={{ background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '12px', boxShadow: 'var(--s-card-shadow, none)', padding: '24px', marginBottom: '12px',
                      textAlign: 'center', fontSize: '13px', color: 'var(--s-body, #4a5168)' }}>
          No {sections.find(sec => sec.id === tier).title.toLowerCase()} resources for these skill gaps.
          {sections.filter(sec => sec.count > 0).map(sec => (
            <button key={sec.id} onClick={() => setTier(sec.id)}
              style={{ marginLeft: '8px', border: 'none', background: 'none', color: 'var(--s-accent, #2d5be3)', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}>
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
            <span style={{ fontSize: '12px', color: 'var(--s-muted, #8b92a8)' }}>{sec.note} · {sec.count} resource{sec.count === 1 ? '' : 's'}</span>
          </div>

          {sec.categories.map(cat => (
            <div key={cat.id} style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--s-body, #4a5168)', textTransform: 'uppercase',
                            letterSpacing: '0.5px', margin: '0 0 8px 2px' }}>
                {cat.title}
              </div>
              {cat.skills.map(rec => (
                <div key={rec.skill_id} style={{
                  background: '#fff', border: '1px solid var(--s-line, #e4e6ef)',
                  borderRadius: '12px', padding: '20px', marginBottom: '12px',
                }}>
                  {/* Skill Gap Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
                    <span style={{
                      padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
                      background: gapColor[rec.gap_type]?.bg || 'var(--s-bad-soft, #fee2e2)',
                      color: gapColor[rec.gap_type]?.color || 'var(--s-bad, #dc2626)',
                    }}>
                      {rec.gap_type === 'gap' ? '✖ Skill Gap' : '◆ Developing'}
                    </span>
                    <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>{rec.skill_name}</span>
                    <ImportanceLabel item={rec} />
                    {upToText(rec.expected_gain) && (
                      <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--s-body, #4a5168)' }}>{upToText(rec.expected_gain)}</span>
                    )}
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
        <div style={{ background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '12px', boxShadow: 'var(--s-card-shadow, none)', padding: '16px 20px', marginBottom: '12px',
                      fontSize: '13px', color: 'var(--s-body, #4a5168)' }}>
          <b>No resources in our library yet for:</b> {noResources.map(r => r.skill_name).join(', ')}. Try searching online for courses on these skills.
        </div>
      )}

      {/* ── Note ── */}
      {recs.length > 0 && (
        <div style={{
          background: 'var(--s-accent-soft, #eef2fd)', border: '1px solid var(--s-accent-line, #c7d7f8)',
          borderRadius: '10px', padding: '14px 18px', marginTop: '8px',
        }}>
          <div style={{ fontSize: '12px', color: 'var(--s-accent, #2d5be3)', fontWeight: '600', marginBottom: '3px' }}>
            ℹ️ About these recommendations
          </div>
          <div style={{ fontSize: '12px', color: 'var(--s-body, #4a5168)' }}>
            These are AI-assisted suggestions based on your skill gaps. Track your progress using the Start and Mark Complete buttons. Consult your academic advisor for personalised career guidance.
          </div>
        </div>
      )}
    </div>
  )
}
