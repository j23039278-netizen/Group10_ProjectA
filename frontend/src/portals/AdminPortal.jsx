// SEAGAS — Admin portal: every page a signed-in admin can open.
// Loaded on its own (see App.jsx), so it is only downloaded for admin accounts.
import { Routes, Route, Navigate } from 'react-router-dom'
import PortalLayout from './PortalLayout'
import AdminUsers from '../pages/AdminUsers'
import AdminLibrary from '../pages/AdminLibrary'

const NAV = [
  { path: '/',        label: 'User Management', icon: '👥' },
  { path: '/library', label: 'Skills & Roles',  icon: '📚' },
]

export default function AdminPortal({ user, onLogout }) {
  return (
    <PortalLayout user={user} navTitle="Administration" navItems={NAV} onLogout={onLogout}>
      <Routes>
        <Route path="/"        element={<AdminUsers />} />
        <Route path="/library" element={<AdminLibrary />} />
        <Route path="*"        element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
