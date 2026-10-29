// SEAGAS — Shared page frame for the signed-in portals: sidebar on the left, page on the right.
import Sidebar from '../components/Sidebar'

export default function PortalLayout({ user, navTitle, navItems, onLogout, children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f5f6fa' }}>
      <Sidebar user={user} navTitle={navTitle} navItems={navItems} onLogout={onLogout} />
      {/* minWidth 0: a wide table scrolls inside its card instead of widening the page */}
      <div style={{ marginLeft: '220px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  )
}
