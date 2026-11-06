// SEAGAS — One dimension of an assessment. Skill dimensions are a labelled bar ("Not required"
// and "No data yet" get a grey dashed bar and a short note instead of 0%). Experience dimensions
// have no percentage: they list up to three of the student's records.
import { dimensionState, dimensionRecords, dimensionSummary } from '../utils/dimensions'
import { readinessColor } from '../utils/readiness'

const SHOWN = 3

function RecordList({ dim, value, records }) {
  const items = dimensionRecords(dim, records)
  // Synthetic students can have an internship count without a record behind it
  const noRecords = parseFloat(value) > 0 ? 'Recorded in the profile' : dim.empty
  return (
    <div style={{ marginBottom: '12px', paddingTop: '10px', borderTop: '1px solid var(--s-surface-2, #eef0f5)' }}>
      <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--s-ink, #1a1f2e)', marginBottom: '4px' }}>{dim.label}</div>
      {items.length === 0
        ? <div style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>{noRecords}</div>
        : (
          <div style={{ fontSize: '12px', lineHeight: 1.6 }}>
            {items.slice(0, SHOWN).map((item, i) => (
              <div key={i} style={{ overflowWrap: 'anywhere', color: 'var(--s-body, #4a5168)' }}>
                {item.title}{item.detail && <span style={{ color: 'var(--s-muted, #8b92a8)' }}> · {item.detail}</span>}
              </div>
            ))}
            {items.length > SHOWN && <div style={{ color: 'var(--s-muted, #8b92a8)' }}>and {items.length - SHOWN} more</div>}
          </div>
        )}
    </div>
  )
}

export default function DimensionBar({ dim, value, skills, records, matches, height = 7 }) {
  if (dim.records) return <RecordList dim={dim} value={value} records={records} />
  const d = dimensionState(dim, value, skills)
  const scored = d.state === 'score'
  const summary = scored ? dimensionSummary(dim, matches) : null
  return (
    <div style={{ marginBottom: '12px' }} title={d.note || undefined}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>{dim.label}</span>
        <span style={{ fontWeight: scored ? '700' : '600', color: scored ? 'var(--s-body, #4a5168)' : 'var(--s-muted, #8b92a8)', whiteSpace: 'nowrap' }}>{d.text}</span>
      </div>
      {scored ? (
        <div style={{ height: `${height}px`, background: 'var(--s-line, #e4e6ef)', borderRadius: '99px', overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: '99px', width: `${Math.min(d.value, 100)}%`, background: readinessColor(d.value), transition: 'width .6s ease' }} />
        </div>
      ) : (
        <div style={{ height: `${height}px`, borderRadius: '99px', border: '1px dashed var(--s-line-strong, #c3c8d6)', boxSizing: 'border-box' }} />
      )}
      {!scored && <div style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)', marginTop: '3px' }}>{d.note}</div>}
      {summary && <div style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)', marginTop: '3px' }}>{summary}</div>}
    </div>
  )
}
