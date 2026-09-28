// SEAGAS — Sidebar Navigation
import { useNavigate, useLocation } from 'react-router-dom'

export default function Sidebar({ onLogout }) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const role      = localStorage.getItem('role')
  const userName  = localStorage.getItem('fullName') || 'User'

  const studentNav = [
    { path: '/',                label: 'Dashboard',       icon: '📊' },
    { path: '/profile',         label: 'My Profile',      icon: '👤' },
    { path: '/job-analysis',    label: 'Job Analysis',    icon: '📄' },
    { path: '/skill-gap',       label: 'Skill Gap',       icon: '🎯' },
    { path: '/recommendations', label: 'Recommendations', icon: '💡' },
  ]

  const advisorNav = [
    { path: '/', label: 'Cohort Overview', icon: '📊' },
  ]

  const navItems = role === 'advisor' ? advisorNav : studentNav

  const isActive = (path) => location.pathname === path

  return (
    <div style={{
      width: '220px', background: '#1a1f2e', position: 'fixed',
      top: 0, left: 0, height: '100vh', display: 'flex',
      flexDirection: 'column', zIndex: 10
    }}>
      {/* Logo */}
      <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ fontSize: '22px', fontWeight: '700', color: '#fff', letterSpacing: '-0.3px' }}>
          SEAGAS
        </div>
        <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', marginTop: '2px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
          Employability Platform
        </div>
      </div>

      {/* User */}
      <div style={{
        padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', gap: '10px'
      }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          background: '#2d5be3', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '12px', fontWeight: '700', color: '#fff'
        }}>
          {userName.charAt(0).toUpperCase()}
        </div>
        <div>
          <div style={{ fontSize: '13px', fontWeight: '600', color: '#fff' }}>{userName}</div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', textTransform: 'capitalize' }}>{role}</div>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ padding: '12px 0', flex: 1 }}>
        <div style={{ fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(255,255,255,0.3)', padding: '12px 20px 6px' }}>
          {role === 'advisor' ? 'Overview' : 'Menu'}
        </div>
        {navItems.map(item => (
          <div
            key={item.path}
            onClick={() => navigate(item.path)}
            style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '9px 20px', cursor: 'pointer', fontSize: '13px',
              fontWeight: '500', transition: 'all .15s',
              borderLeft: `3px solid ${isActive(item.path) ? '#2d5be3' : 'transparent'}`,
              background: isActive(item.path) ? 'rgba(45,91,227,0.25)' : 'transparent',
              color: isActive(item.path) ? '#fff' : 'rgba(255,255,255,0.55)',
            }}
          >
            <span style={{ fontSize: '15px' }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button
          onClick={() => {
            localStorage.removeItem('token')
            localStorage.removeItem('role')
            localStorage.removeItem('fullName')
            window.location.href = '/'
          }}
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