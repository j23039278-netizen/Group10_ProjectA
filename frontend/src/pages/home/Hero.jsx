// SEAGAS Home — hero: headline, role switcher, readiness card, interactive skill tags
import { useState, useEffect, useRef, useCallback } from 'react'
import { HERO_ROLES, FLOAT_SKILLS, STATUS_LABEL } from './data'
import { useAnimatedNumber, useTypewriter, useDismiss, prefersReducedMotion } from './hooks'

const RING_RADIUS = 58
const RING_CIRC = 2 * Math.PI * RING_RADIUS
const HEADLINE = [['Know', 'how', 'ready'], ['you', 'are', 'to', 'become', 'a']]
const HEADLINE_WORDS = HEADLINE.flat().length
const AUTO_ROTATE_MS = 5000

// ---------- Readiness card ----------

function ReadinessCard({ sample }) {
  const score = useAnimatedNumber(sample.score)
  const strong = useAnimatedNumber(sample.strong, true, 700)
  const developing = useAnimatedNumber(sample.developing, true, 700)
  const gap = useAnimatedNumber(sample.gap, true, 700)
  const counts = { strong, developing, gap }
  const offset = RING_CIRC * (1 - score / 100)

  return (
    <div className="hp-rc">
      <div className="hp-rc-head">
        <div>
          <div className="hp-rc-label">Job readiness</div>
          <div key={sample.role} className="hp-rc-role hp-swap">{sample.role}</div>
        </div>
        <span className="hp-pill">Sample result</span>
      </div>

      <div className="hp-rc-body">
        <div className="hp-ring" tabIndex={0} aria-label={`Sample readiness ${sample.score} percent`}>
          <svg width="140" height="140" viewBox="0 0 140 140">
            <defs>
              <linearGradient id="hp-ring-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#39D6C5" />
                <stop offset="100%" stopColor="#4F7CFF" />
              </linearGradient>
            </defs>
            <circle className="hp-ring-track" cx="70" cy="70" r={RING_RADIUS} fill="none" strokeWidth="11" />
            <circle
              className="hp-ring-bar"
              cx="70" cy="70" r={RING_RADIUS} fill="none" strokeWidth="11" strokeLinecap="round"
              stroke="url(#hp-ring-grad)"
              strokeDasharray={RING_CIRC}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="hp-ring-value">
            <div className="hp-ring-num">{score}%</div>
            <div className="hp-ring-cap">Ready</div>
          </div>
          <span className="hp-tooltip" role="tooltip">Weighted by required, preferred and bonus skills</span>
        </div>

        <div className="hp-rc-counts">
          {['strong', 'developing', 'gap'].map(s => (
            <div key={s} className={`hp-count hp-count-${s}`}>
              <span className="hp-dot" />
              <span>{s === 'gap' ? 'Skill gaps' : `${STATUS_LABEL[s]} skills`}</span>
              <b>{counts[s]}</b>
            </div>
          ))}
        </div>
      </div>

      <div className="hp-rc-skills-label">Skills</div>
      <div key={sample.id} className="hp-rc-skills">
        {sample.skills.map(([name, status], i) => (
          <span
            key={name}
            className={`hp-status-chip hp-status-${status}`}
            style={{ animationDelay: `${120 + i * 70}ms` }}
            title={STATUS_LABEL[status]}
          >
            {name}
          </span>
        ))}
      </div>
    </div>
  )
}

// ---------- Floating skill tag ----------

function SkillTag({ skill, open, onToggle, onClose, inline = false, enterDelay = 0 }) {
  const ref = useRef(null)
  useDismiss(ref, open, onClose)

  // Floating tags open their info card towards the centre of the hero
  // and tags near the left/right edge align their tooltip inwards so it never gets cut off
  const nearLeft = skill.pos.left && parseFloat(skill.pos.left) < 15
  const placement = inline
    ? ''
    : `${skill.pos.right ? 'is-right' : ''} ${nearLeft ? 'is-left' : ''} ${skill.pos.bottom ? 'is-bottom' : ''}`
  const className = inline
    ? 'hp-ftag-wrap is-inline'
    : `hp-ftag-wrap hp-enter hp-enter-tag hp-tier-${skill.tier} ${placement}`

  return (
    <div
      ref={ref}
      className={`${className} ${open ? 'is-open' : ''}`}
      style={inline ? undefined : { ...skill.pos, '--d': `${enterDelay}ms` }}
    >
      <div className="hp-ftag-float" style={{ animationDuration: `${skill.dur}s` }}>
        <button
          type="button"
          className="hp-ftag"
          aria-expanded={open}
          onClick={onToggle}
        >
          {skill.name}
          <span className="hp-tooltip" role="tooltip">{skill.tip}</span>
        </button>
      </div>

      {open && (
        <div className="hp-skill-pop" role="dialog" aria-label={`${skill.name} details`}>
          <div className="hp-skill-pop-title">{skill.name}</div>
          <div className="hp-skill-pop-row">
            <span>Category</span>
            <b>{skill.category}</b>
          </div>
          <div className="hp-skill-pop-row">
            <span>Relevant roles</span>
            <b>{skill.roles.join(', ')}</b>
          </div>
          <p>SEAGAS can compare this skill against job requirements.</p>
        </div>
      )}
    </div>
  )
}

// ---------- Hero ----------

export default function Hero({ onStart, onHowItWorks }) {
  const heroRef = useRef(null)
  const [roleIndex, setRoleIndex] = useState(0)
  const [userPicked, setUserPicked] = useState(false)
  const [openSkill, setOpenSkill] = useState(null)
  const sample = HERO_ROLES[roleIndex]
  const typed = useTypewriter(sample.role, 450)

  // Auto-rotate the sample roles until the visitor picks one themselves
  useEffect(() => {
    if (userPicked || prefersReducedMotion()) return
    const t = setTimeout(() => setRoleIndex(i => (i + 1) % HERO_ROLES.length), AUTO_ROTATE_MS)
    return () => clearTimeout(t)
  }, [roleIndex, userPicked])

  // Subtle mouse parallax: write CSS variables directly, no React re-renders
  useEffect(() => {
    const el = heroRef.current
    if (!el || prefersReducedMotion() || !window.matchMedia('(pointer: fine)').matches) return
    let frame = 0
    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width - 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        el.style.setProperty('--mx', x.toFixed(3))
        el.style.setProperty('--my', y.toFixed(3))
      })
    }
    const onLeave = () => {
      cancelAnimationFrame(frame)
      el.style.setProperty('--mx', 0)
      el.style.setProperty('--my', 0)
    }
    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerleave', onLeave)
    return () => {
      cancelAnimationFrame(frame)
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerleave', onLeave)
    }
  }, [])

  const pickRole = (i) => {
    setUserPicked(true)
    setRoleIndex(i)
  }

  const closeSkill = useCallback(() => setOpenSkill(null), [])
  const toggleSkill = (name) => setOpenSkill(cur => (cur === name ? null : name))

  return (
    <section ref={heroRef} className="hp-hero" id="top">
      {/* Background layers */}
      <div className="hp-hero-bg" aria-hidden="true">
        <div className="hp-grid hp-depth-1" />
        <div className="hp-glow hp-glow-teal hp-depth-3" />
        <div className="hp-glow hp-glow-blue hp-depth-2" />
        <div className="hp-beam" />
        <div className="hp-particles hp-depth-2">
          {Array.from({ length: 16 }, (_, i) => (
            <span
              key={i}
              style={{
                left: `${(i * 61) % 100}%`,
                top: `${(i * 37 + 11) % 100}%`,
                animationDelay: `${-(i * 1.3)}s`,
                animationDuration: `${9 + (i % 5) * 2}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Floating skill tags (desktop / tablet) */}
      <div className="hp-ftags hp-depth-2">
        {FLOAT_SKILLS.map((s, i) => (
          <SkillTag
            key={s.name}
            skill={s}
            enterDelay={900 + i * 50}
            open={openSkill === s.name}
            onToggle={() => toggleSkill(s.name)}
            onClose={closeSkill}
          />
        ))}
      </div>

      <div className="hp-container hp-hero-inner">
        <div className="hp-hero-copy">
          <div className="hp-badge hp-enter" style={{ '--d': '160ms' }}>
            <span className="hp-badge-dot" />
            AI-powered employability assessment
          </div>

          <h1 className="hp-title">
            {HEADLINE.map((line, li) => (
              <span key={li} className="hp-title-line">
                {line.map((w, wi) => {
                  const i = HEADLINE.slice(0, li).flat().length + wi
                  return (
                    <span key={w} className="hp-word" style={{ '--d': `${240 + i * 35}ms` }}>
                      {w}{wi < line.length - 1 ? ' ' : ''}
                    </span>
                  )
                })}
              </span>
            ))}
            <span className="hp-word hp-typed-line" style={{ '--d': `${240 + HEADLINE_WORDS * 35}ms` }}>
              <span className="hp-typed">{typed || ' '}</span>
              <span className="hp-caret" aria-hidden="true" />
            </span>
          </h1>

          <p className="hp-sub hp-enter" style={{ '--d': '600ms' }}>
            SEAGAS compares your skills with real industry job requirements, gives you a
            personalised Job Readiness Score, and shows exactly which skills to build next.
          </p>

          <div className="hp-cta-row hp-enter" style={{ '--d': '700ms' }}>
            <button type="button" className="hp-btn hp-btn-primary" onClick={onStart}>
              Check my readiness <span className="hp-arrow" aria-hidden="true">→</span>
            </button>
            <button type="button" className="hp-btn hp-btn-ghost" onClick={onHowItWorks}>
              See how it works
            </button>
          </div>

          <div className="hp-role-switch hp-enter" style={{ '--d': '780ms' }}>
            <span className="hp-role-switch-label">Explore a role</span>
            <div className="hp-role-tabs" role="tablist" aria-label="Sample job roles">
              {HERO_ROLES.map((r, i) => (
                <button
                  key={r.id}
                  type="button"
                  role="tab"
                  aria-selected={i === roleIndex}
                  className={`hp-role-tab ${i === roleIndex ? 'is-active' : ''}`}
                  onClick={() => pickRole(i)}
                >
                  {r.role}
                </button>
              ))}
            </div>
          </div>

          {/* Skill tags shown inline on small screens instead of floating */}
          <div className="hp-inline-tags">
            <span className="hp-role-switch-label">Tap a skill</span>
            <div className="hp-inline-tags-row">
              {FLOAT_SKILLS.filter(s => s.tier === 1).slice(0, 4).map(s => (
                <SkillTag
                  key={s.name}
                  inline
                  skill={s}
                  open={openSkill === `inline-${s.name}`}
                  onToggle={() => toggleSkill(`inline-${s.name}`)}
                  onClose={closeSkill}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="hp-hero-visual hp-enter" style={{ '--d': '820ms' }}>
          <div className="hp-card-parallax hp-depth-card">
            <div className="hp-card-glow" aria-hidden="true" />
            <ReadinessCard sample={sample} />
          </div>
        </div>
      </div>

      <button type="button" className="hp-scroll-hint" onClick={onHowItWorks} aria-label="Scroll to how it works" />
    </section>
  )
}
