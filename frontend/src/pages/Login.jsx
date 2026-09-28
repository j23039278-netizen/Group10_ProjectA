// SEAGAS — Login Page
import { useState } from 'react'
import { authAPI } from '../api/client'

export default function Login({ onLogin }) {
  const [role,     setRole]     = useState('student')
  const [email,    setEmail]    = useState('')
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
      setError('Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const roles = [
    { id: 'student', label: '🎓 Student' },
    { id: 'advisor', label: '👨‍🏫 Advisor' },
    { id: 'admin',   label: '⚙️ Admin' },
  ]

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a1f2e 0%, #2d3755 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#fff', borderRadius: '16px',
        padding: '48px 40px', width: '400px',
        boxShadow: '0 24px 64px rgba(0,0,0,0.3)'
      }}>
        {/* Logo */}
        <div style={{ fontSize: '28px', fontWeight: '700', color: '#2d5be3', marginBottom: '4px' }}>
          SEAGAS
        </div>
        <div style={{ fontSize: '12px', color: '#8b92a8', marginBottom: '32px' }}>
          Student Employability Assessment & Gap Analysis System
        </div>

        {/* Role Selector */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          {roles.map(r => (
            <button key={r.id} onClick={() => setRole(r.id)} style={{
              flex: 1, padding: '10px 6px',
              border: `2px solid ${role === r.id ? '#2d5be3' : '#e4e6ef'}`,
              borderRadius: '8px', cursor: 'pointer', fontSize: '12px',
              fontWeight: '500',
              background: role === r.id ? '#eef2fd' : '#f5f6fa',
              color: role === r.id ? '#2d5be3' : '#4a5168',
            }}>
              {r.label}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#4a5168', marginBottom: '6px' }}>
              Email
            </label>
            <input
              type="email" required
              placeholder={role === 'student' ? 'student@synthetic.example.com' : 'advisor@uni.edu.my'}
              value={email} onChange={e => setEmail(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: '1.5px solid #e4e6ef',
                borderRadius: '8px', fontSize: '14px', outline: 'none',
                background: '#f5f6fa', boxSizing: 'border-box'
              }}
            />
          </div>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#4a5168', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password" required
              placeholder="••••••••"
              value={password} onChange={e => setPassword(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', border: '1.5px solid #e4e6ef',
                borderRadius: '8px', fontSize: '14px', outline: 'none',
                background: '#f5f6fa', boxSizing: 'border-box'
              }}
            />
          </div>

          {error && (
            <div style={{
              background: '#fee2e2', color: '#dc2626', padding: '10px 14px',
              borderRadius: '8px', fontSize: '13px', marginBottom: '14px'
            }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            width: '100%', padding: '12px',
            background: loading ? '#93a8f0' : '#2d5be3',
            color: '#fff', border: 'none', borderRadius: '8px',
            fontSize: '14px', fontWeight: '600', cursor: 'pointer'
          }}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Test account hint */}
        <div style={{ marginTop: '16px', fontSize: '11px', color: '#8b92a8', textAlign: 'center' }}>
          Test: student0001@synthetic.example.com / Seagas@2026
        </div>
      </div>
    </div>
  )
}