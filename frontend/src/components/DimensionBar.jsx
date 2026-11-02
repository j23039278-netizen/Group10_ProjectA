// SEAGAS — One dimension of an assessment. Skill dimensions are a labelled bar ("Not required"
// and "No data yet" get a grey dashed bar and a short note instead of 0%). Experience dimensions
// have no percentage: they list up to three of the student's records.
import { dimensionState, dimensionRecords } from '../utils/dimensions'
import { readinessColor } from '../utils/readiness'

const SHOWN = 3

function RecordList({ dim, value, records }) {
  const items = dimensionRecords(dim, records)
  // Synthetic students can have an internship count without a record behind it
  const noRecords = parseFloat(value) > 0 ? 'Recorded in the profile' : dim.empty
  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ fontWeight: '500', color: '#1a1f2e' }}>{dim.label}</span>
        {items.length > 0 && <span style={{ fontWeight: '600', color: '#4a5168', whiteSpace: 'nowrap' }}>{items.length}</span>}
      </div>
      {items.length === 0
        ? <div style={{ fontSize: '11px', color: '#8b92a8' }}>{noRecords}</div>
        : (
          <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: '#4a5168', lineHeight: 1.5 }}>
            {items.slice(0, SHOWN).map((text, i) => <li key={i} style={{ overflowWrap: 'anywhere' }}>{text}</li>)}
            {items.length > SHOWN && <li style={{ listStyle: 'none', color: '#8b92a8' }}>and {items.length - SHOWN} more</li>}
          </ul>
        )}
    </div>
  )
}

export default function DimensionBar({ dim, value, skills, records, height = 7 }) {
  if (dim.records) return <RecordList dim={dim} value={value} records={records} />
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
          <div style={{ height: '100%', borderRadius: '99px', width: `${Math.min(d.value, 100)}%`, background: readinessColor(d.value), transition: 'width .6s ease' }} />
        </div>
      ) : (
        <div style={{ height: `${height}px`, borderRadius: '99px', border: '1px dashed #c3c8d6', boxSizing: 'border-box' }} />
      )}
      {!scored && <div style={{ fontSize: '11px', color: '#8b92a8', marginTop: '3px' }}>{d.note}</div>}
    </div>
  )
}
