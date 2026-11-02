// SEAGAS — "How is this calculated?" under the dimensions of an assessment: the same formula
// as backend/assessment_service.py (docs/JOB_READINESS_SCORE.md).
export default function HowScored() {
  return (
    <details style={{ fontSize: '12px', color: '#4a5168', marginTop: '4px' }}>
      <summary style={{ cursor: 'pointer', color: '#2d5be3', fontWeight: '600' }}>How is this calculated?</summary>
      <div style={{ marginTop: '6px', padding: '10px 12px', background: '#f5f6fa', borderRadius: '8px', lineHeight: 1.55 }}>
        Each skill the job asks for earns points by importance: required 3, preferred 2, bonus 1.
        A Strong skill earns all its points, a Developing skill half, and a Gap none. A percentage is the points earned
        out of the total for that group of skills, so important skills count for more than the number of skills suggests.
        Project, certification and industry experience are not part of the Job Readiness Score, but they can make a
        matching beginner skill count as Strong.
      </div>
    </details>
  )
}
