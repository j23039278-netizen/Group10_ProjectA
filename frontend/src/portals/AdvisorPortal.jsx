// SEAGAS — Advisor portal: every page a signed-in advisor can open.
// Loaded on its own (see App.jsx), so it is only downloaded for advisor accounts.
import { Routes, Route, Navigate } from 'react-router-dom'
import PortalLayout from './PortalLayout'
import AdvisorDashboard from '../pages/AdvisorDashboard'

const NAV = [
  { path: '/', label: 'Cohort Overview', icon: '📊' },
]

export default function AdvisorPortal({ user, onLogout }) {
  return (
    <PortalLayout user={user} navTitle="Overview" navItems={NAV} onLogout={onLogout}>
      <Routes>
        <Route path="/" element={<AdvisorDashboard />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
