// SEAGAS — Main App with routing
// Everyone signs in on the same /login page. The backend says which role the
// account has, and only that role's portal is loaded: each portal is a separate
// download, so a student's browser never receives advisor or admin pages.
import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { authAPI } from './api/client'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import './App.css'

const PORTALS = {
  student: lazy(() => import('./portals/StudentPortal')),
  advisor: lazy(() => import('./portals/AdvisorPortal')),
  admin:   lazy(() => import('./portals/AdminPortal')),
}

const Loading = () => <div style={{ padding: '40px', color: '#8b92a8' }}>Loading...</div>

function clearSession() {
  localStorage.removeItem('token')
  // Older builds also kept these; the role now always comes from the backend
  localStorage.removeItem('role')
  localStorage.removeItem('fullName')
}

function App() {
  // user = { role, full_name } as reported by the backend, never read from the browser
  const [user, setUser]       = useState(null)
  const [checking, setChecking] = useState(!!localStorage.getItem('token'))

  // Returning visitor with a saved token: ask the backend who this is
  useEffect(() => {
    if (!checking) return
    authAPI.me()
      .then(res => acceptUser(res.data))
      .catch(() => clearSession())
      .finally(() => setChecking(false))
  }, [checking])

  // Only roles that have a portal can sign in to the app
  const acceptUser = (data) => {
    if (PORTALS[data.role]) setUser({ role: data.role, full_name: data.full_name })
    else clearSession()
  }

  const handleLogin = acceptUser

  const handleLogout = () => {
    clearSession()
    window.location.href = '/'
  }

  if (checking) return <Loading />

  if (!user) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/"         element={<Home />} />
          <Route path="/login"    element={<Login onLogin={handleLogin} />} />
          <Route path="/register" element={<Register onLogin={handleLogin} />} />
          <Route path="*"         element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    )
  }

  const Portal = PORTALS[user.role]

  return (
    <BrowserRouter>
      <Suspense fallback={<Loading />}>
        <Portal user={user} onLogout={handleLogout} />
      </Suspense>
    </BrowserRouter>
  )
}

export default App
