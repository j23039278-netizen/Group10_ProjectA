// SEAGAS Home — expandable career role cards
import { useState } from 'react'
import { CAREER_ROLES } from './data'
import { useInView } from './hooks'
import Icon from './Icon'

function RoleCard({ role, open, onToggle, onExplore, delay, inView }) {
  const panelId = `hp-role-${role.id}`
  return (
    <div
      className={`hp-role-card hp-reveal ${inView ? 'is-visible' : ''} ${open ? 'is-open' : ''}`}
      style={{ '--d': `${delay}ms` }}
    >
      <button type="button" className="hp-role-card-head" onClick={onToggle} aria-expanded={open} aria-controls={panelId}>
        <span className="hp-role-icon"><Icon name={role.icon} size={24} /></span>
        <span className="hp-role-text">
          <span className="hp-role-name">{role.role}</span>
          <span className="hp-role-blurb">{role.blurb}</span>
        </span>
        <span className="hp-role-plus" aria-hidden="true"><Icon name="plus" size={16} /></span>
      </button>

      <div id={panelId} className="hp-role-panel" hidden={!open}>
        <div className="hp-role-panel-inner">
          <div className="hp-hv-label">Core skills</div>
          <div className="hp-hv-chips">
            {role.core.map(s => <span key={s} className="hp-chip">{s}</span>)}
          </div>
          <div className="hp-hv-label">Example skill gaps</div>
          <div className="hp-hv-chips">
            {role.gaps.map(s => <span key={s} className="hp-status-chip hp-status-gap">{s}</span>)}
          </div>
          <div className="hp-hv-label">Sample readiness</div>
          <div className="hp-role-score">
            <span className="hp-bar"><span className="hp-bar-fill hp-fill-brand is-now" style={{ '--w': `${role.score}%` }} /></span>
            <b>{role.score}%</b>
          </div>
          <button type="button" className="hp-link-btn" onClick={onExplore}>
            Explore role <span className="hp-arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default function CareerRoles({ onExplore }) {
  const [ref, inView] = useInView(0.15)
  const [open, setOpen] = useState(null)
  return (
    <div ref={ref} className="hp-roles">
      {CAREER_ROLES.map((r, i) => (
        <RoleCard
          key={r.id}
          role={r}
          inView={inView}
          delay={i * 80}
          open={open === r.id}
          onToggle={() => setOpen(cur => (cur === r.id ? null : r.id))}
          onExplore={onExplore}
        />
      ))}
    </div>
  )
}
