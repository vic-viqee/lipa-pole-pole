import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { trackPlan, getPaymentsPublic, initiateMpesaPayment } from '../../services/paymentService'
import { Button } from '../../components/ui'
import './BalanceView.css'

const StoreIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
    <path d="M3 6h18"/>
    <path d="M16 10a4 4 0 0 1-8 0"/>
  </svg>
)

const PartyIcon = () => (
  <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
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

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

const MpesaIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="3"/>
    <path d="M12 8v8"/>
    <path d="M8 12h8"/>
  </svg>
)

const PhoneIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
)

function generateConfetti() {
  return Array.from({ length: 24 }, (_, i) => ({
    id: i,
    style: {
      left: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 2.5}s`,
      animationDuration: `${2.5 + Math.random() * 2}s`,
    },
    pieceClass: `bv-confetti-piece bv-cp-${i % 5}`,
  }))
}

export default function BalanceView() {
  const { trackingToken } = useParams()
  const [plan, setPlan] = useState(null)
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [payPhone, setPayPhone] = useState('')
  const [payAmount, setPayAmount] = useState('')
  const [paying, setPaying] = useState(false)
  const [payError, setPayError] = useState('')
  const [paySuccess, setPaySuccess] = useState('')
  const [polling, setPolling] = useState(false)
  const [pollTicksLeft, setPollTicksLeft] = useState(0)
  const [showConfetti, setShowConfetti] = useState(false)
  const [confettiPieces] = useState(generateConfetti)

  const refreshPublicData = useCallback(async () => {
    const [planRes, paymentsRes] = await Promise.all([
      trackPlan(trackingToken),
      getPaymentsPublic(trackingToken),
    ])
    const newPlan = planRes.data
    if (plan && plan.status === 'active' && newPlan.status === 'completed') {
      setShowConfetti(true)
      setTimeout(() => setShowConfetti(false), 6000)
    }
    setPlan(newPlan)
    setPayments(paymentsRes.data)
    return newPlan
  }, [trackingToken, plan])

  useEffect(() => {
    async function fetchPlan() {
      try {
        await refreshPublicData()
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    fetchPlan()
  }, [refreshPublicData])

  useEffect(() => {
    if (!polling || pollTicksLeft <= 0) return
    const id = setInterval(async () => {
      try {
        const latest = await refreshPublicData()
        setPollTicksLeft((ticks) => ticks - 1)
        if (latest.status === 'completed') setPolling(false)
      } catch {
        setPollTicksLeft((ticks) => ticks - 1)
      }
    }, 10000)
    return () => clearInterval(id)
  }, [polling, pollTicksLeft, refreshPublicData])

  useEffect(() => {
    if (pollTicksLeft <= 0) setPolling(false)
  }, [pollTicksLeft])

  const handlePay = async (e) => {
    e.preventDefault()
    setPayError('')
    setPaySuccess('')

    const amount = Number(payAmount)
    const phone = payPhone.replace(/\D/g, '')
    if (!phone) {
      setPayError('Enter your M-Pesa phone number')
      return
    }
    if (!/^254[17]\d{8}$/.test(phone)) {
      setPayError('Phone must start with 254 (e.g. 254712345678 or 254112345678)')
      return
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setPayError('Enter a valid amount')
      return
    }
    if (amount > Number(plan.balance)) {
      setPayError('This is more than your remaining balance')
      return
    }

    try {
      setPaying(true)
      await initiateMpesaPayment(trackingToken, phone, Math.floor(amount))
      setPaySuccess('M-Pesa STK push sent! Check your phone and enter your PIN to complete payment.')
      setPayAmount('')
      await refreshPublicData()
      setPolling(true)
      setPollTicksLeft(9)
    } catch (err) {
      setPayError(err.response?.data?.detail || 'Failed to initiate payment. Please try again.')
    } finally {
      setPaying(false)
    }
  }

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE')}`
  const fmtDate = (d) => new Date(d).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })
  const fmtTime = (d) => new Date(d).toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' })

  if (loading) {
    return (
      <div className="bv-page">
        <Helmet>
          <title>Loading... - Lipa Polepole</title>
        </Helmet>
        <div className="bv-header">
          <div className="bv-skeleton-title" />
        </div>
        <div className="bv-content">
          <div className="bv-card">
            <div className="skeleton" style={{ height: '120px', marginBottom: '20px' }} />
            <div className="skeleton skeleton-text" style={{ width: '45%', marginBottom: '8px' }} />
            <div className="skeleton" style={{ height: '10px', borderRadius: '5px', marginBottom: '24px' }} />
            <div className="skeleton" style={{ height: '48px', borderRadius: '10px' }} />
          </div>
        </div>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="bv-page">
        <Helmet>
          <title>Plan Not Found - Lipa Polepole</title>
        </Helmet>
        <div className="bv-header">
          <div className="bv-brand">
            <div className="bv-logo"><StoreIcon /></div>
            <span className="bv-brand-name">Lipa Polepole</span>
          </div>
        </div>
        <div className="bv-content">
          <div className="bv-card bv-card-error">
            <div className="bv-not-found-icon">!</div>
            <h2 className="bv-error-title">Plan Not Found</h2>
            <p className="bv-error-desc">This tracking link is invalid or expired. Please contact the shop you purchased from.</p>
          </div>
        </div>
      </div>
    )
  }

  const paid = plan.deposit_paid + plan.amount_paid
  const pct = Math.min(Math.round((paid / plan.total_price) * 100), 100)
  const isComplete = plan.status === 'completed'
  const vendorName = plan.vendor_name || 'Vendor'
  const customerName = plan.customer_name || 'Customer'

  return (
    <div className="bv-page">
      <Helmet>
        <title>{`${plan.product_name} - ${vendorName}`}</title>
        <meta property="og:title" content={`Payment Plan - ${vendorName}`} />
        <meta property="og:description" content={`${customerName} · ${plan.product_name} · ${fmt(plan.balance)} remaining (${pct}% paid) · Pay via M-Pesa`} />
      </Helmet>

      {showConfetti && (
        <div className="bv-confetti-overlay">
          {confettiPieces.map((p) => (
            <div key={p.id} className={p.pieceClass} style={p.style} />
          ))}
        </div>
      )}

      <div className="bv-header">
        <div className="bv-brand">
          <div className="bv-logo"><StoreIcon /></div>
          <span className="bv-brand-name">{vendorName}</span>
        </div>
        <div className="bv-greeting">
          <p className="bv-greeting-label">Hi{', '}{customerName.split(' ')[0]}</p>
          <p className="bv-greeting-sub">Your installment plan for <strong>{plan.product_name}</strong></p>
        </div>
      </div>

      <div className="bv-content">
        {isComplete ? (
          <div className="bv-card bv-card-success animate-slideUp">
            <div className="bv-complete-icon"><PartyIcon /></div>
            <h2 className="bv-complete-title">Fully Paid!</h2>
            <p className="bv-complete-sub">You have completed all payments. Collect your item from <strong>{vendorName}</strong>.</p>
            <div className="bv-amounts-row">
              <div className="bv-amount-box">
                <div className="bv-amount-label">Total Paid</div>
                <div className="bv-amount-value bv-success">{fmt(paid)}</div>
              </div>
              <div className="bv-amount-box">
                <div className="bv-amount-label">Item</div>
                <div className="bv-amount-value" style={{ fontSize: '13px' }}>{plan.product_name}</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bv-card animate-slideUp">
            <div className="bv-balance-display">
              <div className="bv-balance-label">Remaining Balance</div>
              <div className="bv-balance-amount">{fmt(plan.balance)}</div>
              <div className="bv-balance-sub">of {fmt(plan.total_price)} total</div>
            </div>

            <div className="bv-progress-section">
              <div className="bv-progress-top">
                <span>Payment progress</span>
                <strong className="bv-success">{pct}% paid</strong>
              </div>
              <div className="bv-progress-bar">
                <div className="bv-progress-fill" style={{ width: `${pct}%` }} />
              </div>
            </div>

            <div className="bv-amounts-row">
              <div className="bv-amount-box">
                <div className="bv-amount-label">Total Price</div>
                <div className="bv-amount-value">{fmt(plan.total_price)}</div>
              </div>
              <div className="bv-amount-box">
                <div className="bv-amount-label">Amount Paid</div>
                <div className="bv-amount-value bv-success">{fmt(paid)}</div>
              </div>
            </div>
          </div>
        )}

        {!isComplete && (
          <div className="bv-card animate-slideUp" style={{ animationDelay: '100ms' }}>
            <h3 className="bv-card-title">
              <MpesaIcon />
              Pay via M-Pesa
            </h3>
            <form className="bv-pay-form" onSubmit={handlePay}>
              <div className="bv-input-group">
                <div className="bv-input-icon"><PhoneIcon /></div>
                <input
                  className="bv-input bv-input-with-icon"
                  type="tel"
                  placeholder="M-Pesa phone number"
                  value={payPhone}
                  onChange={(e) => setPayPhone(e.target.value.replace(/\D/g, ''))}
                  autoComplete="tel"
                  required
                />
              </div>
              <div className="bv-input-hint">Kenyan number starting with 254 (e.g. 254712345678)</div>

              <div className="bv-input-group">
                <div className="bv-input-icon">KSh</div>
                <input
                  className="bv-input bv-input-with-icon"
                  type="number"
                  min="1"
                  step="1"
                  max={Math.floor(Number(plan.balance))}
                  placeholder={`Amount to pay`}
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                  autoComplete="off"
                  required
                />
              </div>

              <div className="bv-quick-row">
                <span className="bv-quick-label">Quick amounts:</span>
                {[100, 500, 1000].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className="bv-quick-btn"
                    onClick={() => setPayAmount(String(Math.min(value, Math.floor(Number(plan.balance)))))}
                  >
                    KSh {value}
                  </button>
                ))}
                <button
                  type="button"
                  className="bv-quick-btn bv-quick-btn-max"
                  onClick={() => setPayAmount(String(Math.floor(Number(plan.balance))))}
                >
                  Full Balance
                </button>
              </div>

              <Button type="submit" loading={paying} fullWidth>
                {paying ? 'Sending STK Push...' : 'Pay Now'}
              </Button>

              <p className="bv-hint">You'll receive an M-Pesa prompt on your phone. Enter your PIN to complete the payment.</p>

              {payError && (
                <div className="bv-msg bv-msg-error">
                  <span>!</span>
                  <span>{payError}</span>
                </div>
              )}
              {paySuccess && (
                <div className="bv-msg bv-msg-success">
                  <CheckIcon />
                  <div>
                    <strong>{paySuccess.split('.')[0]}.</strong>
                    <span>{paySuccess.split('.').slice(1).join('.')}</span>
                    {polling && <span className="bv-polling-indicator"> Refreshing payment status{' '}{'·'.repeat(pollTicksLeft % 3 + 1)}</span>}
                  </div>
                </div>
              )}
            </form>
          </div>
        )}

        <div className="bv-card animate-slideUp" style={{ animationDelay: '200ms' }}>
          <h3 className="bv-card-title">Payment History</h3>
          <div className="bv-timeline">
            <div className="bv-timeline-item bv-timeline-deposit">
              <div className="bv-timeline-marker">
                <div className="bv-timeline-dot" />
                <div className="bv-timeline-line" />
              </div>
              <div className="bv-timeline-body">
                <div className="bv-timeline-top">
                  <span className="bv-timeline-label">Initial Deposit</span>
                  <span className="bv-timeline-tag">Day 1</span>
                </div>
                <div className="bv-timeline-amount">{fmt(plan.deposit_paid)}</div>
              </div>
            </div>

            {payments.length === 0 ? (
              <div className="bv-timeline-item">
                <div className="bv-timeline-marker">
                  <div className="bv-timeline-dot bv-timeline-dot-empty" />
                </div>
                <div className="bv-timeline-body">
                  <div className="bv-timeline-empty">No payments yet — make your first payment above</div>
                </div>
              </div>
            ) : (
              payments.map((p, i) => {
                const runningTotal = plan.deposit_paid + payments.slice(0, i + 1).reduce((s, x) => s + Number(x.amount), 0)
                return (
                  <div key={p.id} className="bv-timeline-item">
                    <div className="bv-timeline-marker">
                      <div className="bv-timeline-dot" />
                      {i < payments.length - 1 && <div className="bv-timeline-line" />}
                    </div>
                    <div className="bv-timeline-body">
                      <div className="bv-timeline-top">
                        <span className="bv-timeline-date">{fmtDate(p.created_at)}</span>
                        <span className="bv-timeline-time">{fmtTime(p.created_at)}</span>
                      </div>
                      <div className="bv-timeline-amount">{fmt(p.amount)}</div>
                      <div className="bv-timeline-running">Running total: {fmt(runningTotal)}</div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        <div className="bv-footer">
          <StoreIcon />
          Powered by <strong>Lipa Polepole</strong> · Installment tracking for Kenyan businesses
        </div>
      </div>
    </div>
  )
}
