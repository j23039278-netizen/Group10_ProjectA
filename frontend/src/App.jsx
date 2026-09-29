// SEAGAS — Main App with routing
import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import JobAnalysis from './pages/JobAnalysis'
import SkillGap from './pages/SkillGap'
import Recommendations from './pages/Recommendations'
import AdvisorDashboard from './pages/AdvisorDashboard'
import Sidebar from './components/Sidebar'
import './App.css'

function AppLayout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f5f6fa' }}>
      <Sidebar />
      <div style={{ marginLeft: '220px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        {children}
      </div>
    </div>
  )
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'))
  const [role, setRole] = useState(localStorage.getItem('role') || '')

  const handleLogin = (userRole) => {
    setIsLoggedIn(true)
    setRole(userRole)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    setIsLoggedIn(false)
    setRole('')
  }

  if (!isLoggedIn) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/"      element={<Home />} />
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="/register" element={<Register onLogin={handleLogin} />} />
          <Route path="*"      element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    )
  }

  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          {role === 'advisor' ? (
            <>
              <Route path="/" element={<AdvisorDashboard onLogout={handleLogout} />} />
              <Route path="*" element={<Navigate to="/" />} />
            </>
          ) : (
            <>
              <Route path="/"               element={<Dashboard onLogout={handleLogout} />} />
              <Route path="/profile"        element={<Profile />} />
              <Route path="/job-analysis"   element={<JobAnalysis />} />
              <Route path="/skill-gap"      element={<SkillGap />} />
              <Route path="/recommendations"element={<Recommendations />} />
              <Route path="*"               element={<Navigate to="/" />} />
            </>
          )}
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App