import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Button, Input } from '../../components/ui'
import './Auth.css'

const LogoIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v12M8 10h8M8 14h8"/>
  </svg>
)

const ArrowRight = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"/>
    <polyline points="12 5 19 12 12 19"/>
  </svg>
)

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form.email, form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-panel auth-panel-left">
        <div className="auth-brand animate-slideIn">
          <div className="auth-brand-logo">
            <LogoIcon />
          </div>
          <span className="auth-brand-name">Lipa Polepole</span>
        </div>

        <div className="auth-hero stagger-children">
          <h1 className="auth-hero-title">
            Every shilling, <span className="text-accent">tracked.</span>
          </h1>
          <p className="auth-hero-description">
            Stop juggling notebooks and WhatsApp messages. Track your installment plans, 
            accept M-Pesa payments, and give your customers transparency they trust.
          </p>

          <div className="auth-stats">
            <div className="auth-stat">
              <span className="auth-stat-value">100%</span>
              <span className="auth-stat-label">Transparent</span>
            </div>
            <div className="auth-stat">
              <span className="auth-stat-value">M-Pesa</span>
              <span className="auth-stat-label">Integrated</span>
            </div>
            <div className="auth-stat">
              <span className="auth-stat-value">Free</span>
              <span className="auth-stat-label">To start</span>
            </div>
          </div>
        </div>

        <div className="auth-decoration">
          <div className="auth-circle auth-circle-1" />
          <div className="auth-circle auth-circle-2" />
          <div className="auth-grid" />
        </div>
      </div>

      <div className="auth-panel auth-panel-right">
        <div className="auth-form-wrapper animate-fadeIn">
          <div className="auth-form-header">
            <h2 className="auth-form-title">Welcome back</h2>
            <p className="auth-form-subtitle">Sign in to your vendor dashboard</p>
          </div>

          {error && (
            <div className="auth-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            <Input
              label="Email address"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Enter your password"
            />
            <Button type="submit" loading={loading} fullWidth>
              Sign In
              <ArrowRight />
            </Button>
          </form>

          <p className="auth-form-footer">
            New vendor? <Link to="/register" className="auth-link">Create your shop</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
