// SEAGAS Home — "Who's it for?" cards (click / tap to expand details)
import { useState } from 'react'
import { AUDIENCES } from './data'
import { useInView } from './hooks'
import Icon from './Icon'

export default function Audience() {
  const [ref, inView] = useInView(0.2)
  const [active, setActive] = useState('students')
  return (
    <div ref={ref} className="hp-audience">
      {AUDIENCES.map((a, i) => {
        const open = active === a.id
        return (
          <button
            key={a.id}
            type="button"
            className={`hp-aud-card hp-reveal ${inView ? 'is-visible' : ''} ${open ? 'is-open' : ''}`}
            style={{ '--d': `${i * 120}ms` }}
            onClick={() => setActive(a.id)}
            aria-expanded={open}
          >
            <span className="hp-aud-icon"><Icon name={a.icon} size={26} /></span>
            <span className="hp-aud-title">{a.title}</span>
            <span className="hp-aud-text">{a.text}</span>
            <span className="hp-aud-points" hidden={!open}>
              {a.points.map(p => <span key={p} className="hp-aud-point">{p}</span>)}
            </span>
            <span className="hp-aud-more" aria-hidden="true">{open ? '' : 'See more →'}</span>
          </button>
        )
      })}
    </div>
  )
}
