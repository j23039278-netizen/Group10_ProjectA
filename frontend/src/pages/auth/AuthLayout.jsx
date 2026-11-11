// SEAGAS — shared layout for the Login and Change Password pages (styled to match the Home page).
// One centred column: logo, a short heading, then the form card.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BrandLogo } from '../home/BrandLogo'
import Icon from '../home/Icon'
import { useCanvasColor } from '../home/hooks'
import campusMain from '../../assets/campus/inti-campus-main.jpg'
import campusSubang from '../../assets/campus/inti-campus-subang.jpg'
import '../Home.css'
import './Auth.css'

export default function AuthLayout({ heading, title, subtitle, children }) {
  useCanvasColor('#ffffff')
  return (
    <div className="hp au">
      {/* Background: INTI campus photos left and right, red / pink blocks in between; the form sits on top */}
      <div className="au-bg" aria-hidden="true">
        <div className="au-mosaic">
          <div className="au-tile au-t-main" style={{ backgroundImage: `url(${campusMain})` }} />
          <div className="au-tile au-t-pink1" />
          <div className="au-tile au-t-red1" />
          <div className="au-tile au-t-pink2" />
          <div className="au-tile au-t-subang" style={{ backgroundImage: `url(${campusSubang})` }} />
        </div>
      </div>

      <Link to="/" className="au-back">
        <Icon name="back" size={16} /> Back to home
      </Link>

      {/* One white panel: logo, heading and form, so they read clearly over the photos */}
      <main className="au-center">
        <div className="au-card hp-enter" style={{ '--d': '100ms' }}>
          <div className="au-card-head">
            <Link to="/" className="au-logo" aria-label="SEAGAS home">
              <BrandLogo className="au-logo-img" />
            </Link>
            <h1 className="au-heading">{heading}</h1>
          </div>
          <h2 className="au-title">{title}</h2>
          <p className="au-subtitle">{subtitle}</p>
          {children}
          <div className="au-foot">© 2026 SEAGAS · Group 10</div>
        </div>
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
