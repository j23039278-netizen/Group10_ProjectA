// SEAGAS — Sidebar Navigation
import { useNavigate, useLocation } from 'react-router-dom'
import emblem from '../assets/brand/seagas-emblem.png'
import { AFFILIATION } from '../pages/home/BrandLogo'

const PORTAL_NAMES = { student: 'Student Portal', advisor: 'Advisor Portal', admin: 'Admin Portal' }

// The portal passes its own menu, so this file holds no student, advisor or admin pages.
export default function Sidebar({ user, navTitle, navItems, onLogout }) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const role      = user?.role || ''
  const userName  = user?.full_name || 'User'

  const isActive = (path) => location.pathname === path

  return (
    <div className="sb-root" style={{
      width: '220px', background: 'var(--s-side-bg, #1a1f2e)', position: 'fixed',
      top: 0, left: 0, height: '100vh', display: 'flex',
      flexDirection: 'column', zIndex: 10
    }}>
      {/* Logo */}
      <div className="sb-head" style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {/* The logo lockup, as on the sign-in page: emblem on the left, SEAGAS above the course line
            on the right. The portal's tagline sits under it, spread over the lockup's full width
            (from the emblem's left edge to the end of the course line). */}
        <div style={{ display: 'inline-flex', flexDirection: 'column', marginLeft: '-4px', maxWidth: 'calc(100% + 4px)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src={emblem} alt="" aria-hidden="true" style={{ width: '34px', height: '34px', objectFit: 'contain', flex: 'none' }} />
            <div style={{ minWidth: 0 }}>
              <div className="sb-brand" style={{ fontSize: '20px', fontWeight: '700', color: '#fff', letterSpacing: '-0.2px', lineHeight: 1.05 }}>
                SEAGAS
              </div>
              <div className="sb-affiliation" style={{ fontSize: '9px', fontWeight: '600', color: 'rgba(255,255,255,0.7)', marginTop: '3px', letterSpacing: '0.1px', whiteSpace: 'nowrap' }}>
                {AFFILIATION}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Which portal this is, above the signed-in user (own class: the themes' tagline rules
          do not swap the text) */}
      <div className="sb-portal" style={{ padding: '14px 20px 0', fontSize: '12px', fontWeight: '700', color: 'rgba(255,255,255,0.85)',
                                          textTransform: 'uppercase', letterSpacing: '1.5px', lineHeight: 1.2 }}>
        {PORTAL_NAMES[role] || 'Employability Platform'}
      </div>

      {/* User */}
      <div className="sb-user" style={{
        padding: '10px 20px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', gap: '10px'
      }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%', flex: 'none',
          background: 'var(--s-accent, #2d5be3)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '12px', fontWeight: '700', color: '#fff'
        }}>
          {userName.charAt(0).toUpperCase()}
        </div>
        {/* One line; a long name ends in "…" and shows in full on hover */}
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="sb-name" title={userName} style={{ fontSize: '13px', fontWeight: '600', color: '#fff',
                                                             whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{userName}</div>
          <div className="sb-role" style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', textTransform: 'capitalize' }}>{role}</div>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ padding: '12px 0', flex: 1 }}>
        <div className="sb-navtitle" style={{ fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(255,255,255,0.3)', padding: '12px 20px 6px' }}>
          {navTitle}
        </div>
        {navItems.map(item => (
          <div
            key={item.path}
            className={`sb-item${isActive(item.path) ? ' active' : ''}`}
            onClick={() => navigate(item.path)}
            style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '9px 20px', cursor: 'pointer', fontSize: '13px',
              fontWeight: '500', transition: 'all .15s',
              borderLeft: `3px solid ${isActive(item.path) ? 'var(--s-accent, #2d5be3)' : 'transparent'}`,
              background: isActive(item.path) ? 'var(--s-side-active, rgba(45,91,227,0.25))' : 'transparent',
              color: isActive(item.path) ? '#fff' : 'rgba(255,255,255,0.55)',
            }}
          >
            <span style={{ fontSize: '15px' }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div className="sb-foot" style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button
          className="sb-signout"
          onClick={onLogout}
          style={{
            width: '100%', padding: '8px',
            background: 'rgba(255,255,255,0.06)',
            color: 'rgba(255,255,255,0.5)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '7px', fontSize: '12px', cursor: 'pointer'
          }}
        >
          ← Sign out
        </button>
      </div>
    </div>
  )
}