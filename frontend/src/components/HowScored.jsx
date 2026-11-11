// SEAGAS — "How is this calculated?" under the dimensions of an assessment: the same formulas
// as backend/readiness.py (overall score) and backend/assessment_service.py (dimension bars);
// docs/JOB_READINESS_SCORE.md. jdFit is passed by the Skill Gap page only, where that number is shown.
export default function HowScored({ jdFit }) {
  return (
    <details style={{ fontSize: '12px', color: 'var(--s-body, #4a5168)', marginTop: '4px' }}>
      <summary style={{ cursor: 'pointer', color: 'var(--s-accent, #2d5be3)', fontWeight: '600' }}>How is this calculated?</summary>
      <div style={{ marginTop: '6px', padding: '10px 12px', background: 'var(--s-bg, #f5f6fa)', borderRadius: '8px', lineHeight: 1.55, textAlign: 'justify', hyphens: 'auto' }}>
        <div>
          <b>Overall score.</b> The skills a job asks for are split into three groups: required, preferred and bonus.
          In each group, a Strong skill counts in full, a Developing skill counts half and a Gap counts nothing, which gives
          the group a percentage. The required group makes up 70% of the Job Readiness Score, preferred 25% and bonus 5%, however
          many skills each group has. If a job has no skills in a group, that group is left out and the score is worked out
          from the groups it does have, in the same proportions. A job with only required skills is scored on those alone.
        </div>
        <div style={{ marginTop: '6px' }}>
          <b>Dimension bars.</b> The bars count differently: each skill earns points by importance (required 3, preferred 2,
          bonus 1). A Strong skill earns all its points, a Developing skill half, and a Gap none, and a bar shows the points
          earned out of the total for that kind of skill. So the overall score is not an average of the bars.
        </div>
        <div style={{ marginTop: '6px' }}>
          Project, certification and industry experience are not part of the Job Readiness Score, but they can make a
          matching beginner skill count as Strong.
        </div>
        {jdFit && (
          <div style={{ marginTop: '6px' }}>
            <b>Real job descriptions.</b> Each skill you list under the same name as in a job description counts in full,
            or half if you are a beginner with no project, certification or internship behind it, and the job description
            counts as covered when these reach {Math.round(jdFit.threshold * 100)}% of its skills.
          </div>
        )}
      </div>
    </details>
  )
}
