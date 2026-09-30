// SEAGAS Home — "Run skill analysis" demo (visual only, no backend call).
// The swap button flips the direction of the comparison, which changes the question being answered.
import { useState, useEffect, useRef } from 'react'
import { DEMO_YOUR_SKILLS, DEMO_JOB_SKILLS, DEMO_MODES } from './data'
import { prefersReducedMotion } from './hooks'
import Icon from './Icon'

const STAGE_MS = 750

export default function MatchDemo() {
  // phase: 'idle' | 'running' | 'done'
  const [phase, setPhase] = useState('idle')
  const [stage, setStage] = useState(0)
  const [swaps, setSwaps] = useState(0)
  const timers = useRef([])

  const swapped = swaps % 2 === 1
  const mode = DEMO_MODES[swapped ? 'relevance' : 'readiness']
  const scanning = phase === 'running'

  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  const clearTimers = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }

  const run = () => {
    clearTimers()
    const stageMs = prefersReducedMotion() ? 150 : STAGE_MS
    setPhase('running')
    setStage(0)
    mode.stages.forEach((_, i) => {
      if (i > 0) timers.current.push(setTimeout(() => setStage(i), i * stageMs))
    })
    timers.current.push(setTimeout(() => setPhase('done'), mode.stages.length * stageMs))
  }

  // Swapping asks a different question, so the previous answer no longer applies
  const swap = () => {
    clearTimers()
    setPhase('idle')
    setSwaps(n => n + 1)
  }

  const yourCol = { id: 'your', label: 'Your skills', skills: DEMO_YOUR_SKILLS }
  const jobCol = { id: 'job', label: 'Job requirements', skills: DEMO_JOB_SKILLS }
  const [first, second] = swapped ? [jobCol, yourCol] : [yourCol, jobCol]

  // Columns re-mount on swap so they slide into their new side
  const renderCol = (col, slideClass, isScanning) => (
    <div key={`${col.id}-${swaps}`} className={`hp-match-col ${swaps > 0 ? slideClass : ''}`}>
      <div className="hp-hv-label">{col.label}</div>
      <div className="hp-match-chips">
        {col.skills.map((s, i) => (
          <span key={s} className={`hp-chip ${isScanning ? 'is-scanning' : ''}`} style={{ animationDelay: `${i * 120}ms` }}>{s}</span>
        ))}
      </div>
    </div>
  )

  const progress = phase === 'done' ? 100 : scanning ? ((stage + 1) / mode.stages.length) * 100 : 0

  return (
    <div className="hp-match">
      <div className="hp-demo-tag">Demo</div>

      <div className="hp-match-inputs">
        {renderCol(first, 'hp-slide-from-right', scanning && stage === 0)}
        <button
          type="button"
          className={`hp-match-arrow ${scanning ? 'is-active' : ''} ${swapped ? 'is-swapped' : ''}`}
          onClick={swap}
          disabled={scanning}
          aria-label="Swap the comparison direction"
        >
          <span className="hp-match-arrow-icon"><Icon name="swap" size={20} /></span>
          <span className="hp-tooltip" role="tooltip">Swap direction</span>
        </button>
        {renderCol(second, 'hp-slide-from-left', scanning && stage >= 1)}
      </div>

      <div key={`q-${swaps}`} className="hp-match-question hp-swap">
        <span className="hp-match-question-label">Analysis</span>
        {mode.question}
      </div>

      <div className="hp-match-status" aria-live="polite">
        <div className="hp-match-bar"><span style={{ width: `${progress}%` }} /></div>
        <div className="hp-match-stage">
          {phase === 'idle' && 'Ready to analyse'}
          {scanning && <><span className="hp-spinner" aria-hidden="true" />{mode.stages[stage]}</>}
          {phase === 'done' && 'Analysis complete'}
        </div>
      </div>

      {phase === 'done' ? (
        <>
          <div className="hp-match-result">
            {mode.groups.map((g, gi) => (
              <div key={g.label} className={`hp-hv-group hp-group-${g.key} hp-pop-in`} style={{ animationDelay: `${gi * 140}ms` }}>
                <div className="hp-hv-group-head"><span className="hp-dot" />{g.label}</div>
                {g.skills.map((s, i) => (
                  <span key={s} className={`hp-status-chip hp-status-${g.key}`} style={{ animationDelay: `${gi * 140 + 120 + i * 80}ms` }}>{s}</span>
                ))}
              </div>
            ))}
          </div>
          <p className="hp-match-summary hp-pop-in" style={{ animationDelay: '450ms' }}>{mode.summary}</p>
        </>
      ) : (
        <div className="hp-match-placeholder">
          <span>
            Results appear here as{' '}
            {mode.groups.map((g, i) => (
              <span key={g.label}>
                <b>{g.label}</b>{i < mode.groups.length - 2 ? ', ' : i === mode.groups.length - 2 ? ' and ' : '.'}
              </span>
            ))}
          </span>
        </div>
      )}

      <button type="button" className="hp-btn hp-btn-primary hp-match-btn" onClick={run} disabled={scanning}>
        {phase === 'done' ? 'Run again' : scanning ? 'Analysing…' : 'Run skill analysis'}
        {!scanning && <span className="hp-arrow" aria-hidden="true">→</span>}
      </button>
    </div>
  )
}
