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

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ shop_name: '', email: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await register(form.shop_name, form.email, form.phone, form.password)
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    { title: 'Register', desc: 'Create your vendor account' },
    { title: 'Add customers', desc: 'Start tracking installments' },
    { title: 'Get paid', desc: 'Accept M-Pesa payments' },
  ]

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
            Your shop.<br />
            <span className="text-accent">Your terms.</span>
          </h1>
          <p className="auth-hero-description">
            Join vendors across Kenya who are growing their business by offering 
            flexible payment plans — all tracked digitally, all on M-Pesa.
          </p>

          <div className="auth-steps">
            {steps.map((step, i) => (
              <div key={i} className="auth-step">
                <div className="auth-step-number">
                  <CheckIcon />
                </div>
                <div className="auth-step-content">
                  <span className="auth-step-title">{step.title}</span>
                  <span className="auth-step-desc">{step.desc}</span>
                </div>
              </div>
            ))}
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
            <h2 className="auth-form-title">Create your account</h2>
            <p className="auth-form-subtitle">Start tracking installments for free</p>
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
              label="Shop Name"
              type="text"
              required
              value={form.shop_name}
              onChange={(e) => setForm({ ...form, shop_name: e.target.value })}
              placeholder="e.g. Kamau Electronics"
            />
            <Input
              label="Email address"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
            />
            <Input
              label="Phone Number"
              type="tel"
              required
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="0712 345 678"
              hint="Kenyan mobile number for M-Pesa"
            />
            <Input
              label="Password"
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Create a secure password"
            />
            <Button type="submit" loading={loading} fullWidth>
              Create Account
              <ArrowRight />
            </Button>
          </form>

          <p className="auth-form-footer">
            Already have an account? <Link to="/login" className="auth-link">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
