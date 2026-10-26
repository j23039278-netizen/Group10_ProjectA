// SEAGAS — Choose a new password
// Shown instead of the portal while the account still has a temporary password
// (a new student's first sign-in, or after an admin reset). The backend refuses
// every other request until the password is changed. The temporary password is
// not asked again: the user has just signed in with it.
import { useState } from 'react'
import { authAPI } from '../api/client'
import { PASSWORD_RULES, passwordProblem } from '../utils/passwordRules'
import AuthLayout, { Field, PasswordInput, FormAlert } from './auth/AuthLayout'

export default function ChangePassword({ user, onDone, onLogout }) {
  const [next,    setNext]    = useState('')
  const [confirm, setConfirm] = useState('')
  const [error,   setError]   = useState('')
  const [saving,  setSaving]  = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    const problem = passwordProblem(next)
    if (problem) return setError(problem)
    if (next !== confirm) return setError('The two passwords do not match.')
    setSaving(true)
    try {
      await authAPI.changePassword('', next)
      onDone()
    } catch (err) {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : 'Could not change the password. Please try again.')
      setSaving(false)
    }
  }

  return (
    <AuthLayout
      heading={<>Welcome, <span className="au-accent">{user.full_name.split(' ')[0]}</span></>}
      title="Choose your password"
      subtitle="You signed in with a temporary password. Choose your own password to continue."
    >
      <form onSubmit={submit}>
        <Field id="cp-new" label="New password" icon="lock">
          <PasswordInput id="cp-new" autoComplete="new-password" value={next} onChange={e => setNext(e.target.value)} />
        </Field>

        {/* Live checklist of the password rules */}
        <ul aria-label="Password rules" style={{ listStyle: 'none', padding: 0, margin: '-4px 0 16px', fontSize: '13px' }}>
          {PASSWORD_RULES.map(r => {
            const ok = r.test(next)
            return (
              <li key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '3px 0',
                                      color: ok ? '#2dd4bf' : 'rgba(255,255,255,0.55)' }}>
                <span aria-hidden="true" style={{ width: '14px', textAlign: 'center' }}>{ok ? '✓' : '○'}</span>
                {r.text}<span className="sr-only">{ok ? ' (done)' : ' (missing)'}</span>
              </li>
            )
          })}
        </ul>

        <Field id="cp-confirm" label="Confirm new password" icon="lock"
          error={confirm && confirm !== next ? 'The two passwords do not match.' : undefined}>
          <PasswordInput id="cp-confirm" autoComplete="new-password" value={confirm} onChange={e => setConfirm(e.target.value)}
            invalid={!!confirm && confirm !== next} />
        </Field>

        {error && <FormAlert>{error}</FormAlert>}

        <button type="submit" disabled={saving} className="hp-btn hp-btn-primary au-submit">
          {saving ? 'Saving...' : <>Save and continue <span className="hp-arrow" aria-hidden="true">→</span></>}
        </button>
      </form>
      <p className="au-switch">
        Not you? <a href="/" onClick={e => { e.preventDefault(); onLogout() }}>Sign out</a>
      </p>
    </AuthLayout>
  )
}
