// SEAGAS — Home (landing) page shown to visitors before login.
// Everything here is a visual preview with sample data; the real assessment lives behind /login.
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrandLogo, BrandEmblem } from './home/BrandLogo'
import Hero from './home/Hero'
import HowItWorks from './home/HowItWorks'
import MatchDemo from './home/MatchDemo'

// Small dots around the three clusters (students, advisors, universities): [x, y, r]
const LINK_NODES = [
  [95, 395, 4], [190, 470, 3], [110, 480, 3], [200, 390, 2.5], [60, 440, 2.5],
  [560, 90, 3], [650, 95, 4], [600, 60, 2.5], [540, 140, 2.5], [665, 150, 3],
  [1010, 395, 3], [1110, 470, 4], [1100, 390, 2.5], [1020, 480, 3], [1150, 430, 2.5],
]

// Number of rising steps behind the Recommendations & progress section
const GROW_BARS = 24

// Destination pins on the Career paths "explore" map: [left %, top %, pulse delay s]
const EXPLORE_PINS = [[10, 20, 0], [91, 15, 1.2], [7.5, 83, 2.4], [93, 87, 0.6], [28, 96, 1.8], [73, 3, 3]]

// Skill names that drift up behind the Skill matching section: [word, left %, seconds, start offset]
const RISE_TOKENS = [
  ['Python', 4, 22, 0], ['SQL', 12, 26, 9], ['Excel', 20, 19, 4], ['React', 28, 24, 15], ['Git', 36, 21, 7],
  ['Power BI', 63, 25, 12], ['AWS', 71, 20, 2], ['Docker', 79, 27, 18], ['Linux', 87, 23, 6], ['Tableau', 94, 21, 11],
  ['Statistics', 8, 28, 20], ['Teamwork', 91, 26, 23], ['Java', 46, 30, 14], ['Machine Learning', 55, 29, 25],
  ['Communication', 16, 31, 27], ['Cloud', 83, 24, 16],
]
import SkillGapPreview from './home/SkillGapPreview'
import CareerRoles from './home/CareerRoles'
import { RecommendationPreview, ProgressPreview } from './home/NextStep'
import Audience from './home/Audience'
import Preloader from './home/Preloader'
import { groupOf } from './home/skillGroups'
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

  useCanvasColor('#ffffff')

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

  // Keep the same section in view when the window is resized (e.g. desktop -> phone width).
  // Without this the browser keeps the old scroll offset, which lands on a different section
  // once the page gets taller or shorter.
  useEffect(() => {
    const NAV_LINE = 80
    let anchor = null
    let width = window.innerWidth
    let raf = 0
    const sections = () => [...document.querySelectorAll('.hp-hero, .hp main > section')]

    const remember = () => {
      if (window.innerWidth !== width) return   // mid-resize: keep the anchor from before
      const el = sections().filter(s => s.getBoundingClientRect().top <= NAV_LINE).pop()
      if (!el) { anchor = null; return }
      const r = el.getBoundingClientRect()
      anchor = { el, ratio: (NAV_LINE - r.top) / Math.max(r.height, 1) }
    }
    const restore = () => {
      if (anchor) {
        const r = anchor.el.getBoundingClientRect()
        const top = window.scrollY + r.top + anchor.ratio * r.height - NAV_LINE
        window.scrollTo({ top, behavior: 'instant' })
      }
      width = window.innerWidth
    }
    const onResize = () => {
      if (window.innerWidth === width) return
      cancelAnimationFrame(raf)
      // Wait two frames so React re-renders that depend on the width have landed
      raf = requestAnimationFrame(() => { raf = requestAnimationFrame(restore) })
    }

    remember()
    window.addEventListener('scroll', remember, { passive: true })
    window.addEventListener('resize', onResize)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('scroll', remember)
      window.removeEventListener('resize', onResize)
    }
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
            <div className="hp-nav-actions">
              <button type="button" className="hp-btn hp-btn-primary hp-btn-sm" onClick={goLogin}>Sign in</button>
            </div>
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
            <span key={i} className={`hp-marquee-item hp-sg-${groupOf(s)}`}>{s}</span>
          ))}
        </div>
      </div>

      <main>
        <section id="how" className="hp-section hp-route-section">
          {/* Background: a faint route from bottom left (your profile) to top right (your plan),
              with four stops for the four steps and a red dot travelling along it */}
          <div className="hp-route-bg" aria-hidden="true">
            <svg viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice">
              <defs>
                <linearGradient id="hp-route-fade" x1="0" x2="1" y1="0" y2="0">
                  <stop offset="0" stopColor="#c8102e" stopOpacity="0" />
                  <stop offset=".15" stopColor="#c8102e" stopOpacity=".35" />
                  <stop offset=".85" stopColor="#c8102e" stopOpacity=".35" />
                  <stop offset="1" stopColor="#c8102e" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path id="hp-route-path" className="hp-route-line" d="M -40 560 C 180 560, 260 380, 430 380 S 700 250, 820 230 S 1060 90, 1240 40" />
              {[[214, 470], [546, 359], [820, 230], [1008, 146]].map(([x, y], i) => (
                <g key={i} className="hp-route-stop" style={{ animationDelay: `${i * 1.5}s` }}>
                  <circle cx={x} cy={y} r="14" className="hp-route-stop-ring" />
                  <circle cx={x} cy={y} r="5" className="hp-route-stop-dot" />
                </g>
              ))}
              <circle r="6" className="hp-route-runner">
                <animateMotion dur="6s" repeatCount="indefinite" rotate="auto">
                  <mpath href="#hp-route-path" />
                </animateMotion>
              </circle>
            </svg>
          </div>
          <div className="hp-container">
            <SectionHead
              eyebrow="How it works"
              title="From profile to plan in four steps"
              lead="Click a step to see what SEAGAS does at each stage."
            />
            <HowItWorks />
          </div>
        </section>

        <section id="skill-gap" className="hp-section hp-section-alt hp-rise-section">
          {/* Background: a grid and skill names drifting upwards, like data being analysed */}
          <div className="hp-rise-bg" aria-hidden="true">
            <div className="hp-rise-grid" />
            <div className="hp-rise-scan" />
            {RISE_TOKENS.map(([word, left, dur, delay], i) => (
              <span key={i} className="hp-rise-token" style={{ left: `${left}%`, animationDuration: `${dur}s`, animationDelay: `-${delay}s` }}>
                {word}
              </span>
            ))}
          </div>
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

        <section id="careers" className="hp-section hp-explore-section">
          {/* Background: an "explore" map. A large compass with a slow radar sweep in the middle,
              and destination pins (career roles) around it, joined by dotted paths */}
          <div className="hp-explore-bg" aria-hidden="true">
            <div className="hp-explore-radar">
              <div className="hp-explore-sweep" />
              <svg viewBox="-100 -100 200 200" className="hp-explore-compass">
                <circle r="96" /><circle r="70" /><circle r="44" /><circle r="18" />
                <path d="M -100 0 H 100 M 0 -100 V 100" />
                <path className="hp-explore-needle" d="M 0 -60 L 7 0 L 0 60 L -7 0 Z" />
              </svg>
            </div>
            <svg viewBox="0 0 1200 600" preserveAspectRatio="none" className="hp-explore-paths">
              <path d="M 600 300 Q 360 160 120 120 M 600 300 Q 820 120 1090 90 M 600 300 Q 330 430 90 500
                       M 600 300 Q 900 470 1120 520 M 600 300 Q 470 520 340 575 M 600 300 Q 760 40 880 20" />
            </svg>
            {EXPLORE_PINS.map(([left, top, delay], i) => (
              <span key={i} className="hp-explore-pin" style={{ left: `${left}%`, top: `${top}%`, animationDelay: `${delay}s` }} />
            ))}
          </div>
          <div className="hp-container">
            <SectionHead
              eyebrow="Career paths"
              title="Explore where your skills could take you"
              lead="Open a role to see its core skills, common gaps and a sample readiness score."
            />
            <CareerRoles onExplore={goLogin} />
          </div>
        </section>

        <section className="hp-section hp-section-alt hp-grow-section">
          {/* Background: "watch yourself improve". Steps rising from left to right along the
              bottom, growing in a wave, and an upward trend line that draws itself again and again */}
          <div className="hp-grow-bg" aria-hidden="true">
            <div className="hp-grow-bars">
              {Array.from({ length: GROW_BARS }, (_, i) => (
                <span key={i} style={{ height: `${14 + (i / (GROW_BARS - 1)) * 58}%`, animationDelay: `${i * 0.18}s` }} />
              ))}
            </div>
            <svg viewBox="0 0 1200 600" preserveAspectRatio="none" className="hp-grow-trend">
              <path pathLength="100" d="M 0 540 C 160 520, 260 470, 380 450 S 600 380, 720 330 S 960 200, 1200 90" />
            </svg>
            <span className="hp-grow-chip" style={{ left: '8%', animationDelay: '0s' }}>+12%</span>
            <span className="hp-grow-chip" style={{ left: '90%', animationDelay: '2.5s' }}>+8%</span>
            <span className="hp-grow-chip" style={{ left: '15%', animationDelay: '5s' }}>Strong</span>
            <span className="hp-grow-chip" style={{ left: '84%', animationDelay: '7.5s' }}>+15%</span>
          </div>
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

        <section id="who" className="hp-section hp-link-section">
          {/* Background: students, advisors and universities as three faint clusters joined by
              lines, with a light travelling student -> advisor -> university */}
          <div className="hp-link-bg" aria-hidden="true">
            <svg viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice">
              <path id="hp-link-path" className="hp-link-line" d="M 140 430 Q 380 170 600 120 Q 820 170 1060 430" />
              <path className="hp-link-line" d="M 140 430 Q 600 600 1060 430" />
              {LINK_NODES.map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} className="hp-link-node" />)}
              {[[140, 430], [600, 120], [1060, 430]].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="16" className="hp-link-hub" style={{ animationDelay: `${i * 2}s` }} />
              ))}
              <circle r="5" className="hp-link-runner">
                <animateMotion dur="9s" repeatCount="indefinite"><mpath href="#hp-link-path" /></animateMotion>
              </circle>
            </svg>
          </div>
          <div className="hp-container">
            <SectionHead eyebrow="Who's it for" title="Built for everyone on the path to employment" />
            <Audience />
          </div>
        </section>

        <section className="hp-section hp-section-cta">
          <div className="hp-container">
            <div ref={ctaRef} className={`hp-cta hp-reveal hp-reveal-scale ${ctaInView ? 'is-visible' : ''}`}>
              <div className="hp-cta-bg" aria-hidden="true" />
              {/* The rocket emblem, white and faint, floating on the right with sparks rising: ready for take-off */}
              <div className="hp-cta-rocket" aria-hidden="true"><BrandEmblem className="hp-cta-rocket-img" /></div>
              <div className="hp-cta-sparks" aria-hidden="true">
                {[12, 22, 34, 66, 76, 86, 93].map((left, i) => (
                  <span key={i} style={{ left: `${left}%`, animationDelay: `${i * 0.9}s`, animationDuration: `${5 + (i % 3)}s` }} />
                ))}
              </div>
              <div className="hp-cta-sheen" aria-hidden="true" />
              <h2 className="hp-h2">Ready to understand your career readiness?</h2>
              <p>Find your strengths. Discover your gaps. Build what comes next.</p>
              <div className="hp-cta-row hp-cta-center">
                <button type="button" className="hp-btn hp-btn-primary hp-cta-pulse" onClick={goLogin}>
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
