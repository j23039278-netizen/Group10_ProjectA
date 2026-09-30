// SEAGAS Home — full-screen splash shown while the landing page loads
import { BrandEmblem, BrandWordmark } from './BrandLogo'

export default function Preloader({ leaving }) {
  return (
    <div className={`hp-preloader ${leaving ? 'is-leaving' : ''}`} role="status" aria-label="Loading SEAGAS">
      <div className="hp-preloader-glow" aria-hidden="true" />
      <div className="hp-preloader-brand">
        <div className="hp-preloader-mark">
          <BrandEmblem className="hp-preloader-emblem" />
        </div>
        <BrandWordmark className="hp-preloader-wordmark" />
        <span className="hp-preloader-tag">FROM CAMPUS TO CAREER</span>
      </div>
      <div className="hp-preloader-bar" aria-hidden="true"><span /></div>
    </div>
  )
}
