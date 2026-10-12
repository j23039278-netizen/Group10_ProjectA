// SEAGAS — Register Page
// Creates a student account via POST /api/auth/register, then signs the new user straight in.
// Only students can sign up here; advisor and admin accounts are created by an admin.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI } from '../api/client'
import AuthLayout, { Field, PasswordInput, FormAlert } from './auth/AuthLayout'

const PASSWORD_MIN = 8
const PASSWORD_CHECKS = [
  { label: `${PASSWORD_MIN}+ characters`, test: p => p.length >= PASSWORD_MIN },
  { label: 'A number',                    test: p => /\d/.test(p) },
  { label: 'An uppercase letter',         test: p => /[A-Z]/.test(p) },
  { label: 'A symbol',                    test: p => /[^A-Za-z0-9]/.test(p) },
]
const STRENGTH = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong']
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function errorMessage(err) {
  if (!err.response) return 'Cannot reach the server. Please make sure the backend is running.'
  const detail = err.response.data?.detail
  if (detail === 'Email already registered') return 'This email is already registered. Try signing in instead.'
  if (Array.isArray(detail)) return 'Please check your details. The email address may be invalid.'
  return typeof detail === 'string' ? detail : 'Registration failed. Please try again.'
}

export default function Register({ onLogin }) {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [touched,  setTouched]  = useState(false)
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const passed = PASSWORD_CHECKS.filter(c => c.test(password)).length
  const passwordTooShort = password.length < PASSWORD_MIN
  const mismatch = confirm.length > 0 && confirm !== password
  const emailInvalid = !EMAIL_RE.test(email.trim())

  const fieldErrors = touched ? {
    fullName: !fullName.trim() ? 'Please enter your full name.' : '',
    email:    emailInvalid ? 'Please enter a valid email address.' : '',
    password: passwordTooShort ? `Password must be at least ${PASSWORD_MIN} characters.` : '',
    confirm:  confirm !== password ? 'Passwords do not match.' : '',
  } : { fullName: '', email: '', password: '', confirm: mismatch ? 'Passwords do not match.' : '' }

  const handleRegister = async (e) => {
    e.preventDefault()
    setTouched(true)
    setError('')
    if (!fullName.trim() || emailInvalid || passwordTooShort || confirm !== password) return

    setLoading(true)
    try {
      await authAPI.register({ email: email.trim(), password, full_name: fullName.trim(), role: 'student' })
    } catch (err) {
      setError(errorMessage(err))
      setLoading(false)
      return
    }

    // Account created: sign in straight away (same steps as the Login page)
    try {
      const res  = await authAPI.login(email.trim(), password)
      const data = res.data
      localStorage.setItem('token',    data.access_token)
      localStorage.setItem('role',     data.role)
      localStorage.setItem('fullName', data.full_name)
      onLogin(data.role)
    } catch {
      navigate('/login', { state: { registeredEmail: email.trim() } })
    }
  }

  return (
    <AuthLayout
      heading={<>Start your <span className="au-accent">journey</span></>}
      title="Create your account"
      subtitle="Student sign-up. Advisor accounts are created by your SEAGAS administrator."
    >

      <form onSubmit={handleRegister} noValidate>
        <Field id="reg-name" label="Full name" icon="profile" error={fieldErrors.fullName}>
          <input
            id="reg-name"
            className="au-input"
            type="text" required
            autoComplete="name"
            placeholder="e.g. Tan Wei Ming"
            value={fullName} onChange={e => setFullName(e.target.value)}
            aria-invalid={!!fieldErrors.fullName || undefined}
          />
        </Field>

        <Field id="reg-email" label="Email" icon="mail" error={fieldErrors.email}>
          <input
            id="reg-email"
            className="au-input"
            type="email" required
            autoComplete="email"
            placeholder="you@student.edu.my"
            value={email} onChange={e => setEmail(e.target.value)}
            aria-invalid={!!fieldErrors.email || undefined}
          />
        </Field>

        <Field id="reg-password" label="Password" icon="lock" error={fieldErrors.password}>
          <PasswordInput
            id="reg-password"
            autoComplete="new-password"
            placeholder={`At least ${PASSWORD_MIN} characters`}
            value={password}
            onChange={e => setPassword(e.target.value)}
            invalid={!!fieldErrors.password}
          />
        </Field>

        {password && (
          <div className="au-strength" aria-live="polite">
            <div className="au-strength-bars" data-score={passed}>
              {PASSWORD_CHECKS.map((_, i) => <span key={i} className={i < passed ? 'is-on' : ''} />)}
            </div>
            <div className="au-strength-label">Strength: <b>{STRENGTH[passed]}</b></div>
            <ul className="au-checks">
              {PASSWORD_CHECKS.map(c => (
                <li key={c.label} className={c.test(password) ? 'is-met' : ''}>{c.label}</li>
              ))}
            </ul>
          </div>
        )}

        <Field id="reg-confirm" label="Confirm password" icon="lock" error={fieldErrors.confirm}>
          <PasswordInput
            id="reg-confirm"
            autoComplete="new-password"
            placeholder="Re-enter your password"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            invalid={!!fieldErrors.confirm}
          />
        </Field>

        {error && <FormAlert>{error}</FormAlert>}

        <button type="submit" disabled={loading} className="hp-btn hp-btn-primary au-submit">
          {loading
            ? <><span className="hp-spinner au-btn-spinner" aria-hidden="true" />Creating account...</>
            : <>Create account <span className="hp-arrow" aria-hidden="true">→</span></>}
        </button>
      </form>

      <p className="au-switch">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </AuthLayout>
  )
}
