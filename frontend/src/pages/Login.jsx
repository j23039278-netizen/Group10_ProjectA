// SEAGAS — Login Page
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { authAPI } from '../api/client'
import AuthLayout, { Field, PasswordInput, FormAlert } from './auth/AuthLayout'

export default function Login({ onLogin }) {
  const location = useLocation()
  // Register sends people here with their email if the automatic sign-in didn't work
  const registeredEmail = location.state?.registeredEmail || ''

  const [role,     setRole]     = useState('student')
  const [email,    setEmail]    = useState(registeredEmail)
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res  = await authAPI.login(email, password)
      const data = res.data
      localStorage.setItem('token',    data.access_token)
      localStorage.setItem('role',     data.role)
      localStorage.setItem('fullName', data.full_name)
      onLogin(data.role)
    } catch (err) {
      setError(err.response
        ? 'Invalid email or password. Please try again.'
        : 'Cannot reach the server. Please make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const roles = [
    { id: 'student', label: 'Student' },
    { id: 'advisor', label: 'Advisor' },
    { id: 'admin',   label: 'Admin' },
  ]

  return (
    <AuthLayout
      heading={<>Welcome <span className="au-accent">back</span></>}
      title="Sign in"
      subtitle="Use the email and password for your SEAGAS account."
    >
      {registeredEmail && (
        <FormAlert type="success">Account created. Please sign in to continue.</FormAlert>
      )}

      {/* Role Selector */}
      <div className="au-roles" role="radiogroup" aria-label="I am signing in as">
        {roles.map(r => (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={role === r.id}
            className={`au-role ${role === r.id ? 'is-active' : ''}`}
            onClick={() => setRole(r.id)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Form */}
      <form onSubmit={handleLogin}>
        <Field id="login-email" label="Email" icon="mail">
          <input
            id="login-email"
            className="au-input"
            type="email" required
            autoComplete="email"
            placeholder={role === 'student' ? 'student@synthetic.example.com' : 'advisor@uni.edu.my'}
            value={email} onChange={e => setEmail(e.target.value)}
          />
        </Field>

        <Field id="login-password" label="Password" icon="lock">
          <PasswordInput
            id="login-password"
            autoComplete="current-password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </Field>

        {error && <FormAlert>{error}</FormAlert>}

        <button type="submit" disabled={loading} className="hp-btn hp-btn-primary au-submit">
          {loading ? <><span className="hp-spinner au-btn-spinner" aria-hidden="true" />Signing in...</> : <>Sign in <span className="hp-arrow" aria-hidden="true">→</span></>}
        </button>
      </form>

      <p className="au-switch">
        Don&apos;t have an account? <Link to="/register">Create one</Link>
      </p>

      {/* Test account hint */}
      <div className="au-hint">
        Test: student0001@synthetic.example.com / Seagas@2026
      </div>
    </AuthLayout>
  )
}
