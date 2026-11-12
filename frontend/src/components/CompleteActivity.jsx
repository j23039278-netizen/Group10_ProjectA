// SEAGAS — "Complete activity" dialog (Recommendations and Progress pages).
// A student must attach evidence (a file or a link) before a recommended activity
// can be marked complete; the backend refuses to complete it otherwise.
// Advisors see this evidence on the student's page.
import { useState } from 'react'
import { fileAPI, progressAPI } from '../api/client'
import EvidenceFiles from './EvidenceFiles'
import { ALLOWED_TEXT } from './evidenceRules'

// resource: { resource_id, resource_title }; evidence: its current evidence list.
// onChanged(): reload the evidence; onCompleted(response): the activity is complete (called once
// the student has seen the "Congratulations" step and, for a skill they already had, chosen
// whether to raise its level).
const LEVEL = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }

export default function CompleteActivity({ resource, evidence = [], onChanged, onCompleted, onClose }) {
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)    // the complete response: shows the Congratulations step
  const rid = resource.resource_id

  const complete = async () => {
    setError('')
    setSaving(true)
    try {
      const res = await progressAPI.complete(rid)
      setResult(res)
    } catch (e) {
      const d = e.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Could not mark it as completed. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  // Raise the skill the student already had, then finish with that as the notice
  const raise = async (level) => {
    setError('')
    setSaving(true)
    try {
      const r = await progressAPI.raiseSkill(rid, level)
      onCompleted({ ...result, data: { ...result.data, notice: r.data.notice } })
    } catch (e) {
      const d = e.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Could not change the level. Please try again.')
      setSaving(false)
    }
  }

  const btnStyle = (primary) => ({ padding: '10px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer',
    background: primary ? 'var(--s-score-good, #16a34a)' : '#fff', color: primary ? '#fff' : 'var(--s-body, #4a5168)',
    border: primary ? 'none' : '1.5px solid var(--s-line, #e4e6ef)' })

  if (result) {
    const s = result.data.skill || {}
    const finish = () => onCompleted(result)
    return (
      <div onClick={finish} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000,
                                     display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
        <div role="dialog" aria-modal="true" aria-label="Activity completed" onClick={e => e.stopPropagation()}
          style={{ background: '#fff', borderRadius: '16px', padding: '28px', width: '100%', maxWidth: '480px', textAlign: 'center',
                   boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
          <div aria-hidden="true" style={{ fontSize: '44px', lineHeight: 1 }}>🎉</div>
          <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)', marginTop: '10px' }}>Congratulations!</div>
          <div style={{ fontSize: '14px', color: 'var(--s-body, #4a5168)', marginTop: '10px', lineHeight: 1.6 }}>
            You have completed <b>{resource.resource_title}</b>.
            {s.status === 'added' && <> <b>{s.skill_name}</b> has been added to your skill profile at <b>{LEVEL[s.level] || s.level}</b> level.</>}
            {s.status === 'existing' && s.suggested_level && <>
              {' '}Your profile already has <b>{s.skill_name}</b> at <b>{LEVEL[s.level] || s.level}</b> level.
              Would you like to raise it to <b>{LEVEL[s.suggested_level]}</b>?</>}
            {s.status === 'existing' && !s.suggested_level && <>
              {' '}<b>{s.skill_name}</b> is already at <b>{LEVEL[s.level] || s.level}</b> level in your profile;
              this activity has been added to it as evidence.</>}
          </div>
          {error && <div role="alert" style={{ background: 'var(--s-bad-soft, #fee2e2)', color: 'var(--s-bad, #dc2626)', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginTop: '12px' }}>{error}</div>}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px', flexWrap: 'wrap' }}>
            {s.status === 'existing' && s.suggested_level ? <>
              <button onClick={finish} disabled={saving} style={btnStyle(false)}>Keep at {LEVEL[s.level] || s.level}</button>
              <button onClick={() => raise(s.suggested_level)} disabled={saving} style={btnStyle(true)}>
                {saving ? 'Saving…' : `Raise to ${LEVEL[s.suggested_level]}`}
              </button>
            </> : (
              <button onClick={finish} style={btnStyle(true)}>Great!</button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div role="dialog" aria-modal="true" aria-label="Complete activity" onClick={e => e.stopPropagation()}
        style={{ background: '#fff', borderRadius: '16px', padding: '28px', width: '100%', maxWidth: '560px',
                 maxHeight: 'calc(100vh - 32px)', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '17px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>Complete this activity</div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--s-accent, #2d5be3)', marginTop: '4px' }}>{resource.resource_title}</div>
          </div>
          <button onClick={onClose} aria-label="Close" style={{ border: 'none', background: 'none', fontSize: '20px', color: 'var(--s-muted, #8b92a8)', cursor: 'pointer' }}>×</button>
        </div>

        <div style={{ fontSize: '13px', color: 'var(--s-body, #4a5168)', margin: '14px 0 6px', lineHeight: 1.5 }}>
          Attach proof that you finished it, for example a certificate, a screenshot of the completed course, a report
          or slides ({ALLOWED_TEXT}), or a link to a video, GitHub repository or credential page. Your advisor can see it.
        </div>

        <div style={{ background: 'var(--s-bg, #f5f6fa)', borderRadius: '10px', padding: '10px 12px 12px', marginTop: '10px' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>
            Evidence ({evidence.length}) {evidence.length === 0 && <span style={{ color: 'var(--s-bad, #dc2626)', fontWeight: '600' }}>· required</span>}
          </div>
          <EvidenceFiles files={evidence}
            onUpload={async f => { await progressAPI.uploadEvidence(rid, f); setError(''); await onChanged() }}
            onAddLink={async (url, title) => { await progressAPI.linkEvidence(rid, url, title); setError(''); await onChanged() }}
            onDelete={async f => { await fileAPI.remove(f.file_id); await onChanged() }}
            onError={setError} />
        </div>

        {error && <div role="alert" style={{ background: 'var(--s-bad-soft, #fee2e2)', color: 'var(--s-bad, #dc2626)', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginTop: '12px' }}>{error}</div>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '18px' }}>
          <button onClick={onClose} style={{ padding: '10px 16px', background: '#fff', color: 'var(--s-body, #4a5168)', border: '1.5px solid var(--s-line, #e4e6ef)',
                                              borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
            Later
          </button>
          <button onClick={complete} disabled={saving || evidence.length === 0}
            title={evidence.length === 0 ? 'Attach at least one piece of evidence first' : undefined}
            style={{ padding: '10px 16px', background: evidence.length === 0 ? 'var(--s-disabled, #d1d5db)' : 'var(--s-good, #16a34a)', color: '#fff', border: 'none',
                     borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: evidence.length === 0 ? 'not-allowed' : 'pointer' }}>
            {saving ? 'Saving…' : '✓ Mark complete'}
          </button>
        </div>
      </div>
    </div>
  )
}
