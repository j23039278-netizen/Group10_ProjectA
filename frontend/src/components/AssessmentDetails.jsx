// SEAGAS — What the selected assessment was about: the job, when, how it was matched and the
// result; for a pasted job description also its company and full text.
import { assessmentName, assessmentDate } from '../utils/assessments'

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '')

export default function AssessmentDetails({ assessment: h }) {
  if (!h) return null
  const pasted = !h.role_id
  const counts = [['Strong', h.strong_count, '#16a34a'], ['Developing', h.developing_count, '#d97706'], ['Gaps', h.gap_count, '#dc2626']]
  return (
    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #f0f1f5', fontSize: '12px', color: '#4a5168' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 18px', alignItems: 'baseline' }}>
        <b style={{ fontSize: '13px', color: '#1a1f2e' }}>{assessmentName(h)}</b>
        <span>{pasted ? 'Pasted job description' : 'Role template'}</span>
        {h.jd_company && <span>{h.jd_company}</span>}
        <span>{assessmentDate(h)}</span>
        <span>{cap(h.matching_method)} matching</span>
        <span>{h.skill_count} skills required:{' '}
          {counts.map(([label, n, color], i) => (
            <span key={label}>{i > 0 && ', '}<b style={{ color }}>{n} {label.toLowerCase()}</b></span>
          ))}
        </span>
      </div>
      {pasted && h.jd_text && (
        <details style={{ marginTop: '8px' }}>
          <summary style={{ cursor: 'pointer', color: '#2d5be3', fontWeight: '600' }}>Show the job description</summary>
          <div style={{ whiteSpace: 'pre-wrap', marginTop: '6px', padding: '10px 12px', background: '#f5f6fa', borderRadius: '8px', maxHeight: '220px', overflowY: 'auto', lineHeight: 1.5 }}>
            {h.jd_text}
          </div>
        </details>
      )}
    </div>
  )
}
