// SEAGAS — Advisor portal: every page a signed-in advisor can open.
// Loaded on its own (see App.jsx), so it is only downloaded for advisor accounts.
import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { settingsAPI } from '../api/client'
import { applyBands } from '../utils/readiness'
import PortalLayout from './PortalLayout'
import AdvisorDashboard from '../pages/AdvisorDashboard'
import AdvisorStudentDetail from '../pages/AdvisorStudentDetail'
import AdvisorNewStudents from '../pages/AdvisorNewStudents'
// Shared with the admin portal; advisors change the entries of their own courses
import AdminLibrary from '../pages/AdminLibrary'
import AdminResources from '../pages/AdminResources'
import './advisorTheme.css'

const NAV = [
  { path: '/', label: 'Cohort Overview', icon: 'barChart' },
  { path: '/new-students', label: 'New Students', icon: 'userPlus' },
  { path: '/library', label: 'Skills & Roles', icon: 'book' },
  { path: '/resources', label: 'Learning Resources', icon: 'graduationCap' },
]

export default function AdvisorPortal({ user, onLogout }) {
  useEffect(() => { settingsAPI.get().then(r => applyBands(r.data)).catch(() => {}) }, [])

  return (
    <PortalLayout user={user} navTitle="Overview" navItems={NAV} onLogout={onLogout} className="advisor-theme">
      <Routes>
        <Route path="/" element={<AdvisorDashboard />} />
        <Route path="/students/:userId" element={<AdvisorStudentDetail />} />
        <Route path="/new-students" element={<AdvisorNewStudents />} />
        <Route path="/library" element={<AdminLibrary />} />
        <Route path="/resources" element={<AdminResources />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
