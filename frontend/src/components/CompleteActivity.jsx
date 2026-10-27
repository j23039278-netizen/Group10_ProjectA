// SEAGAS — "Complete activity" dialog (Recommendations and Progress pages).
// A student must attach evidence (a file or a link) before a recommended activity
// can be marked complete; the backend refuses to complete it otherwise.
// Advisors see this evidence on the student's page.
import { useState } from 'react'
import { fileAPI, progressAPI } from '../api/client'
import EvidenceFiles from './EvidenceFiles'
import { ALLOWED_TEXT } from './evidenceRules'

// resource: { resource_id, resource_title }; evidence: its current evidence list.
// onChanged(): reload the evidence; onCompleted(response): the activity is complete.
export default function CompleteActivity({ resource, evidence = [], onChanged, onCompleted, onClose }) {
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)
  const rid = resource.resource_id

  const complete = async () => {
    setError('')
    setSaving(true)
    try {
      const res = await progressAPI.complete(rid)
      onCompleted(res)
    } catch (e) {
      const d = e.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Could not mark it as completed. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div role="dialog" aria-modal="true" aria-label="Complete activity" onClick={e => e.stopPropagation()}
        style={{ background: '#fff', borderRadius: '16px', padding: '28px', width: '100%', maxWidth: '560px',
                 maxHeight: 'calc(100vh - 32px)', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '17px', fontWeight: '700', color: '#1a1f2e' }}>Complete this activity</div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#2d5be3', marginTop: '4px' }}>{resource.resource_title}</div>
          </div>
          <button onClick={onClose} aria-label="Close" style={{ border: 'none', background: 'none', fontSize: '20px', color: '#8b92a8', cursor: 'pointer' }}>×</button>
        </div>

        <div style={{ fontSize: '13px', color: '#4a5168', margin: '14px 0 6px', lineHeight: 1.5 }}>
          Attach proof that you finished it, for example a certificate, a screenshot of the completed course, a report
          or slides ({ALLOWED_TEXT}), or a link to a video, GitHub repository or credential page. Your advisor can see it.
        </div>

        <div style={{ background: '#f5f6fa', borderRadius: '10px', padding: '10px 12px 12px', marginTop: '10px' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#1a1f2e' }}>
            Evidence ({evidence.length}) {evidence.length === 0 && <span style={{ color: '#dc2626', fontWeight: '600' }}>· required</span>}
          </div>
          <EvidenceFiles files={evidence}
            onUpload={async f => { await progressAPI.uploadEvidence(rid, f); setError(''); await onChanged() }}
            onAddLink={async (url, title) => { await progressAPI.linkEvidence(rid, url, title); setError(''); await onChanged() }}
            onDelete={async f => { await fileAPI.remove(f.file_id); await onChanged() }}
            onError={setError} />
        </div>

        {error && <div role="alert" style={{ background: '#fee2e2', color: '#dc2626', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', marginTop: '12px' }}>{error}</div>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '18px' }}>
          <button onClick={onClose} style={{ padding: '10px 16px', background: '#fff', color: '#4a5168', border: '1.5px solid #e4e6ef',
                                              borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}>
            Later
          </button>
          <button onClick={complete} disabled={saving || evidence.length === 0}
            title={evidence.length === 0 ? 'Attach at least one piece of evidence first' : undefined}
            style={{ padding: '10px 16px', background: evidence.length === 0 ? '#d1d5db' : '#16a34a', color: '#fff', border: 'none',
                     borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: evidence.length === 0 ? 'not-allowed' : 'pointer' }}>
            {saving ? 'Saving…' : '✓ Mark complete'}
          </button>
        </div>
      </div>
    </div>
  )
}
