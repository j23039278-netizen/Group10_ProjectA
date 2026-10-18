// SEAGAS — Evidence file rules, the same ones the server enforces (backend/evidence.py)
export const MAX_FILES = 5
export const MAX_BYTES = 5 * 1024 * 1024
export const ACCEPT = '.jpg,.jpeg,.png,.pdf'
const TYPES = ['image/jpeg', 'image/png', 'application/pdf']

// Returns an error message, or null when the file can be attached
export function checkFile(file) {
  if (!TYPES.includes(file.type) && !/\.(jpe?g|png|pdf)$/i.test(file.name)) return `${file.name}: only JPG, PNG or PDF files can be attached.`
  if (file.size > MAX_BYTES) return `${file.name} is larger than 5 MB.`
  if (file.size === 0) return `${file.name} is empty.`
  return null
}
