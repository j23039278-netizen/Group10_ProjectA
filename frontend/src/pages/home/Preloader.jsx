// SEAGAS Home — full-screen splash shown while the landing page loads
import { BrandWordmark } from './BrandLogo'
import ringSrc from '../../assets/brand/seagas-emblem-ring.png'
import arrowSrc from '../../assets/brand/seagas-emblem-arrow.png'

export default function Preloader({ leaving, onSpeedUp }) {
  // Each tap speeds up every animation inside the splash (the exit slide is a transition, so it is untouched)
  const handlePointerDown = (e) => {
    if (leaving || !onSpeedUp) return
    const rate = onSpeedUp()
    e.currentTarget.getAnimations({ subtree: true }).forEach((a) => { a.playbackRate = rate })
  }

  return (
    <div
      className={`hp-preloader ${leaving ? 'is-leaving' : ''}`}
      role="status"
      aria-label="Loading SEAGAS"
      onPointerDown={handlePointerDown}
    >
      <div className="hp-preloader-glow" aria-hidden="true" />
      <div className="hp-preloader-brand">
        <div className="hp-preloader-mark">
          {/* Emblem split in two layers: the ring appears, then the arrow shoots in from the bottom-left */}
          <div className="hp-preloader-emblem" aria-hidden="true">
            <img src={ringSrc} alt="" className="hp-pre-ring" draggable="false" />
            <span className="hp-pre-arrow">
              <img src={arrowSrc} alt="" draggable="false" />
            </span>
            <span className="hp-pre-impact" />
          </div>
        </div>
        <BrandWordmark className="hp-preloader-wordmark" />
        <span className="hp-preloader-tag">FROM CAMPUS TO CAREER</span>
      </div>
      <div className="hp-preloader-bar" aria-hidden="true"><span /></div>
    </div>
  )
}
