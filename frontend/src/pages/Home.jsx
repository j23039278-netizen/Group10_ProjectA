// SEAGAS — Home (landing) page shown to visitors before login.
// Everything here is a visual preview with sample data; the real assessment lives behind /login.
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrandLogo, BrandEmblem } from './home/BrandLogo'
import Hero from './home/Hero'
import HowItWorks from './home/HowItWorks'
import MatchDemo from './home/MatchDemo'
import SkillGapPreview from './home/SkillGapPreview'
import CareerRoles from './home/CareerRoles'
import { RecommendationPreview, ProgressPreview } from './home/NextStep'
import Audience from './home/Audience'
import Preloader from './home/Preloader'
import { useInView, prefersReducedMotion, useCanvasColor } from './home/hooks'
import './Home.css'

const NAV = [
  { id: 'how',       label: 'How it works' },
  { id: 'skill-gap', label: 'Skill gap' },
  { id: 'careers',   label: 'Career paths' },
  { id: 'who',       label: "Who's it for" },
]

const MARQUEE_SKILLS = [
  'Python', 'SQL', 'Power BI', 'Tableau', 'Machine Learning', 'TensorFlow', 'PyTorch',
  'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Linux', 'Git',
  'React', 'JavaScript', 'Wireshark', 'Nmap', 'SIEM', 'Pandas', 'NumPy',
  'Generative AI', 'Critical Thinking', 'Communication', 'Teamwork', 'Project Management',
]

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 72
  window.scrollTo({ top, behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
}

// Splash timing: at least MIN_MS (so the logo animation can play), then wait for the
// window "load" event, but never longer than MAX_MS. LEAVE_MS matches the CSS exit.
const PRELOAD_MIN_MS = 2200
const PRELOAD_MAX_MS = 3000
const PRELOAD_LEAVE_MS = 850
// Each tap/click on the splash makes it play this much faster, up to MAX_SPEED
const PRELOAD_TAP_SPEEDUP = 1.6
const PRELOAD_MAX_SPEED = 6

// Plays once per page load; navigating back to Home inside the app (e.g. from /login) skips it
let preloaderShown = false

function SectionHead({ eyebrow, title, lead }) {
  const [ref, inView] = useInView(0.4)
  return (
    <div ref={ref} className={`hp-section-head hp-reveal ${inView ? 'is-visible' : ''}`}>
      <span className="hp-eyebrow">{eyebrow}</span>
      <h2 className="hp-h2">{title}</h2>
      {lead && <p className="hp-lead">{lead}</p>}
    </div>
  )
}

export default function Home() {
  // 'loading' → splash only; 'leaving' → splash slides away while the page mounts; 'done'
  const [stage, setStage] = useState(preloaderShown ? 'done' : 'loading')

  useCanvasColor('#071D33')

  // Tapping the splash speeds it up: the splash clock and its CSS animations run at this rate
  const speedRef = useRef(1)

  useEffect(() => {
    if (stage !== 'loading') return
    preloaderShown = true
    const reduced = prefersReducedMotion()
    const minMs = reduced ? 400 : PRELOAD_MIN_MS
    const maxMs = reduced ? minMs : PRELOAD_MAX_MS
    let loaded = document.readyState === 'complete'
    const onLoaded = () => { loaded = true }
    if (!loaded) window.addEventListener('load', onLoaded, { once: true })

    // Splash clock advances faster while sped up
    let elapsed = 0
    let last = performance.now()
    const tick = setInterval(() => {
      const now = performance.now()
      elapsed += (now - last) * speedRef.current
      last = now
      if ((loaded && elapsed >= minMs) || elapsed >= maxMs) {
        clearInterval(tick)
        setStage('leaving')
      }
    }, 40)

    return () => {
      window.removeEventListener('load', onLoaded)
      clearInterval(tick)
    }
  }, [stage])

  const speedUp = () => {
    if (stage !== 'loading') return 1
    speedRef.current = Math.min(speedRef.current * PRELOAD_TAP_SPEEDUP, PRELOAD_MAX_SPEED)
    return speedRef.current
  }

  // Remove the splash once its exit animation has finished
  useEffect(() => {
    if (stage !== 'leaving') return
    const t = setTimeout(() => setStage('done'), prefersReducedMotion() ? 200 : PRELOAD_LEAVE_MS)
    return () => clearTimeout(t)
  }, [stage])

  return (
    <div className="hp">
      {stage !== 'done' && <Preloader leaving={stage === 'leaving'} onSpeedUp={speedUp} />}
      {stage !== 'loading' && <HomeContent />}
    </div>
  )
}

function HomeContent() {
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)
  const [activeNav, setActiveNav] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [ctaRef, ctaInView] = useInView(0.3)

  const goLogin = () => navigate('/login')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Highlight the nav item for the section currently in view
  useEffect(() => {
    const sections = NAV.map(n => document.getElementById(n.id)).filter(Boolean)
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) setActiveNav(e.target.id) })
    }, { rootMargin: '-45% 0px -50% 0px' })
    sections.forEach(s => observer.observe(s))
    return () => observer.disconnect()
  }, [])

  const onNav = (id) => {
    setMenuOpen(false)
    if (id === 'top') window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
    else scrollToSection(id)
  }

  return (
    <>
      {/* Nav (Home page only; the app Sidebar is untouched) */}
      <header className={`hp-nav ${scrolled || menuOpen ? 'is-scrolled' : ''}`}>
        <div className="hp-nav-inner">
          <button type="button" className="hp-logo hp-enter" style={{ '--d': '0ms' }} onClick={() => onNav('top')} aria-label="SEAGAS, back to top">
            <BrandLogo className="hp-logo-img" />
          </button>

          <nav className="hp-nav-links hp-enter" style={{ '--d': '80ms' }} aria-label="Home page sections">
            {NAV.map(n => (
              <button
                key={n.id}
                type="button"
                className={`hp-nav-link ${activeNav === n.id ? 'is-active' : ''}`}
                onClick={() => onNav(n.id)}
              >
                {n.label}
              </button>
            ))}
            <button type="button" className="hp-btn hp-btn-primary hp-btn-sm" onClick={goLogin}>Sign in</button>
          </nav>

          <button
            type="button"
            className={`hp-menu-btn ${menuOpen ? 'is-open' : ''}`}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(o => !o)}
          >
            <span /><span /><span />
          </button>
        </div>

        {menuOpen && (
          <div className="hp-mobile-menu">
            {NAV.map(n => (
              <button key={n.id} type="button" className="hp-mobile-link" onClick={() => onNav(n.id)}>{n.label}</button>
            ))}
            <button type="button" className="hp-btn hp-btn-primary" onClick={goLogin}>Sign in</button>
          </div>
        )}
      </header>

      <Hero onStart={goLogin} onHowItWorks={() => scrollToSection('how')} />

      {/* Skills marquee */}
      <div className="hp-marquee" aria-hidden="true">
        <div className="hp-marquee-track">
          {[...MARQUEE_SKILLS, ...MARQUEE_SKILLS].map((s, i) => (
            <span key={i} className="hp-marquee-item">{s}</span>
          ))}
        </div>
      </div>

      <main>
        <section id="how" className="hp-section">
          <div className="hp-container">
            <SectionHead
              eyebrow="How it works"
              title="From profile to plan in four steps"
              lead="Click a step to see what SEAGAS does at each stage."
            />
            <HowItWorks />
          </div>
        </section>

        <section id="skill-gap" className="hp-section hp-section-alt">
          <div className="hp-container">
            <SectionHead
              eyebrow="Skill matching"
              title="See how SEAGAS finds your skill gaps"
              lead="Run a quick demo analysis to see how your skills are compared with a job's requirements."
            />
            <MatchDemo />

            <div className="hp-subsection">
              <SectionHead
                eyebrow="Skill gap analysis"
                title="Know exactly how far each skill has to go"
                lead="Every required skill shows your current alignment against the level the job asks for."
              />
              <SkillGapPreview />
            </div>
          </div>
        </section>

        <section id="careers" className="hp-section">
          <div className="hp-container">
            <SectionHead
              eyebrow="Career paths"
              title="Explore where your skills could take you"
              lead="Open a role to see its core skills, common gaps and a sample readiness score."
            />
            <CareerRoles onExplore={goLogin} />
          </div>
        </section>

        <section className="hp-section hp-section-alt">
          <div className="hp-container">
            <SectionHead
              eyebrow="Recommendations & progress"
              title="Know your next step, and watch yourself improve"
              lead="Each gap comes with a course, certification or project. Re-run your assessment to track your progress."
            />
            <div className="hp-next">
              <RecommendationPreview onView={goLogin} />
              <ProgressPreview />
            </div>
          </div>
        </section>

        <section id="who" className="hp-section">
          <div className="hp-container">
            <SectionHead eyebrow="Who's it for" title="Built for everyone on the path to employment" />
            <Audience />
          </div>
        </section>

        <section className="hp-section hp-section-cta">
          <div className="hp-container">
            <div ref={ctaRef} className={`hp-cta hp-reveal hp-reveal-scale ${ctaInView ? 'is-visible' : ''}`}>
              <div className="hp-cta-bg" aria-hidden="true" />
              <h2 className="hp-h2">Ready to understand your career readiness?</h2>
              <p>Find your strengths. Discover your gaps. Build what comes next.</p>
              <div className="hp-cta-row hp-cta-center">
                <button type="button" className="hp-btn hp-btn-primary" onClick={goLogin}>
                  Check my readiness <span className="hp-arrow" aria-hidden="true">→</span>
                </button>
                <button type="button" className="hp-btn hp-btn-ghost" onClick={goLogin}>Sign in</button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="hp-footer">
        <div className="hp-container hp-footer-inner">
          <span className="hp-footer-brand">
            <BrandEmblem className="hp-footer-logo" />
            © 2026 SEAGAS · From campus to career · Group 10
          </span>
          <span>COS40005 Computing Technology Project A · Swinburne University / INTI International College Subang</span>
        </div>
      </footer>
    </>
  )
}
