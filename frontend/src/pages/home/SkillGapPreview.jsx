// SEAGAS Home — simplified skill gap bars with a hover / tap detail panel
import { useState } from 'react'
import { GAP_SKILLS, STATUS_LABEL, gapStatus } from './data'
import { useInView } from './hooks'

export default function SkillGapPreview() {
  const [ref, inView] = useInView(0.3)
  const [active, setActive] = useState(2) // start on a skill that has a gap
  const skill = GAP_SKILLS[active]
  const status = gapStatus(skill)
  const gap = Math.max(skill.required - skill.current, 0)

  return (
    <div ref={ref} className={`hp-gapview hp-reveal ${inView ? 'is-visible' : ''}`}>
      <div className="hp-gap-bars">
        <div className="hp-demo-tag">Sample</div>
        {GAP_SKILLS.map((s, i) => {
          const st = gapStatus(s)
          return (
            <button
              key={s.name}
              type="button"
              className={`hp-gap-row ${i === active ? 'is-active' : ''}`}
              onMouseEnter={() => setActive(i)}
              onFocus={() => setActive(i)}
              onClick={() => setActive(i)}
              aria-pressed={i === active}
            >
              <span className="hp-gap-top">
                <span className="hp-gap-name">{s.name}</span>
                <span className={`hp-gap-status hp-text-${st}`}>{STATUS_LABEL[st]}</span>
              </span>
              <span className="hp-bar">
                <span
                  className={`hp-bar-fill hp-fill-${st}`}
                  style={{ '--w': `${s.current}%`, '--d': `${200 + i * 110}ms` }}
                />
                <span className="hp-bar-target" style={{ left: `${s.required}%` }} title="Required level" />
              </span>
            </button>
          )
        })}
        <div className="hp-gap-legend">
          <span><i className="hp-legend-fill" />Current alignment</span>
          <span><i className="hp-legend-target" />Required level</span>
        </div>
      </div>

      <div className="hp-gap-detail" aria-live="polite">
        <div key={skill.name} className="hp-swap">
          <div className="hp-gap-detail-head">
            <span className="hp-gap-detail-name">{skill.name}</span>
            <span className={`hp-status-chip hp-status-${status}`}>{STATUS_LABEL[status]}</span>
          </div>
          <div className="hp-gap-stats">
            <div><span>Current alignment</span><b>{skill.current}%</b></div>
            <div><span>Required alignment</span><b>{skill.required}%</b></div>
            <div><span>Gap</span><b className={`hp-text-${status}`}>{gap}%</b></div>
          </div>
          <div className="hp-hv-label">Suggested next action</div>
          <p className="hp-gap-action">{skill.action}</p>
        </div>
        <div className="hp-gap-hint">Hover or tap a skill to see details</div>
      </div>
    </div>
  )
}
