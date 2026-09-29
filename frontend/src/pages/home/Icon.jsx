// SEAGAS Home — small line icons used on the landing page
const PATHS = {
  cloud: <path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.2 4.5 4.5 0 0 0 7 18Z" />,
  chart: <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M22 20H2" /></>,
  code: <><path d="m8 7-5 5 5 5" /><path d="m16 7 5 5-5 5" /><path d="m14 4-4 16" /></>,
  shield: <><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z" /><path d="m9 12 2 2 4-4" /></>,
  brain: <><circle cx="12" cy="5" r="2" /><circle cx="5" cy="12" r="2" /><circle cx="19" cy="12" r="2" /><circle cx="12" cy="19" r="2" /><path d="M12 7v10M7 12h10M6.5 10.5 10.5 6.5M17.5 13.5l-4 4" /></>,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18" /><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></>,
  target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" /></>,
  compare: <><path d="M7 4v16" /><path d="M17 4v16" /><path d="m3 8 4-4 4 4" /><path d="m13 16 4 4 4-4" /></>,
  gap: <><path d="M4 19h16" /><path d="M6 15h4v4H6z" /><path d="M14 9h4v10h-4z" /><path d="M14 5h4" strokeDasharray="2 2" /></>,
  student: <><path d="m2 9 10-5 10 5-10 5L2 9Z" /><path d="M6 11v5c3 2 9 2 12 0v-5" /></>,
  advisor: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7" /><path d="M18 14a6 6 0 0 1 3.5 6" /></>,
  university: <><path d="m3 9 9-5 9 5" /><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8" /><path d="M3 21h18" /></>,
  swap: <><path d="M4 8h15" /><path d="m15 4 4 4-4 4" /><path d="M20 16H5" /><path d="m9 12-4 4 4 4" /></>,
  plus: <><path d="M12 5v14" /><path d="M5 12h14" /></>,
  mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></>,
  lock: <><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></>,
  eye: <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></>,
  eyeOff: <><path d="M3 3l18 18" /><path d="M10.6 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.1M6.6 6.6A17 17 0 0 0 2 12s3.5 7 10 7a10 10 0 0 0 5.4-1.6" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></>,
  check: <path d="m5 12 5 5L20 7" />,
  alert: <><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 16h.01" /></>,
  back: <><path d="M19 12H5" /><path d="m11 18-6-6 6-6" /></>,
  spark:<><path d="M12 3v4M12 17v4M3 12h4M17 12h4" /><path d="m6 6 2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" /></>,
}

export default function Icon({ name, size = 22, className = '' }) {
  return (
    <svg
      className={className}
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  )
}
