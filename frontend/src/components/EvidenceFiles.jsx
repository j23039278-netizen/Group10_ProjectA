// SEAGAS — Evidence attached to a project, certification or recommended activity.
// A piece of evidence is a file (PDF, JPG, PNG, Word, PowerPoint) or a link
// (videos, GitHub, Drive, credential pages). Students can add and delete; advisors
// get the same list read-only (leave out onUpload / onAddLink / onDelete).
// The server re-checks every rule (backend/evidence.py).
import { useRef, useState } from 'react'
import { fileAPI } from '../api/client'
import { MAX_FILES, ACCEPT, ALLOWED_TEXT, checkFile, checkLink } from './evidenceRules'

const sizeText = (b) => b >= 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`

const chip = { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 6px 4px 9px', borderRadius: '8px',
               background: '#f5f6fa', border: '1px solid #e4e6ef', fontSize: '12px', color: '#1a1f2e', maxWidth: '100%' }
const addBtn = { ...chip, padding: '5px 10px', cursor: 'pointer', color: '#2d5be3', fontWeight: '600', background: '#fff', borderStyle: 'dashed' }
const linkBtn = (color) => ({ border: 'none', background: 'none', padding: '0 3px', fontSize: '12px', fontWeight: '600', color, cursor: 'pointer' })
const nameStyle = { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }

const VIDEO_HOSTS = /(youtube\.com|youtu\.be|vimeo\.com|loom\.com|drive\.google\.com|onedrive|sharepoint|tiktok\.com)/i

// Icon for a stored piece of evidence, a picked File, or a pending link
function iconFor({ kind, link_url, url, content_type, type, name, file_name }) {
  if (kind === 'link') return VIDEO_HOSTS.test(link_url || url || '') ? '🎬' : '🔗'
  const t = content_type || type || ''
  const n = (file_name || name || '').toLowerCase()
  if (t.includes('pdf') || n.endsWith('.pdf')) return '📄'
  if (t.includes('wordprocessing') || n.endsWith('.docx')) return '📝'
  if (t.includes('presentation') || n.endsWith('.pptx')) return '📊'
  return '🖼️'
}

function errorOf(e, fallback) {
  const d = e.response?.data?.detail
  return typeof d === 'string' ? d : fallback
}

// Small inline form for adding a link (URL + optional title)
function LinkForm({ onAdd, onCancel, onError }) {
  const [url, setUrl]     = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy]   = useState(false)
  const input = { padding: '5px 8px', fontSize: '12px', border: '1px solid #e4e6ef', borderRadius: '6px', outline: 'none' }
  const submit = async () => {
    const err = checkLink(url)
    if (err) return onError(err)
    setBusy(true)
    try {
      await onAdd(url.trim(), title.trim())
    } finally {
      setBusy(false)
    }
  }
  return (
    <span style={{ display: 'inline-flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
      <input aria-label="Link URL" autoFocus placeholder="https://… (video, GitHub, credential page)" value={url}
        onChange={e => setUrl(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
        style={{ ...input, width: '260px', maxWidth: '100%' }} />
      <input aria-label="Link title (optional)" placeholder="Title (optional)" value={title}
        onChange={e => setTitle(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
        style={{ ...input, width: '150px' }} />
      <button type="button" disabled={busy} onClick={submit} style={{ ...linkBtn('#2d5be3'), fontSize: '12px' }}>{busy ? 'Adding…' : 'Add'}</button>
      <button type="button" onClick={onCancel} style={linkBtn('#8b92a8')}>Cancel</button>
    </span>
  )
}

// Evidence chosen in an Add / Edit form, saved after the form is saved.
// files: a mix of File objects and { kind: 'link', url, title }.
// slots: how many more pieces the item can take (MAX_FILES minus the ones it already has)
export function PendingFiles({ files, onChange, onError, slots = MAX_FILES }) {
  const input = useRef(null)
  const [linking, setLinking] = useState(false)

  const pick = (e) => {
    const chosen = [...e.target.files]
    e.target.value = ''
    const ok = []
    for (const f of chosen) {
      const err = checkFile(f)
      if (err) { onError(err); continue }
      if (files.length + ok.length >= slots) { onError(`You can attach at most ${MAX_FILES} pieces of evidence.`); break }
      ok.push(f)
    }
    if (ok.length) onChange([...files, ...ok])
  }

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px' }}>
      {files.map((f, i) => (
        <span key={i} style={chip}>
          <span aria-hidden="true">{iconFor(f)}</span>
          <span style={nameStyle}>{f.kind === 'link' ? (f.title || f.url) : f.name}</span>
          {f.kind !== 'link' && <span style={{ color: '#8b92a8' }}>{sizeText(f.size)}</span>}
          <button type="button" onClick={() => onChange(files.filter((_, j) => j !== i))}
            aria-label="Remove" style={linkBtn('#dc2626')}>✕</button>
        </span>
      ))}
      {files.length < slots ? (
        linking ? (
          <LinkForm onError={onError} onCancel={() => setLinking(false)}
            onAdd={async (url, title) => { onChange([...files, { kind: 'link', url, title }]); setLinking(false) }} />
        ) : (
          <>
            <input ref={input} type="file" accept={ACCEPT} multiple onChange={pick} style={{ display: 'none' }} />
            <button type="button" onClick={() => input.current.click()} style={addBtn}>📎 Attach file</button>
            <button type="button" onClick={() => setLinking(true)} style={addBtn}>🔗 Add link</button>
            <span style={{ fontSize: '11px', color: '#8b92a8' }}>{ALLOWED_TEXT} (max 5 MB), or a link for videos · up to {slots}</span>
          </>
        )
      ) : (
        <span style={{ fontSize: '11px', color: '#8b92a8' }}>Maximum {MAX_FILES} pieces of evidence</span>
      )}
    </div>
  )
}

export default function EvidenceFiles({ files = [], onUpload, onAddLink, onDelete, onError, emptyText }) {
  const input = useRef(null)
  const [busy, setBusy]       = useState(false)
  const [linking, setLinking] = useState(false)
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

  const addLink = async (url, title) => {
    try {
      await onAddLink(url, title)
      setLinking(false)
    } catch (err) {
      report(errorOf(err, 'Could not add the link.'))
    }
  }

  const remove = async (f) => {
    if (!window.confirm(`Delete ${f.file_name}?`)) return
    try {
      await onDelete(f)
    } catch (err) {
      report(errorOf(err, 'Could not delete it.'))
    }
  }

  const canAdd = (onUpload || onAddLink) && files.length < MAX_FILES
  if (files.length === 0 && !canAdd) return emptyText ? <span style={{ fontSize: '12px', color: '#8b92a8' }}>{emptyText}</span> : null

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
      {files.map(f => (
        <span key={f.file_id} style={chip}
          title={f.kind === 'link' ? f.link_url : `${f.file_name} · ${sizeText(f.size_bytes)}`}>
          <span aria-hidden="true">{iconFor(f)}</span>
          <span style={nameStyle}>{f.file_name}</span>
          {f.kind === 'link' ? (
            <a href={f.link_url} target="_blank" rel="noopener noreferrer" style={{ ...linkBtn('#2d5be3'), textDecoration: 'none' }}>Open</a>
          ) : (
            <>
              <span style={{ color: '#8b92a8' }}>{sizeText(f.size_bytes)}</span>
              <button type="button" onClick={() => view(f)} style={linkBtn('#2d5be3')}>View</button>
            </>
          )}
          {onDelete && (
            <button type="button" onClick={() => remove(f)} aria-label={`Delete ${f.file_name}`} style={linkBtn('#dc2626')}>✕</button>
          )}
        </span>
      ))}
      {canAdd && (linking ? (
        <LinkForm onAdd={addLink} onCancel={() => setLinking(false)} onError={report} />
      ) : (
        <>
          {onUpload && (
            <>
              <input ref={input} type="file" accept={ACCEPT} onChange={pick} style={{ display: 'none' }} />
              <button type="button" disabled={busy} onClick={() => input.current.click()} style={{ ...addBtn, cursor: busy ? 'wait' : 'pointer' }}>
                {busy ? 'Uploading…' : '📎 Attach file'}
              </button>
            </>
          )}
          {onAddLink && <button type="button" onClick={() => setLinking(true)} style={addBtn}>🔗 Add link</button>}
        </>
      ))}
      {(onUpload || onAddLink) && files.length >= MAX_FILES && (
        <span style={{ fontSize: '11px', color: '#8b92a8' }}>Maximum {MAX_FILES} pieces of evidence reached</span>
      )}
    </div>
  )
}
