// SEAGAS — Evidence rules, the same ones the server enforces (backend/evidence.py).
// Evidence is a file (PDF, JPG, PNG, Word, PowerPoint) or a link; videos are links.
// Defaults; applyLimits() sets the values from System Settings (GET /api/settings).
// Exported with let, so every importer sees the current values.
export let MAX_FILES = 5          // pieces of evidence (files + links) per item
export let MAX_BYTES = 5 * 1024 * 1024
export function applyLimits(settings) {
  if (settings?.max_evidence_per_item) MAX_FILES = settings.max_evidence_per_item
  if (settings?.max_upload_mb) MAX_BYTES = settings.max_upload_mb * 1024 * 1024
}
export const ACCEPT = '.pdf,.jpg,.jpeg,.png,.docx,.pptx'
export const ALLOWED_TEXT = 'PDF, JPG, PNG, Word or PowerPoint'
const TYPES = [
  'image/jpeg', 'image/png', 'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
]

// Returns an error message, or null when the file can be attached
export function checkFile(file) {
  if (!TYPES.includes(file.type) && !/\.(pdf|jpe?g|png|docx|pptx)$/i.test(file.name))
    return `${file.name}: only ${ALLOWED_TEXT} files can be attached. For a video, add a link instead.`
  if (file.size > MAX_BYTES) return `${file.name} is larger than ${MAX_BYTES / (1024 * 1024)} MB. For a video, add a link instead.`
  if (file.size === 0) return `${file.name} is empty.`
  return null
}

// Returns an error message, or null when the link can be added
export function checkLink(url) {
  const u = (url || '').trim()
  if (!/^https?:\/\/\S+$/i.test(u) || u.length > 2000) return 'Enter a full web address starting with http:// or https://'
  return null
}
