import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { trackPlan, getPaymentsPublic, initiateMpesaPayment } from '../../services/paymentService'
import { Button } from '../../components/ui'
import './BalanceView.css'

const LogoIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v12M8 10h8M8 14h8"/>
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

  const refreshPublicData = useCallback(async () => {
    const [planRes, paymentsRes] = await Promise.all([
      trackPlan(trackingToken),
      getPaymentsPublic(trackingToken),
    ])
    const newPlan = planRes.data
    if (plan && plan.status === 'active' && newPlan.status === 'completed') {
      setShowConfetti(true)
      setTimeout(() => setShowConfetti(false), 5000)
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
      setPayError('Phone must start with 254 (e.g. 2547... or 2541...)')
      return
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setPayError('Enter a valid amount')
      return
    }
    if (amount > Number(plan.balance)) {
      setPayError('Amount cannot be greater than the remaining balance')
      return
    }

    try {
      setPaying(true)
      await initiateMpesaPayment(trackingToken, phone, Math.floor(amount))
      setPaySuccess('STK push sent. Check your phone and enter your M-Pesa PIN.')
      setPayAmount('')
      await refreshPublicData()
      setPolling(true)
      setPollTicksLeft(9)
    } catch (err) {
      setPayError(err.response?.data?.detail || 'Failed to initiate payment')
    } finally {
      setPaying(false)
    }
  }

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE')}`
  const fmtDate = (d) => new Date(d).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' })
if (loading) return (
  <div className="bv-page">
    <div className="bv-header">
      <div className="bv-brand">
        <div className="bv-logo"><LogoIcon /></div>
        <span className="bv-brand-name">Lipa Polepole</span>
      </div>
    </div>
    <div className="bv-content">
      <div className="bv-card">
        <div className="skeleton" style={{ height: '140px', marginBottom: '20px' }} />
        <div className="skeleton skeleton-text" style={{ width: '40%', marginBottom: '8px' }} />
        <div className="skeleton" style={{ height: '12px', borderRadius: '6px', marginBottom: '20px' }} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div className="skeleton" style={{ height: '60px' }} />
          <div className="skeleton" style={{ height: '60px' }} />
        </div>
      </div>
    </div>
  </div>
)

if (notFound) return (
  <div className="bv-page">
    <div className="bv-header">
      <div className="bv-logo"><LogoIcon /></div>
      <span className="bv-brand-name">Lipa Polepole</span>
    </div>
    <div className="bv-content">
      <div className="bv-not-found">
        <div className="bv-not-found-icon">?</div>
        <h2>Plan Not Found</h2>
        <p>This tracking link is invalid. Please check with your vendor.</p>
      </div>
    </div>
  </div>
)

  const paid = plan.deposit_paid + plan.amount_paid
  const pct = Math.min(Math.round((paid / plan.total_price) * 100), 100)
  const isComplete = plan.status === 'completed'

  return (
    <div className="bv-page">
      <div className="bv-header">
        <div className="bv-brand">
          <div className="bv-logo"><LogoIcon /></div>
          <span className="bv-brand-name">Lipa Polepole</span>
        </div>
        <div className="bv-header-product">
          <h1>{plan.product_name}</h1>
          <p>Your installment plan · Plan #{plan.id}</p>
        </div>
      </div>

      <div className="bv-content">
        {isComplete ? (
          <div className="bv-card bv-card-success animate-slideUp">
            <div className="bv-complete-icon"><PartyIcon /></div>
            <h2 className="bv-complete-title">Fully Paid!</h2>
            <p className="bv-complete-sub">You have completed all payments. You can now collect your item from the shop.</p>
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
              <div className="bv-balance-sub">Amount left to pay</div>
            </div>

            <div className="bv-progress-section">
              <div className="bv-progress-top">
                <span>Payment progress</span>
                <strong className="bv-success">{pct}% complete</strong>
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
            <h3 className="bv-card-title">Pay Now via M-Pesa</h3>
            <form className="bv-pay-form" onSubmit={handlePay}>
              <input
                className="bv-input"
                type="tel"
                placeholder="Phone e.g. 254712345678"
                value={payPhone}
                onChange={(e) => setPayPhone(e.target.value.replace(/\D/g, ''))}
                required
              />
              <input
                className="bv-input"
                type="number"
                min="1"
                step="1"
                max={Number(plan.balance)}
                placeholder={`Amount (max ${Math.floor(Number(plan.balance))})`}
                value={payAmount}
                onChange={(e) => setPayAmount(e.target.value)}
                required
              />
              <div className="bv-quick-row">
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
                  className="bv-quick-btn"
                  onClick={() => setPayAmount(String(Math.floor(Number(plan.balance))))}
                >
                  Max
                </button>
              </div>
              <Button type="submit" loading={paying} fullWidth>
                Pay Now
              </Button>
              <p className="bv-hint">You can pay any amount up to your current balance.</p>
              {payError && <p className="bv-error">{payError}</p>}
              {paySuccess && (
                <p className="bv-success-msg">
                  <CheckIcon />
                  {paySuccess}
                  {polling && ` Refreshing payment status... (${pollTicksLeft * 10}s)`}
                </p>
              )}
            </form>
          </div>
        )}

        <div className="bv-card animate-slideUp" style={{ animationDelay: '200ms' }}>
          <h3 className="bv-card-title">Payment History</h3>
          <div className="bv-payment-list">
            <div className="bv-deposit-item">
              <div>
                <span className="bv-deposit-label">Initial Deposit</span>
                <span className="bv-deposit-tag">Day 1</span>
              </div>
              <span className="bv-success">{fmt(plan.deposit_paid)}</span>
            </div>
            {payments.length === 0 ? (
              <div className="bv-empty-payments">No additional payments recorded yet</div>
            ) : (
              payments.map(p => (
                <div key={p.id} className="bv-payment-item">
                  <div className="bv-payment-left">
                    <div className="bv-payment-dot" />
                    <span className="bv-payment-date">{fmtDate(p.created_at)}</span>
                  </div>
                  <span className="bv-success">{fmt(p.amount)}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bv-footer">Powered by <span className="bv-success">Lipa Polepole</span> · Installment tracking for Kenyan businesses</div>
      </div>
    </div>
  )
}
