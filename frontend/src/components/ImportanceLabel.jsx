// SEAGAS — Required / Preferred / Bonus label of a skill (same colours as Career Paths)
import { importanceOf } from '../utils/importance'
import { label } from '../utils/labels'

const STYLE = {
  required:  { background: '#fee2e2', color: '#dc2626' },
  preferred: { background: '#fef3c7', color: '#d97706' },
  bonus:     { background: '#f1f5f9', color: '#64748b' },
}

export default function ImportanceLabel({ item }) {
  const importance = importanceOf(item)
  return (
    <span style={{ ...STYLE[importance], padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', whiteSpace: 'nowrap' }}>
      {label(importance)}
    </span>
  )
}
