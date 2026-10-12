// SEAGAS — Login Pages
// One component, three pages: /login (students), /advisor/login and /admin/login.
// The route decides the role, so users never pick one. The account's real role
// comes from the database, and a page only signs in accounts of its own role.
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { authAPI } from '../api/client'
import AuthLayout, { Field, PasswordInput, FormAlert } from './auth/AuthLayout'

const LOGIN_PAGES = {
  student: {
    path: '/login',
    label: 'Student',
    heading: <>Welcome <span className="au-accent">back</span></>,
    title: 'Student sign in',
    subtitle: 'Use the email and password for your SEAGAS student account.',
    placeholder: 'student@synthetic.example.com',
  },
  advisor: {
    path: '/advisor/login',
    label: 'Advisor',
    heading: <>Advisor <span className="au-accent">portal</span></>,
    title: 'Advisor sign in',
    subtitle: 'Sign in to view your cohort’s readiness and skill gaps.',
    placeholder: 'name@uni.edu.my',
  },
  admin: {
    path: '/admin/login',
    label: 'Admin',
    heading: <>SEAGAS <span className="au-accent">admin</span></>,
    title: 'Admin sign in',
    subtitle: 'Manage advisor and admin accounts and the skills library.',
    placeholder: 'name@uni.edu.my',
  },
}

export default function Login({ role = 'student', onLogin }) {
  const page = LOGIN_PAGES[role]
  const location = useLocation()
  // Register sends people here with their email if the automatic sign-in didn't work
  const registeredEmail = location.state?.registeredEmail || ''

  const [email,     setEmail]     = useState(registeredEmail)
  const [password,  setPassword]  = useState('')
  const [error,     setError]     = useState('')
  const [wrongPage, setWrongPage] = useState(null)
  const [loading,   setLoading]   = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setWrongPage(null)
    setLoading(true)
    try {
      const res  = await authAPI.login(email, password)
      const data = res.data
      if (data.role !== role) {
        // Right password, wrong page: don't sign in here, point to the account's own page
        setWrongPage(LOGIN_PAGES[data.role] || null)
        return
      }
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

  return (
    <AuthLayout heading={page.heading} title={page.title} subtitle={page.subtitle}>
      {registeredEmail && role === 'student' && (
        <FormAlert type="success">Account created. Please sign in to continue.</FormAlert>
      )}

      <form onSubmit={handleLogin}>
        <Field id="login-email" label="Email" icon="mail">
          <input
            id="login-email"
            className="au-input"
            type="email" required
            autoComplete="email"
            placeholder={page.placeholder}
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
        {wrongPage && (
          <FormAlert>
            This is {/^[aeiou]/i.test(wrongPage.label) ? 'an' : 'a'} {wrongPage.label.toLowerCase()} account.
            Please use the <Link to={wrongPage.path}>{wrongPage.label} sign-in page</Link>.
          </FormAlert>
        )}

        <button type="submit" disabled={loading} className="hp-btn hp-btn-primary au-submit">
          {loading ? <><span className="hp-spinner au-btn-spinner" aria-hidden="true" />Signing in...</> : <>Sign in <span className="hp-arrow" aria-hidden="true">→</span></>}
        </button>
      </form>

      {role === 'student' ? (
        <>
          <p className="au-switch">
            Don&apos;t have an account? <Link to="/register">Create one</Link>
          </p>
          <p className="au-switch au-switch-staff">
            Are you an advisor? <Link to={LOGIN_PAGES.advisor.path}>Advisor sign in</Link>
          </p>
          {/* Test account hint (synthetic student data only) */}
          <div className="au-hint">
            Test: student0001@synthetic.example.com / Seagas@2026
          </div>
        </>
      ) : (
        <>
          <p className="au-switch">
            {page.label} accounts are created by your SEAGAS administrator.
          </p>
          <p className="au-switch au-switch-staff">
            <Link to={LOGIN_PAGES.student.path}>Student sign in</Link>
            {role === 'advisor' && <> · <Link to={LOGIN_PAGES.admin.path}>Admin sign in</Link></>}
            {role === 'admin' && <> · <Link to={LOGIN_PAGES.advisor.path}>Advisor sign in</Link></>}
          </p>
        </>
      )}
    </AuthLayout>
  )
}
