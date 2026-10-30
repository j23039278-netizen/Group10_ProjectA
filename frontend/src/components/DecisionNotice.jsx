// SEAGAS — Reminder on the advisor pages that the scores are decision support, not decisions.
export default function DecisionNotice({ compact = false }) {
  return (
    <div role="note" className="no-print" style={{ background: '#eef2fd', border: '1px solid #c7d4fb', borderRadius: '10px',
                                                    padding: compact ? '8px 12px' : '10px 14px', marginBottom: '16px',
                                                    fontSize: '12px', color: '#33416b', lineHeight: 1.5 }}>
      <b>Decision support, not a decision.</b> Readiness scores and skill gaps come from automated skill matching (NLP)
      against job requirements, using skills the students enter themselves. Use them to start a conversation with the
      student, check them against what you know, and record your own judgement in the student&apos;s advisor notes.
    </div>
  )
}
