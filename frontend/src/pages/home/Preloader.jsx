// SEAGAS Home — full-screen splash shown while the landing page loads
import LogoMark from './LogoMark'

export default function Preloader({ leaving }) {
  return (
    <div className={`hp-preloader ${leaving ? 'is-leaving' : ''}`} role="status" aria-label="Loading SEAGAS">
      <div className="hp-preloader-glow" aria-hidden="true" />
      <div className="hp-preloader-brand">
        <div className="hp-preloader-mark">
          <LogoMark dark className="hp-preloader-logo" />
        </div>
        <div className="hp-preloader-text">
          <span className="hp-preloader-name">SEAGAS</span>
          <span className="hp-preloader-tag">FROM CAMPUS TO CAREER</span>
        </div>
      </div>
      <div className="hp-preloader-bar" aria-hidden="true"><span /></div>
    </div>
  )
}
