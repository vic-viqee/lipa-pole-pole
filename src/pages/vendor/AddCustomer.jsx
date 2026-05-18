import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createCustomer } from '../../services/customerService'
import { createPlan } from '../../services/paymentService'
import { Button, Input, Card } from '../../components/ui'
import Layout from '../../components/Layout'

const ArrowLeftIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12"/>
    <polyline points="12 19 5 12 12 5"/>
  </svg>
)

const ArrowRightIcon = () => (
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

const UserIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

export default function AddCustomer() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdCustomer, setCreatedCustomer] = useState(null)

  const [customerForm, setCustomerForm] = useState({
    full_name: '',
    phone: '',
    national_id: ''
  })

  const [planForm, setPlanForm] = useState({
    product_name: '',
    total_price: '',
    deposit_paid: ''
  })

  const handleCreateCustomer = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await createCustomer(customerForm)
      setCreatedCustomer(res.data)
      setStep(2)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create customer')
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePlan = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await createPlan({
        product_name: planForm.product_name,
        total_price: parseFloat(planForm.total_price),
        deposit_paid: parseFloat(planForm.deposit_paid),
        customer_id: createdCustomer.id
      })
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create plan')
    } finally {
      setLoading(false)
    }
  }

  const balance = planForm.total_price && planForm.deposit_paid
    ? parseFloat(planForm.total_price) - parseFloat(planForm.deposit_paid)
    : null

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE')}`

  const steps = [
    { num: 1, name: 'Customer Details', desc: 'Name, phone, ID' },
    { num: 2, name: 'Installment Plan', desc: 'Product, price, deposit' }
  ]

  return (
    <Layout>
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--text-tertiary)', textDecoration: 'none', marginBottom: '32px', fontSize: '14px' }}>
          <ArrowLeftIcon />
          Back to Dashboard
        </Link>

        <div style={{ display: 'flex', gap: '16px', marginBottom: '40px' }}>
          {steps.map((s, i) => (
            <div key={s.num} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                fontSize: '14px',
                flexShrink: 0,
                background: step > s.num ? 'var(--color-primary-subtle)' : step === s.num ? 'var(--color-primary)' : 'var(--surface-overlay)',
                color: step > s.num ? 'var(--color-primary)' : step === s.num ? 'oklch(15% 0 0)' : 'var(--text-muted)',
                border: step > s.num ? '1px solid var(--color-primary-border)' : '1px solid var(--border-default)'
              }}>
                {step > s.num ? <CheckIcon /> : s.num}
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: step === s.num ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{s.name}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{s.desc}</div>
              </div>
              {i < steps.length - 1 && (
                <div style={{ 
                  width: '40px', 
                  height: '1px', 
                  background: step > s.num ? 'var(--color-primary-border)' : 'var(--border-default)',
                  flexShrink: 0,
                  marginLeft: 'auto'
                }} />
              )}
            </div>
          ))}
        </div>

        {step === 1 && (
          <Card padding="lg" className="animate-slideUp">
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 700, marginBottom: '8px' }}>
              Add New Customer
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginBottom: '24px' }}>
              Enter the customer's details to get started
            </p>

            {error && (
              <div className="auth-error" style={{ marginBottom: '20px' }}>{error}</div>
            )}

            <form onSubmit={handleCreateCustomer} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <Input
                label="Full Name"
                required
                value={customerForm.full_name}
                onChange={e => setCustomerForm({ ...customerForm, full_name: e.target.value })}
                placeholder="e.g. John Kamau"
              />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <Input
                  label="Phone Number"
                  type="tel"
                  required
                  value={customerForm.phone}
                  onChange={e => setCustomerForm({ ...customerForm, phone: e.target.value })}
                  placeholder="0712 345 678"
                />
                <Input
                  label="National ID"
                  required
                  value={customerForm.national_id}
                  onChange={e => setCustomerForm({ ...customerForm, national_id: e.target.value })}
                  placeholder="12345678"
                />
              </div>
              <Button type="submit" loading={loading}>
                Continue to Plan
                <ArrowRightIcon />
              </Button>
            </form>
          </Card>
        )}

        {step === 2 && (
          <Card padding="lg" className="animate-slideUp">
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 700, marginBottom: '8px' }}>
              Create Installment Plan
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginBottom: '24px' }}>
              Set the product, price and deposit for this customer
            </p>

            {createdCustomer && (
              <div style={{
                background: 'var(--color-primary-subtle)',
                border: '1px solid var(--color-primary-border)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '24px'
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  background: 'oklch(85% 0.04 145)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-primary)'
                }}>
                  <UserIcon />
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '15px' }}>{createdCustomer.full_name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{createdCustomer.phone}</div>
                </div>
                <div style={{ marginLeft: 'auto', background: 'var(--color-primary)', color: 'oklch(15% 0 0)', fontSize: '11px', fontWeight: 600, padding: '4px 10px', borderRadius: 'var(--radius-full)' }}>
                  Added
                </div>
              </div>
            )}

            {error && (
              <div className="auth-error" style={{ marginBottom: '20px' }}>{error}</div>
            )}

            <form onSubmit={handleCreatePlan} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <Input
                label="Product Name"
                required
                value={planForm.product_name}
                onChange={e => setPlanForm({ ...planForm, product_name: e.target.value })}
                placeholder="e.g. Samsung 32 inch TV"
              />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <Input
                  label="Total Price (KSh)"
                  type="number"
                  required
                  min="1"
                  value={planForm.total_price}
                  onChange={e => setPlanForm({ ...planForm, total_price: e.target.value })}
                  placeholder="30000"
                />
                <Input
                  label="Deposit Paid (KSh)"
                  type="number"
                  required
                  min="0"
                  value={planForm.deposit_paid}
                  onChange={e => setPlanForm({ ...planForm, deposit_paid: e.target.value })}
                  placeholder="5000"
                  hint="Amount paid upfront today"
                />
              </div>

              {balance !== null && balance >= 0 && (
                <div style={{
                  background: 'var(--color-primary-subtle)',
                  border: '1px solid var(--color-primary-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>Remaining Balance</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Customer will pay this over time</div>
                  </div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 800, color: 'var(--color-primary)' }}>
                    {fmt(balance)}
                  </div>
                </div>
              )}

              <Button type="submit" loading={loading}>
                Create Plan
                <ArrowRightIcon />
              </Button>
            </form>
          </Card>
        )}
      </div>
    </Layout>
  )
}
