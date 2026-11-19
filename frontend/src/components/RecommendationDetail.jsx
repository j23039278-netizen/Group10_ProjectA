// SEAGAS — Why a recommended skill matters and the level it needs (lecturer feedback F05)
// Data: rec.why and rec.level from backend/rec_details.py
import { useState } from 'react'

// The JD quote marks the skill's words with << >>: show them in bold
function Quote({ text }) {
  const parts = text.split(/<<(.+?)>>/)
  return (
    <span style={{ fontStyle: 'italic' }}>
      “{parts.map((p, i) => (i % 2 ? <b key={i} style={{ fontStyle: 'normal' }}>{p}</b> : p))}”
    </span>
  )
}

const LEVEL = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }

export default function RecommendationDetail({ rec }) {
  const [showQuote, setShowQuote] = useState(false)
  const { why, level } = rec
  if (!why && !level) return null
  const pct = why?.jd_percent

  return (
    <div style={{ background: 'var(--s-surface-2, #f8fafc)', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '10px',
                  padding: '12px 14px', margin: '0 0 14px', display: 'grid', gap: '10px', fontSize: '13px',
                  color: 'var(--s-body, #4a5168)' }}>
      {why && (
        <div>
          <div style={{ fontSize: '11px', fontWeight: '800', letterSpacing: '0.5px', textTransform: 'uppercase',
                        color: 'var(--s-muted, #8b92a8)', marginBottom: '4px' }}>Why it matters</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {pct != null && why.jd_total > 0 && (
              <div aria-hidden="true" style={{ width: '90px', height: '6px', borderRadius: '3px', background: 'var(--s-line, #e4e6ef)', overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: 'var(--s-accent, #c8102e)' }} />
              </div>
            )}
            <span>{why.text}</span>
          </div>
          {why.example && (
            <div style={{ marginTop: '4px' }}>
              <button type="button" className="no-print" onClick={() => setShowQuote(v => !v)}
                      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: '12px',
                               color: 'var(--s-accent, #c8102e)', fontWeight: '600' }}>
                {showQuote ? '▾ Hide example' : '▸ See it in a real job description'}
              </button>
              {showQuote && (
                <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--s-muted, #6b7280)' }}>
                  <Quote text={why.example.quote} /> <span>({why.example.jd_ref})</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {level && (
        <div>
          <div style={{ fontSize: '11px', fontWeight: '800', letterSpacing: '0.5px', textTransform: 'uppercase',
                        color: 'var(--s-muted, #8b92a8)', marginBottom: '4px' }}>Your level</div>
          <div style={{ display: 'flex', alignItems: 'stretch', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 180px', background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '8px', padding: '8px 10px' }}>
              <div style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>Now</div>
              <div style={{ fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>
                {level.current ? LEVEL[level.current] : level.related_skill ? `Related: ${level.related_skill}` : 'Not on your profile'}
              </div>
              <div style={{ fontSize: '12px' }}>{level.current_text}</div>
            </div>
            <div aria-hidden="true" style={{ alignSelf: 'center', fontSize: '18px', color: 'var(--s-muted, #8b92a8)' }}>→</div>
            <div style={{ flex: '1 1 180px', background: '#fff', border: '1px solid var(--s-line, #e4e6ef)', borderRadius: '8px', padding: '8px 10px' }}>
              <div style={{ fontSize: '11px', color: 'var(--s-muted, #8b92a8)' }}>Needed to count as Strong</div>
              <div style={{ fontWeight: '700', color: 'var(--s-ink, #1a1f2e)' }}>{LEVEL[level.target]}</div>
              <div style={{ fontSize: '12px' }}>{level.target_text}</div>
            </div>
          </div>
          <div style={{ marginTop: '8px', padding: '8px 10px', borderRadius: '8px',
                        background: level.met_now ? 'var(--s-good-soft, #dcfce7)' : '#fff7ed',
                        color: level.met_now ? 'var(--s-good, #15803d)' : '#9a3412',
                        border: `1px solid ${level.met_now ? 'var(--s-good-line, #bbf7d0)' : '#fed7aa'}` }}>
            <b>{level.met_now ? '✓ ' : 'Next step: '}</b>{level.next_step}
          </div>
        </div>
      )}
    </div>
  )
}
