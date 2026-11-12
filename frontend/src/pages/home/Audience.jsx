// SEAGAS Home - "Who's it for?" cards. All three show their details, so the cards are the
// same height and the three kinds of user can be compared at a glance.
import { AUDIENCES } from './data'
import { useInView } from './hooks'
import Icon from './Icon'

export default function Audience() {
  const [ref, inView] = useInView(0.2)
  return (
    <div ref={ref} className="hp-audience">
      {AUDIENCES.map((a, i) => (
        <div
          key={a.id}
          className={`hp-aud-card is-open hp-reveal ${inView ? 'is-visible' : ''}`}
          style={{ '--d': `${i * 120}ms` }}
        >
          <span className="hp-aud-icon"><Icon name={a.icon} size={26} /></span>
          <span className="hp-aud-title">{a.title}</span>
          <span className="hp-aud-text">{a.text}</span>
          <span className="hp-aud-points">
            {a.points.map(pt => <span key={pt} className="hp-aud-point">{pt}</span>)}
          </span>
        </div>
      ))}
    </div>
  )
}
