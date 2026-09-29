// SEAGAS logo mark: rising skill bars under an arc. `dark` = for navy backgrounds
export default function LogoMark({ dark = false, className = '' }) {
  const lead = dark ? '#ffffff' : '#0E2A47'
  const bars = dark
    ? ['#0f6f69', '#128a82', '#14a095', '#16B3A6']
    : ['#a8e6df', '#6fd0c6', '#3fc2b6', '#16B3A6']
  return (
    <svg className={className} viewBox="0 0 140 128" aria-hidden="true">
      <path className="hp-logo-arc" d="M12 54 Q48 6 110 8" fill="none" stroke={lead} strokeWidth="9" strokeLinecap="round" />
      <rect className="hp-logo-bar" x="0"   y="68" width="22" height="58"  rx="5" fill={lead} />
      <rect className="hp-logo-bar" x="37"  y="96" width="14" height="30"  rx="3" fill={bars[0]} style={{ animationDelay: '.1s' }} />
      <rect className="hp-logo-bar" x="63"  y="80" width="14" height="46"  rx="3" fill={bars[1]} style={{ animationDelay: '.2s' }} />
      <rect className="hp-logo-bar" x="89"  y="60" width="14" height="66"  rx="3" fill={bars[2]} style={{ animationDelay: '.3s' }} />
      <rect className="hp-logo-bar" x="115" y="20" width="22" height="106" rx="5" fill={bars[3]} style={{ animationDelay: '.4s' }} />
    </svg>
  )
}
