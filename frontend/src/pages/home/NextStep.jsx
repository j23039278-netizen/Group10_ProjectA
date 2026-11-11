// SEAGAS Home — recommendation preview + progress preview chart
import { useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts'
import { NEXT_STEPS, PROGRESS_DATA } from './data'
import { useInView, useAnimatedNumber, prefersReducedMotion } from './hooks'

const VIEWS = [
  { id: 'readiness', label: 'Readiness' },
  { id: 'skills',    label: 'Skills' },
  { id: 'progress',  label: 'Progress' },
]

const AXIS = { stroke: '#5d5d66', fontSize: 11, tickLine: false, axisLine: false }
const TOOLTIP = {
  contentStyle: { background: '#ffffff', border: '1px solid rgba(22,22,26, .108)', borderRadius: 10, fontSize: 12, color: '#16161a' },
  labelStyle: { color: '#5d5d66' },
  cursor: { fill: 'rgba(22,22,26, .036)', stroke: 'rgba(22,22,26, .09)' },
}

export function RecommendationPreview({ onView }) {
  const [ref, inView] = useInView(0.3)
  const [i, setI] = useState(0)
  const rec = NEXT_STEPS[i]
  return (
    <div ref={ref} className={`hp-panel hp-rec hp-reveal ${inView ? 'is-visible' : ''}`}>
      <div className="hp-panel-head">
        <div>
          <div className="hp-rc-label">Your next step</div>
          <div className="hp-panel-title">Close a skill gap</div>
        </div>
        <span className="hp-pill">Example</span>
      </div>

      <div className="hp-seg" role="tablist" aria-label="Example skill gaps">
        {NEXT_STEPS.map((r, idx) => (
          <button
            key={r.gap}
            type="button"
            role="tab"
            aria-selected={idx === i}
            className={`hp-seg-btn ${idx === i ? 'is-active' : ''}`}
            onClick={() => setI(idx)}
          >
            {r.gap}
          </button>
        ))}
      </div>

      <div key={rec.gap} className="hp-swap">
        <div className="hp-rec-gap">
          <span>Skill gap</span>
          <span className="hp-status-chip hp-status-gap">{rec.gap}</span>
        </div>
        <div className="hp-rec-card">
          <div className="hp-rec-type">{rec.type} · {rec.provider}</div>
          <div className="hp-rec-title">{rec.title}</div>
          <div className="hp-rec-meta">
            <div><span>Difficulty</span><b>{rec.difficulty}</b></div>
            <div><span>Estimated time</span><b>{rec.hours} hours</b></div>
            <div><span>Cost</span><b>{rec.cost}</b></div>
          </div>
        </div>
      </div>

      <button type="button" className="hp-btn hp-btn-ghost hp-btn-block" onClick={onView}>
        View recommendation <span className="hp-arrow" aria-hidden="true">→</span>
      </button>
    </div>
  )
}

export function ProgressPreview() {
  const [ref, inView] = useInView(0.3)
  const [view, setView] = useState('readiness')
  const latest = PROGRESS_DATA[PROGRESS_DATA.length - 1]
  const headline = { readiness: latest.readiness, skills: latest.strong, progress: latest.completed }[view]
  const shown = useAnimatedNumber(headline, inView, 800)
  const animate = !prefersReducedMotion()

  const caption = {
    readiness: <>{shown}% <small>readiness · up from {PROGRESS_DATA[0].readiness}%</small></>,
    skills: <>{shown} <small>strong skills · gaps down to {latest.gap}</small></>,
    progress: <>{shown} <small>recommendations completed</small></>,
  }[view]

  return (
    <div ref={ref} className={`hp-panel hp-progress hp-reveal ${inView ? 'is-visible' : ''}`} style={{ '--d': '120ms' }}>
      <div className="hp-panel-head">
        <div>
          <div className="hp-rc-label">Progress over time</div>
          <div className="hp-panel-big">{caption}</div>
        </div>
        <span className="hp-pill">Sample</span>
      </div>

      <div className="hp-seg" role="tablist" aria-label="Progress chart view">
        {VIEWS.map(v => (
          <button
            key={v.id}
            type="button"
            role="tab"
            aria-selected={view === v.id}
            className={`hp-seg-btn ${view === v.id ? 'is-active' : ''}`}
            onClick={() => setView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </div>

      <div className="hp-chart">
        {inView && (
          <ResponsiveContainer width="100%" height="100%">
            {view === 'readiness' ? (
              <AreaChart key="readiness" data={PROGRESS_DATA} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="hp-area" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#c8102e" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#c8102e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(22,22,26, .054)" vertical={false} />
                <XAxis dataKey="name" {...AXIS} />
                <YAxis domain={[0, 100]} {...AXIS} unit="%" />
                <Tooltip {...TOOLTIP} formatter={(v) => [`${v}%`, 'Readiness']} />
                <Area
                  type="monotone" dataKey="readiness" stroke="#e11d2e" strokeWidth={3}
                  fill="url(#hp-area)" dot={{ r: 4, fill: '#e11d2e', strokeWidth: 0 }} activeDot={{ r: 6 }}
                  isAnimationActive={animate} animationDuration={1100}
                />
              </AreaChart>
            ) : view === 'skills' ? (
              <BarChart key="skills" data={PROGRESS_DATA} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="rgba(22,22,26, .054)" vertical={false} />
                <XAxis dataKey="name" {...AXIS} />
                <YAxis {...AXIS} allowDecimals={false} />
                <Tooltip {...TOOLTIP} />
                <Bar dataKey="strong" name="Strong" stackId="s" fill="#16a34a" isAnimationActive={animate} />
                <Bar dataKey="developing" name="Developing" stackId="s" fill="#f59e0b" isAnimationActive={animate} />
                <Bar dataKey="gap" name="Gap" stackId="s" fill="#ef4444" radius={[6, 6, 0, 0]} isAnimationActive={animate} />
              </BarChart>
            ) : (
              <BarChart key="progress" data={PROGRESS_DATA} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke="rgba(22,22,26, .054)" vertical={false} />
                <XAxis dataKey="name" {...AXIS} />
                <YAxis {...AXIS} allowDecimals={false} />
                <Tooltip {...TOOLTIP} formatter={(v) => [v, 'Completed']} />
                <Bar dataKey="completed" fill="#8f0a1f" radius={[6, 6, 0, 0]} isAnimationActive={animate} animationDuration={900} />
              </BarChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
