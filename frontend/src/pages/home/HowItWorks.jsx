// SEAGAS Home — interactive "How it works" stepper with a live visual preview
import { useState, useEffect } from 'react'
import { STEPS } from './data'
import { useInView, prefersReducedMotion } from './hooks'
import Icon from './Icon'

const STEP_ICONS = { profile: 'profile', career: 'target', compare: 'compare', gaps: 'gap' }
const AUTO_ADVANCE_MS = 5500

// Row layout used by the "compare" visual so the SVG lines can line up with the chips
const ROW_H = 46
const YOUR = ['Python', 'React', 'Git']
const REQUIRED = ['AWS', 'Python', 'Docker', 'React']
const MATCHES = [[0, 1], [1, 3]] // [your index, required index]

function ProfileVisual() {
  return (
    <div className="hp-hv-card">
      <div className="hp-hv-profile">
        <div className="hp-hv-avatar">S</div>
        <div>
          <div className="hp-hv-name">Sample student</div>
          <div className="hp-hv-meta">Bachelor of Computer Science · GPA 3.6</div>
        </div>
      </div>
      <div className="hp-hv-label">Skills</div>
      <div className="hp-hv-chips">
        {['Python', 'React', 'Git', 'SQL', 'Teamwork'].map((s, i) => (
          <span key={s} className="hp-chip hp-pop-in" style={{ animationDelay: `${150 + i * 90}ms` }}>{s}</span>
        ))}
      </div>
      <div className="hp-hv-label">Projects & certifications</div>
      <div className="hp-hv-lines">
        <span className="hp-grow-in" style={{ '--w': '82%', animationDelay: '500ms' }} />
        <span className="hp-grow-in" style={{ '--w': '64%', animationDelay: '620ms' }} />
      </div>
    </div>
  )
}

function CareerVisual() {
  const roles = ['Data Analyst', 'Software Developer', 'Cloud Engineer', 'Cybersecurity Analyst']
  return (
    <div className="hp-hv-card">
      <div className="hp-hv-label">Choose a role template</div>
      <div className="hp-hv-roles">
        {roles.map((r, i) => (
          <div
            key={r}
            className={`hp-hv-role hp-pop-in ${r === 'Software Developer' ? 'is-picked' : ''}`}
            style={{ animationDelay: `${100 + i * 90}ms` }}
          >
            {r}
            {r === 'Software Developer' && <span className="hp-hv-tick">✓</span>}
          </div>
        ))}
      </div>
      <div className="hp-hv-label">…or paste a job description</div>
      <div className="hp-hv-jd">
        We are hiring a junior developer with experience in <mark>Python</mark>,{' '}
        <mark>React</mark> and <mark>AWS</mark>. Knowledge of <mark>Docker</mark> is a plus.
      </div>
    </div>
  )
}

function CompareVisual() {
  const height = REQUIRED.length * ROW_H
  return (
    <div className="hp-hv-card">
      <div className="hp-compare">
        <div className="hp-compare-col">
          <div className="hp-hv-label">Your skills</div>
          {YOUR.map((s, i) => (
            <div key={s} className="hp-compare-row" style={{ height: ROW_H }}>
              <span className={`hp-chip hp-pop-in ${MATCHES.some(m => m[0] === i) ? 'is-match' : ''}`} style={{ animationDelay: `${i * 80}ms` }}>{s}</span>
            </div>
          ))}
        </div>

        <div className="hp-compare-mid">
          <div className="hp-hv-label hp-vs">VS</div>
          <svg viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" style={{ height }} aria-hidden="true">
            {MATCHES.map(([a, b], i) => {
              const y1 = a * ROW_H + ROW_H / 2
              const y2 = b * ROW_H + ROW_H / 2
              return (
                <path
                  key={i}
                  className="hp-link-line"
                  d={`M0 ${y1} C50 ${y1} 50 ${y2} 100 ${y2}`}
                  pathLength="1"
                  style={{ animationDelay: `${450 + i * 250}ms` }}
                />
              )
            })}
          </svg>
        </div>

        <div className="hp-compare-col">
          <div className="hp-hv-label">Job requirements</div>
          {REQUIRED.map((s, i) => (
            <div key={s} className="hp-compare-row" style={{ height: ROW_H }}>
              <span className={`hp-chip hp-pop-in ${MATCHES.some(m => m[1] === i) ? 'is-match' : ''}`} style={{ animationDelay: `${150 + i * 80}ms` }}>{s}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="hp-hv-note">2 of 4 requirements matched</div>
    </div>
  )
}

function GapsVisual() {
  const groups = [
    ['strong', 'Strong', ['Python', 'React']],
    ['developing', 'Developing', ['Git']],
    ['gap', 'Gap', ['AWS', 'Docker']],
  ]
  return (
    <div className="hp-hv-card">
      <div className="hp-hv-groups">
        {groups.map(([key, label, skills], gi) => (
          <div key={key} className={`hp-hv-group hp-pop-in hp-group-${key}`} style={{ animationDelay: `${gi * 140}ms` }}>
            <div className="hp-hv-group-head"><span className="hp-dot" />{label}</div>
            {skills.map(s => <span key={s} className={`hp-status-chip hp-status-${key}`}>{s}</span>)}
          </div>
        ))}
      </div>
      <div className="hp-hv-note">Each gap links to a course, certification or project.</div>
    </div>
  )
}

const VISUALS = { profile: ProfileVisual, career: CareerVisual, compare: CompareVisual, gaps: GapsVisual }

export default function HowItWorks() {
  const [ref, inView] = useInView(0.3)
  const [active, setActive] = useState(0)
  const [userPicked, setUserPicked] = useState(false)

  // Gently auto-advance while visible, until the visitor clicks a step
  useEffect(() => {
    if (!inView || userPicked || prefersReducedMotion()) return
    const t = setTimeout(() => setActive(a => (a + 1) % STEPS.length), AUTO_ADVANCE_MS)
    return () => clearTimeout(t)
  }, [active, inView, userPicked])

  const Visual = VISUALS[STEPS[active].id]

  return (
    <div ref={ref} className={`hp-how hp-reveal ${inView ? 'is-visible' : ''}`}>
      <div className="hp-steps" role="tablist" aria-label="How SEAGAS works">
        {STEPS.map((step, i) => (
          <button
            key={step.id}
            type="button"
            role="tab"
            aria-selected={i === active}
            className={`hp-step ${i === active ? 'is-active' : ''}`}
            onClick={() => { setUserPicked(true); setActive(i) }}
          >
            <span className="hp-step-num">0{i + 1}</span>
            <span className="hp-step-icon"><Icon name={STEP_ICONS[step.id]} /></span>
            <span className="hp-step-body">
              <span className="hp-step-title">{step.title}</span>
              <span className="hp-step-text">{step.text}</span>
            </span>
            {i === active && !userPicked && inView && (
              <span className="hp-step-timer" style={{ animationDuration: `${AUTO_ADVANCE_MS}ms` }} />
            )}
          </button>
        ))}
      </div>

      <div className="hp-how-visual" role="tabpanel" aria-label={STEPS[active].title}>
        <div className="hp-demo-tag">Example</div>
        <div key={STEPS[active].id} className="hp-swap">
          <Visual />
        </div>
      </div>
    </div>
  )
}
