// SEAGAS brand logo (A2 teal-to-blue gradient artwork, white wordmark for dark backgrounds)
import logoSrc from '../../assets/brand/seagas-logo.png'
import emblemSrc from '../../assets/brand/seagas-emblem.png'
import wordmarkSrc from '../../assets/brand/seagas-wordmark.png'
import intiSrc from '../../assets/brand/inti-logo.png'
import swinburneSrc from '../../assets/brand/swinburne-logo.png'

// The course line (portal sidebars)
export const AFFILIATION = 'INTI × SWINBURNE × COS40005'

// Rocket emblem + "Seagas" × Swinburne logo × INTI logo (home navbar, sign-in pages).
// scale shrinks the whole lockup (the sign-in card is narrower than the navbar). On narrow
// screens the two university logos are hidden (.brand-partners in Home.css).
export function BrandLogo({ className = '', scale = 1 }) {
  const px = (n) => `${Math.round(n * scale)}px`
  const times = <span aria-hidden="true" style={{ fontSize: px(18), fontWeight: 500, color: '#9ca3af', lineHeight: 1 }}>×</span>
  return (
    <span role="img" aria-label="Seagas × Swinburne University of Technology × INTI International University & Colleges"
          style={{ display: 'inline-flex', alignItems: 'center', gap: px(10) }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: px(6) }}>
        <img src={emblemSrc} alt="" className={className} draggable="false" style={{ height: px(40), width: 'auto' }} />
        <img src={wordmarkSrc} alt="" draggable="false" style={{ display: 'block', height: px(22), width: 'auto' }} />
      </span>
      <span className="brand-partners" style={{ display: 'inline-flex', alignItems: 'center', gap: px(10) }}>
        {times}
        <img src={swinburneSrc} alt="" draggable="false" style={{ display: 'block', height: px(36), width: 'auto' }} />
        {times}
        <img src={intiSrc} alt="" draggable="false" style={{ display: 'block', height: px(22), width: 'auto' }} />
      </span>
    </span>
  )
}

// The original emblem + wordmark artwork in one image
export function BrandLogoImage({ className = '' }) {
  return <img src={logoSrc} alt="Seagas" className={className} draggable="false" />
}

// Emblem only (footer, preloader)
export function BrandEmblem({ className = '' }) {
  return <img src={emblemSrc} alt="" aria-hidden="true" className={className} draggable="false" />
}

// "Seagas" wordmark only (preloader)
export function BrandWordmark({ className = '' }) {
  return <img src={wordmarkSrc} alt="Seagas" className={className} draggable="false" />
}
