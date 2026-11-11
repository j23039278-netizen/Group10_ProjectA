// SEAGAS — Admin portal: every page a signed-in admin can open.
// Loaded on its own (see App.jsx), so it is only downloaded for admin accounts.
import { Routes, Route, Navigate } from 'react-router-dom'
import PortalLayout from './PortalLayout'
import AdminUsers from '../pages/AdminUsers'
import AdminIntake from '../pages/AdminIntake'
import AdminLibrary from '../pages/AdminLibrary'
import AdminResources from '../pages/AdminResources'
import AdminAudit from '../pages/AdminAudit'
import AdminSettings from '../pages/AdminSettings'
import './adminTheme.css'

const NAV = [
  { path: '/',        label: 'User Management', icon: 'users' },
  { path: '/intake',  label: 'Student Intake',  icon: 'userPlus' },
  { path: '/library', label: 'Skills & Roles',  icon: 'book' },
  { path: '/resources', label: 'Learning Resources', icon: 'graduationCap' },
  { path: '/audit',   label: 'Audit Log',       icon: 'clipboardList' },
  { path: '/settings', label: 'System Settings', icon: 'settings' },
]

export default function AdminPortal({ user, onLogout }) {
  return (
    <PortalLayout user={user} navTitle="Administration" navItems={NAV} onLogout={onLogout} className="admin-theme">
      <Routes>
        <Route path="/"        element={<AdminUsers />} />
        <Route path="/intake"  element={<AdminIntake />} />
        <Route path="/library" element={<AdminLibrary />} />
        <Route path="/resources" element={<AdminResources />} />
        <Route path="/audit"   element={<AdminAudit />} />
        <Route path="/settings" element={<AdminSettings />} />
        <Route path="*"        element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
