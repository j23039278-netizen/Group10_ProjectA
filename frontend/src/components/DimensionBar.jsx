// SEAGAS — One dimension of an assessment as a labelled bar. "Not required" and
// "No data yet" (utils/dimensions.js) get a grey dashed bar and a short note instead of 0%.
import { dimensionState } from '../utils/dimensions'

const defaultColor = (v) => (v >= 70 ? '#16a34a' : v >= 40 ? '#2d5be3' : '#dc2626')

export default function DimensionBar({ dim, value, skills, colorOf = defaultColor, height = 7 }) {
  const d = dimensionState(dim, value, skills)
  const scored = d.state === 'score'
  return (
    <div style={{ marginBottom: '12px' }} title={d.note || undefined}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ fontWeight: '500', color: '#1a1f2e' }}>{dim.label}</span>
        <span style={{ fontWeight: scored ? '700' : '600', color: scored ? '#4a5168' : '#8b92a8', whiteSpace: 'nowrap' }}>{d.text}</span>
      </div>
      {scored ? (
        <div style={{ height: `${height}px`, background: '#e4e6ef', borderRadius: '99px', overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: '99px', width: `${Math.min(d.value, 100)}%`, background: colorOf(d.value), transition: 'width .6s ease' }} />
        </div>
      ) : (
        <div style={{ height: `${height}px`, borderRadius: '99px', border: '1px dashed #c3c8d6', boxSizing: 'border-box' }} />
      )}
      {!scored && <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '3px' }}>{d.note}</div>}
    </div>
  )
}
