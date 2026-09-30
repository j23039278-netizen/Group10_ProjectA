// SEAGAS brand logo (A2 teal-to-blue gradient artwork, white wordmark for dark backgrounds)
import logoSrc from '../../assets/brand/seagas-logo.png'
import emblemSrc from '../../assets/brand/seagas-emblem.png'
import wordmarkSrc from '../../assets/brand/seagas-wordmark.png'

// Emblem + "Seagas" side by side (navbar, Login / Register)
export function BrandLogo({ className = '' }) {
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
