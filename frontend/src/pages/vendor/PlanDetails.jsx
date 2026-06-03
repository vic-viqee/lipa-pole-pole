import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getPlan, recordPayment, getPaymentsForPlan } from '../../services/paymentService'
import { Button, Input, Badge, Progress, Card } from '../../components/ui'
import Layout from '../../components/Layout'
import '../../styles/pages.css'

const ArrowLeftIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12"/>
    <polyline points="12 19 5 12 12 5"/>
  </svg>
)

const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
)

const WhatsAppIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const PartyIcon = () => (
  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5.8 11.3 2 22l10.7-3.79"/>
    <path d="M4 3h.01"/>
    <path d="M22 8h.01"/>
    <path d="M15 2h.01"/>
    <path d="M22 20h.01"/>
    <path d="m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"/>
    <path d="m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11v0c-.11.7-.72 1.22-1.43 1.22H17"/>
    <path d="m11 2 .33.82c.34.86-.2 1.82-1.11 1.98v0C9.52 4.9 9 5.52 9 6.23V7"/>
    <path d="M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2Z"/>
  </svg>
)

export default function PlanDetails() {
  const { planId } = useParams()
  const [plan, setPlan] = useState(null)
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [payAmount, setPayAmount] = useState('')
  const [paying, setPaying] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [copied, setCopied] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)

  const fetchAll = async () => {
    try {
      const [planRes, paymentsRes] = await Promise.all([
        getPlan(planId),
        getPaymentsForPlan(planId)
      ])
      const newPlan = planRes.data
      if (plan && plan.status === 'active' && newPlan.status === 'completed') {
        setShowConfetti(true)
        setTimeout(() => setShowConfetti(false), 5000)
      }
      setPlan(newPlan)
      setPayments(paymentsRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [planId])

  const handlePayment = async (e) => {
    e.preventDefault()
    setPaying(true)
    setError('')
    setSuccess('')
    try {
      await recordPayment({ amount: parseFloat(payAmount), plan_id: parseInt(planId) })
      setSuccess(`Payment of KSh ${Number(payAmount).toLocaleString()} recorded successfully!`)
      setPayAmount('')
      fetchAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Payment failed')
    } finally {
      setPaying(false)
    }
  }

  const handleCopyLink = () => {
    const url = `${window.location.origin}/track/${plan.tracking_token}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE')}`
  const fmtDate = (d) => new Date(d).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })

  if (loading) return (
    <Layout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div className="skeleton" style={{ width: '200px', height: '24px' }} />
      </div>
    </Layout>
  )

  if (!plan) return (
    <Layout>
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <p>Plan not found.</p>
        <Link to="/" style={{ color: 'var(--color-primary)', marginTop: '16px', display: 'inline-block' }}>Back to Dashboard</Link>
      </div>
    </Layout>
  )

  const paid = plan.deposit_paid + plan.amount_paid
  const pct = Math.min(Math.round((paid / plan.total_price) * 100), 100)

  const getStatusBadge = (status) => {
    const variants = { active: 'warning', completed: 'success', defaulted: 'error' }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  return (
    <Layout>
      {showConfetti && (
        <div className="confetti-container">
          {[...Array(20)].map((_, i) => (
            <div key={i} className={`confetti piece-${i % 5}`} style={{ left: `${Math.random() * 100}%`, animationDelay: `${Math.random() * 3}s` }} />
          ))}
        </div>
      )}
      <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--text-tertiary)', textDecoration: 'none', marginBottom: '32px', fontSize: '14px' }}>
        <ArrowLeftIcon />
        Back to Dashboard
      </Link>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px', alignItems: 'start' }} className="plan-grid">
        <div className="animate-slideUp" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Card padding="lg">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 800, marginBottom: '4px' }}>{plan.product_name}</h1>
                <p style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Customer #{plan.customer_id} · Plan #{plan.id}</p>
              </div>
              {getStatusBadge(plan.status)}
            </div>

            <Progress value={pct} variant="gradient" showLabel label={`${pct}% complete`} size="lg" />

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '24px' }}>
              <div style={{ background: 'var(--surface-overlay)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '8px' }}>Total Price</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>{fmt(plan.total_price)}</div>
              </div>
              <div style={{ background: 'var(--surface-overlay)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '8px' }}>Total Paid</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, color: 'var(--color-primary)' }}>{fmt(paid)}</div>
              </div>
              <div style={{ background: 'var(--surface-overlay)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '8px' }}>Balance</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, color: 'oklch(70% 0.14 85)' }}>{fmt(plan.balance)}</div>
              </div>
            </div>
          </Card>

          <Card padding="lg">
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '16px' }}>Customer Tracking Link</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', marginBottom: '12px' }}>Share this link with your customer so they can track their balance and pay via M-Pesa</p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
              <input
                readOnly
                value={`${window.location.origin}/track/${plan.tracking_token}`}
                style={{
                  flex: 1,
                  background: 'var(--surface-overlay)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  color: 'var(--text-tertiary)',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                  outline: 'none'
                }}
              />
              <Button variant="secondary" size="sm" onClick={handleCopyLink}>
                {copied ? <CheckIcon /> : <CopyIcon />}
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
            <Button
              variant="primary"
              size="sm"
              fullWidth
              onClick={() => {
                const url = `${window.location.origin}/track/${plan.tracking_token}`
                const ogUrl = `${window.location.origin}/og/track/${plan.tracking_token}`
                const msg = encodeURIComponent(`Hi! Track your installment plan for ${plan.product_name} and pay via M-Pesa here: ${ogUrl}`)
                window.open(`https://wa.me/?text=${msg}`, '_blank')
              }}
              style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <WhatsAppIcon />
              Share via WhatsApp
            </Button>
          </Card>

          <Card padding="lg">
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '16px' }}>Payment History ({payments.length + 1})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--color-primary-subtle)', border: '1px solid var(--color-primary-border)', borderRadius: 'var(--radius-md)', padding: '14px 18px' }}>
                <div>
                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Initial Deposit</div>
                  <div style={{ fontSize: '10px', color: 'var(--color-primary)', fontWeight: 600, marginTop: '2px' }}>Day 1</div>
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)' }}>{fmt(plan.deposit_paid)}</div>
              </div>
              {payments.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '13px', background: 'var(--surface-overlay)', borderRadius: 'var(--radius-md)' }}>
                  No additional payments yet
                </div>
              ) : (
                payments.map(p => (
                  <div key={p.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--surface-overlay)', borderRadius: 'var(--radius-md)', padding: '14px 18px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-primary)', flexShrink: 0 }} />
                      <div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{fmtDate(p.created_at)}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Payment #{p.id}</div>
                      </div>
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)' }}>{fmt(p.amount)}</div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="animate-slideUp" style={{ animationDelay: '100ms' }}>
          <Card padding="lg" className="plan-sticky">
            {plan.status === 'completed' ? (
              <div style={{ textAlign: 'center', padding: '24px' }}>
                <div style={{ color: 'var(--color-primary)', marginBottom: '12px' }}><PartyIcon /></div>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, color: 'var(--color-primary)', marginBottom: '8px' }}>Fully Paid!</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>This customer has completed all payments and can collect their item.</p>
              </div>
            ) : (
              <>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>Record Payment</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', marginBottom: '20px' }}>Enter amount paid by customer</p>

                <div style={{ background: 'var(--color-primary-subtle)', border: '1px solid var(--color-primary-border)', borderRadius: 'var(--radius-md)', padding: '20px', textAlign: 'center', marginBottom: '20px' }}>
                  <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: '8px' }}>Outstanding Balance</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '32px', fontWeight: 800, color: 'var(--color-primary)' }}>{fmt(plan.balance)}</div>
                </div>

                {success && (
                  <div style={{ background: 'var(--color-primary-subtle)', border: '1px solid var(--color-primary-border)', color: 'var(--color-primary)', padding: '12px 16px', borderRadius: 'var(--radius-md)', fontSize: '13px', marginBottom: '16px' }}>
                    {success}
                  </div>
                )}

                {error && (
                  <div style={{ background: 'oklch(92% 0.04 25)', border: '1px solid oklch(85% 0.04 25)', color: 'oklch(55% 0.15 25)', padding: '12px 16px', borderRadius: 'var(--radius-md)', fontSize: '13px', marginBottom: '16px' }}>
                    {error}
                  </div>
                )}

                <form onSubmit={handlePayment} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <Input
                    label="Amount (KSh)"
                    type="number"
                    required
                    min="1"
                    max={plan.balance}
                    value={payAmount}
                    onChange={e => setPayAmount(e.target.value)}
                    placeholder={`Max ${fmt(plan.balance)}`}
                  />
                  <Button type="submit" loading={paying} fullWidth>
                    Record Payment
                  </Button>
                </form>
              </>
            )}
          </Card>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .plan-grid { grid-template-columns: 1fr !important; }
          .plan-sticky { position: static !important; }
        }

        .confetti-container {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 1000;
          overflow: hidden;
        }

        .confetti {
          position: absolute;
          width: 10px;
          height: 20px;
          top: -20px;
          opacity: 0.8;
          animation: fall linear infinite;
        }

        .piece-0 { background: var(--color-primary); width: 8px; height: 16px; }
        .piece-1 { background: var(--color-accent); width: 12px; height: 12px; border-radius: 50%; }
        .piece-2 { background: var(--color-info); width: 10px; height: 10px; transform: rotate(45deg); }
        .piece-3 { background: var(--color-success); width: 6px; height: 20px; }
        .piece-4 { background: var(--color-warning); width: 14px; height: 14px; }

        @keyframes fall {
          0% { transform: translateY(0) rotate(0); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }

        .confetti:nth-child(odd) { animation-duration: 3s; }
        .confetti:nth-child(even) { animation-duration: 4s; }
      `}</style>
    </Layout>
  )
}
