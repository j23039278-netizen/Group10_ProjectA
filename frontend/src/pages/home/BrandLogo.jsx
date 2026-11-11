// SEAGAS brand logo (A2 teal-to-blue gradient artwork, white wordmark for dark backgrounds)
import logoSrc from '../../assets/brand/seagas-logo.png'
import emblemSrc from '../../assets/brand/seagas-emblem.png'
import wordmarkSrc from '../../assets/brand/seagas-wordmark.png'

// The course line shown under the logo everywhere (home, sign-in pages, portal sidebars)
export const AFFILIATION = 'INTI × Swinburne · COS40005'

// Emblem on the left; "Seagas" above the course line on the right (navbar, sign-in pages).
// className sizes the emblem (its height sets the lockup's height).
export function BrandLogo({ className = '' }) {
  return (
    <span role="img" aria-label={`Seagas, ${AFFILIATION}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <img src={emblemSrc} alt="" className={className} draggable="false" style={{ height: '44px', width: 'auto' }} />
      <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}>
        <img src={wordmarkSrc} alt="" draggable="false" style={{ display: 'block', height: '22px', width: 'auto' }} />
        <span style={{ fontSize: '10.5px', fontWeight: 600, letterSpacing: '0.5px', color: '#6b7280', whiteSpace: 'nowrap', lineHeight: 1 }}>
          {AFFILIATION}
        </span>
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
