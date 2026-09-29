// SEAGAS — shared layout for the Login and Register pages (styled to match the Home page).
// One centred column: logo, a short heading, then the form card.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import LogoMark from '../home/LogoMark'
import Icon from '../home/Icon'
import { useCanvasColor } from '../home/hooks'
import '../Home.css'
import './Auth.css'

export default function AuthLayout({ heading, title, subtitle, children }) {
  useCanvasColor('#071D33')
  return (
    <div className="hp au">
      <div className="au-bg" aria-hidden="true">
        <div className="hp-grid" />
        <div className="au-glow au-glow-teal" />
        <div className="au-glow au-glow-blue" />
      </div>

      <Link to="/" className="au-back">
        <Icon name="back" size={16} /> Back to home
      </Link>

      <main className="au-center">
        <Link to="/" className="au-logo hp-enter" aria-label="SEAGAS home">
          <LogoMark dark className="au-logo-mark" />
          <span className="hp-logo-text">
            <span className="hp-logo-name">SEAGAS</span>
            <span className="hp-logo-tag">FROM CAMPUS TO CAREER</span>
          </span>
        </Link>

        <h1 className="au-heading hp-enter" style={{ '--d': '100ms' }}>{heading}</h1>

        <div className="au-card hp-enter" style={{ '--d': '200ms' }}>
          <h2 className="au-title">{title}</h2>
          <p className="au-subtitle">{subtitle}</p>
          {children}
        </div>

        <div className="au-foot">© 2026 SEAGAS · Group 10</div>
      </main>
    </div>
  )
}

// ---------- Form building blocks ----------

export function Field({ id, label, icon, error, hint, children }) {
  return (
    <div className={`au-field ${error ? 'has-error' : ''}`}>
      <label htmlFor={id} className="au-label">{label}</label>
      <div className="au-input-wrap">
        {icon && <span className="au-input-icon"><Icon name={icon} size={17} /></span>}
        {children}
      </div>
      {error
        ? <div className="au-field-error" id={`${id}-error`}>{error}</div>
        : hint && <div className="au-field-hint">{hint}</div>}
    </div>
  )
}

export function PasswordInput({ id, value, onChange, placeholder = '••••••••', autoComplete, invalid }) {
  const [show, setShow] = useState(false)
  return (
    <>
      <input
        id={id}
        className="au-input has-toggle"
        type={show ? 'text' : 'password'}
        required
        placeholder={placeholder}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        aria-invalid={invalid || undefined}
        aria-describedby={invalid ? `${id}-error` : undefined}
      />
      <button
        type="button"
        className="au-eye"
        onClick={() => setShow(s => !s)}
        aria-label={show ? 'Hide password' : 'Show password'}
      >
        <Icon name={show ? 'eyeOff' : 'eye'} size={17} />
      </button>
    </>
  )
}

export function FormAlert({ type = 'error', children }) {
  return (
    <div className={`au-alert au-alert-${type}`} role={type === 'error' ? 'alert' : 'status'}>
      <Icon name={type === 'error' ? 'alert' : 'check'} size={17} />
      <span>{children}</span>
    </div>
  )
}
