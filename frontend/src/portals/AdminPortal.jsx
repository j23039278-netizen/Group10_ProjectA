// SEAGAS — Admin portal: every page a signed-in admin can open.
// Loaded on its own (see App.jsx), so it is only downloaded for admin accounts.
import { Routes, Route, Navigate } from 'react-router-dom'
import PortalLayout from './PortalLayout'
import AdminUsers from '../pages/AdminUsers'
import AdminIntake from '../pages/AdminIntake'
import AdminLibrary from '../pages/AdminLibrary'
import AdminResources from '../pages/AdminResources'
import AdminAudit from '../pages/AdminAudit'

const NAV = [
  { path: '/',        label: 'User Management', icon: '👥' },
  { path: '/intake',  label: 'Student Intake',  icon: '🧑‍🎓' },
  { path: '/library', label: 'Skills & Roles',  icon: '📚' },
  { path: '/resources', label: 'Learning Resources', icon: '🎓' },
  { path: '/audit',   label: 'Audit Log',       icon: '🧾' },
]

export default function AdminPortal({ user, onLogout }) {
  return (
    <PortalLayout user={user} navTitle="Administration" navItems={NAV} onLogout={onLogout}>
      <Routes>
        <Route path="/"        element={<AdminUsers />} />
        <Route path="/intake"  element={<AdminIntake />} />
        <Route path="/library" element={<AdminLibrary />} />
        <Route path="/resources" element={<AdminResources />} />
        <Route path="/audit"   element={<AdminAudit />} />
        <Route path="*"        element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
