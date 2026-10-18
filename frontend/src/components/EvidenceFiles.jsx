// SEAGAS — Evidence files attached to a project or certification.
// Students see "Attach file" and can delete; advisors get the same list read-only
// (leave out onUpload / onDelete). The server re-checks every rule below.
import { useRef, useState } from 'react'
import { fileAPI } from '../api/client'
import { MAX_FILES, ACCEPT, checkFile } from './evidenceRules'


const sizeText = (b) => b >= 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`

const chip = { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 6px 4px 9px', borderRadius: '8px',
               background: '#f5f6fa', border: '1px solid #e4e6ef', fontSize: '12px', color: '#1a1f2e', maxWidth: '100%' }
const linkBtn = (color) => ({ border: 'none', background: 'none', padding: '0 3px', fontSize: '12px', fontWeight: '600', color, cursor: 'pointer' })

function errorOf(e, fallback) {
  const d = e.response?.data?.detail
  return typeof d === 'string' ? d : fallback
}

// Files chosen in the Add / Edit form, uploaded after the form is saved.
// slots: how many more files the item can take (MAX_FILES minus the ones it already has)
export function PendingFiles({ files, onChange, onError, slots = MAX_FILES }) {
  const input = useRef(null)

  const pick = (e) => {
    const chosen = [...e.target.files]
    e.target.value = ''
    const room = slots - files.length
    const ok = []
    for (const f of chosen) {
      const err = checkFile(f)
      if (err) { onError(err); continue }
      if (ok.length >= room) { onError(`You can attach at most ${MAX_FILES} files.`); break }
      ok.push(f)
    }
    if (ok.length) onChange([...files, ...ok])
  }

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px' }}>
      {files.map((f, i) => (
        <span key={`${f.name}-${i}`} style={chip}>
          <span aria-hidden="true">{/\.pdf$/i.test(f.name) || f.type === 'application/pdf' ? '📄' : '🖼️'}</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>{f.name}</span>
          <span style={{ color: '#8b92a8' }}>{sizeText(f.size)}</span>
          <button type="button" onClick={() => onChange(files.filter((_, j) => j !== i))}
            aria-label={`Remove ${f.name}`} style={linkBtn('#dc2626')}>✕</button>
        </span>
      ))}
      {files.length < slots ? (
        <>
          <input ref={input} type="file" accept={ACCEPT} multiple onChange={pick} style={{ display: 'none' }} />
          <button type="button" onClick={() => input.current.click()}
            style={{ ...chip, padding: '6px 10px', cursor: 'pointer', color: '#2d5be3', fontWeight: '600', background: '#fff', borderStyle: 'dashed' }}>
            📎 Attach proof (JPG, PNG, PDF · max 5 MB, up to {slots})
          </button>
        </>
      ) : (
        <span style={{ fontSize: '11px', color: '#8b92a8' }}>Maximum {MAX_FILES} files</span>
      )}
    </div>
  )
}

export default function EvidenceFiles({ files = [], onUpload, onDelete, onError }) {
  const input = useRef(null)
  const [busy, setBusy] = useState(false)
  const report = (msg) => (onError ? onError(msg) : window.alert(msg))

  // Open the window first, while the click still counts as a user action, so
  // popup blockers allow it; then point it at the downloaded file.
  const view = async (f) => {
    const win = window.open('', '_blank')
    try {
      const res = await fileAPI.download(f.file_id)
      const url = URL.createObjectURL(res.data)
      if (win) {
        win.opener = null
        win.location.href = url
      } else {
        const a = document.createElement('a')
        a.href = url
        a.download = f.file_name
        a.click()
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      if (win) win.close()
      report(e.response?.status === 404 ? 'This file no longer exists.' : 'Could not open the file.')
    }
  }

  const pick = async (e) => {
    const file = e.target.files[0]
    e.target.value = ''
    if (!file) return
    const err = checkFile(file)
    if (err) return report(err)
    setBusy(true)
    try {
      await onUpload(file)
    } catch (err) {
      report(errorOf(err, 'Could not upload the file.'))
    } finally {
      setBusy(false)
    }
  }

  const remove = async (f) => {
    if (!window.confirm(`Delete ${f.file_name}?`)) return
    try {
      await onDelete(f)
    } catch (err) {
      report(errorOf(err, 'Could not delete the file.'))
    }
  }

  if (files.length === 0 && !onUpload) return null

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
      {files.map(f => (
        <span key={f.file_id} style={chip} title={`${f.file_name} · ${sizeText(f.size_bytes)}`}>
          <span aria-hidden="true">{f.content_type === 'application/pdf' ? '📄' : '🖼️'}</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>{f.file_name}</span>
          <span style={{ color: '#8b92a8' }}>{sizeText(f.size_bytes)}</span>
          <button type="button" onClick={() => view(f)} style={linkBtn('#2d5be3')}>View</button>
          {onDelete && (
            <button type="button" onClick={() => remove(f)} aria-label={`Delete ${f.file_name}`} style={linkBtn('#dc2626')}>✕</button>
          )}
        </span>
      ))}
      {onUpload && files.length < MAX_FILES && (
        <>
          <input ref={input} type="file" accept={ACCEPT} onChange={pick} style={{ display: 'none' }} />
          <button type="button" disabled={busy} onClick={() => input.current.click()}
            style={{ ...chip, padding: '4px 10px', cursor: busy ? 'wait' : 'pointer', color: '#2d5be3', fontWeight: '600', background: '#fff', borderStyle: 'dashed' }}>
            {busy ? 'Uploading…' : '📎 Attach proof (JPG, PNG, PDF · max 5 MB)'}
          </button>
        </>
      )}
      {onUpload && files.length >= MAX_FILES && (
        <span style={{ fontSize: '11px', color: '#8b92a8' }}>Maximum {MAX_FILES} files reached</span>
      )}
    </div>
  )
}
