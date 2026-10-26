// SEAGAS — Login Page
// One sign-in page for everyone. The backend returns the account's role from the
// database, and App.jsx opens that role's portal: students, advisors and admins
// never choose a role themselves.
// Students also enter their student ID. There is no sign-up: student accounts
// are created by an admin from the advisor's new-student list, and the student
// receives a temporary password by email.
import { useState } from 'react'
import { authAPI } from '../api/client'
import AuthLayout, { Field, PasswordInput, FormAlert } from './auth/AuthLayout'

export default function Login({ onLogin }) {
  const [email,     setEmail]     = useState('')
  const [studentId, setStudentId] = useState('')
  const [password,  setPassword]  = useState('')
  const [error,     setError]     = useState('')
  const [loading,   setLoading]   = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    if (studentId.trim() && !/^\d{9}$/.test(studentId.trim()))
      return setError('A student ID has 9 digits, e.g. 105967029.')
    setLoading(true)
    try {
      const res  = await authAPI.login(email, password, studentId)
      localStorage.setItem('token', res.data.access_token)
      onLogin(res.data)
    } catch (err) {
      setError(!err.response
        ? 'Cannot reach the server. Please make sure the backend is running.'
        : err.response.status === 403
          ? 'This account is disabled. Please contact your advisor.'
          : 'Incorrect email, student ID or password. Please try again.')
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      heading={<>Welcome <span className="au-accent">back</span></>}
      title="Sign in"
      subtitle="Students: use your school email, student ID and password. Advisors and admins: leave Student ID empty."
    >
      <form onSubmit={handleLogin}>
        <Field id="login-email" label="Email" icon="mail">
          <input
            id="login-email"
            className="au-input"
            type="email" required
            autoComplete="email"
            placeholder="105967029@student.newinti.edu.my"
            value={email} onChange={e => setEmail(e.target.value)}
          />
        </Field>

        <Field id="login-student-id" label="Student ID (students only)" icon="student">
          <input
            id="login-student-id"
            className="au-input"
            type="text" inputMode="numeric" maxLength={9}
            autoComplete="username"
            placeholder="9 digits, e.g. 105967029"
            value={studentId} onChange={e => setStudentId(e.target.value.replace(/\D/g, ''))}
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
        New student? Your advisor registers you. Your student ID, school email and a temporary
        password are sent to your personal email.
      </p>

      {/* Test account hint (synthetic student data only) */}
      <div className="au-hint">
        Test: student0001@synthetic.example.com / 900000001 / Seagas@2026
      </div>
    </AuthLayout>
  )
}
