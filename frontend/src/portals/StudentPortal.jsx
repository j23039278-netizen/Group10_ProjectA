// SEAGAS — Student portal: every page a signed-in student can open.
// Loaded on its own (see App.jsx), so advisor and admin code never reaches a student's browser.
import { Routes, Route, Navigate } from 'react-router-dom'
import PortalLayout from './PortalLayout'
import Dashboard from '../pages/Dashboard'
import Profile from '../pages/Profile'
import JobAnalysis from '../pages/JobAnalysis'
import SkillGap from '../pages/SkillGap'
import Recommendations from '../pages/Recommendations'
import ProgressTracking from '../pages/ProgressTracking'
import CvExport from '../pages/CvExport'

const NAV = [
  { path: '/',                label: 'Dashboard',       icon: '📊' },
  { path: '/profile',         label: 'My Profile',      icon: '👤' },
  { path: '/job-analysis',    label: 'Job Analysis',    icon: '📄' },
  { path: '/skill-gap',       label: 'Skill Gap',       icon: '🎯' },
  { path: '/recommendations', label: 'Recommendations', icon: '💡' },
  { path: '/progress',        label: 'Progress',        icon: '📈' },
]

export default function StudentPortal({ user, onLogout }) {
  return (
    <PortalLayout user={user} navTitle="Menu" navItems={NAV} onLogout={onLogout}>
      <Routes>
        <Route path="/"                element={<Dashboard onLogout={onLogout} />} />
        <Route path="/profile"         element={<Profile />} />
        <Route path="/job-analysis"    element={<JobAnalysis />} />
        <Route path="/skill-gap"       element={<SkillGap />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/progress"        element={<ProgressTracking />} />
        <Route path="/cv"              element={<CvExport />} />
        <Route path="*"                element={<Navigate to="/" />} />
      </Routes>
    </PortalLayout>
  )
}
