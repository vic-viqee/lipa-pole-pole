import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { getPlans } from '../../services/paymentService'
import { Button, Badge, Progress, Card } from '../../components/ui'
import Layout from '../../components/Layout'
import '../../styles/pages.css'

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
)

const ArrowRightIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"/>
    <polyline points="12 5 19 12 12 19"/>
  </svg>
)

const EmptyIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <line x1="3" y1="9" x2="21" y2="9"/>
    <line x1="9" y1="21" x2="9" y2="9"/>
  </svg>
)

export default function Dashboard() {
  const { vendor, privacyMode } = useAuth()
  const navigate = useNavigate()
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const plansRes = await getPlans()
        setPlans(plansRes.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const totalOutstanding = plans.reduce((sum, p) => sum + (p.balance || 0), 0)
  const totalCollected = plans.reduce((sum, p) => sum + (p.amount_paid + p.deposit_paid), 0)
  const activePlans = plans.filter(p => p.status === 'active').length
  const completedPlans = plans.filter(p => p.status === 'completed').length

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE', { minimumFractionDigits: 0 })}`

  const PrivacyMask = ({ children }) => (
    <span 
      style={{
        ...(privacyMode ? {
          filter: 'blur(8px)',
          userSelect: 'none',
          pointerEvents: 'none',
          background: 'var(--color-privacy-overlay)',
          borderRadius: '4px',
          display: 'inline-block',
          minWidth: '100px'
        } : {})
      }}
    >
      {children}
    </span>
  )

  const getStatusBadge = (status) => {
    const variants = {
      active: 'warning',
      completed: 'success',
      defaulted: 'error'
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  return (
    <Layout>
      <div className="page-header animate-slideUp">
        <div>
          <h1 className="page-title">
            Good day, <span className="page-title-accent">{vendor?.shop_name}</span>
          </h1>
          <p className="page-subtitle">Here's an overview of your installment plans</p>
        </div>
        <Link to="/customers/add">
          <Button>
            <PlusIcon />
            New Plan
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="stats-grid stagger-children">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="stat-card">
              <div className="skeleton skeleton-text" style={{ width: '60%' }} />
              <div className="skeleton skeleton-text" style={{ width: '40%', marginTop: '8px' }} />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="stats-grid stagger-children">
            <div className="stat-card">
              <div className="stat-card-label">Outstanding</div>
              <div className="stat-card-value warning">
                <PrivacyMask>{fmt(totalOutstanding)}</PrivacyMask>
              </div>
              <div className="stat-card-sub">Balance to collect</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Collected</div>
              <div className="stat-card-value success">
                <PrivacyMask>{fmt(totalCollected)}</PrivacyMask>
              </div>
              <div className="stat-card-sub">Payments received</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Active Plans</div>
              <div className="stat-card-value">{activePlans}</div>
              <div className="stat-card-sub">In progress</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Completed</div>
              <div className="stat-card-value info">{completedPlans}</div>
              <div className="stat-card-sub">Fully paid</div>
            </div>
          </div>

          <div className="section animate-slideUp" style={{ animationDelay: '200ms' }}>
            <div className="section-header">
              <h2 className="section-title">All Plans ({plans.length})</h2>
            </div>
            <div className="table-container">
              {plans.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">
                    <EmptyIcon />
                  </div>
                  <h3 className="empty-state-title">No plans yet</h3>
                  <p className="empty-state-description">
                    Start by adding a customer and creating their first installment plan
                  </p>
                  <Link to="/customers/add">
                    <Button>
                      <PlusIcon />
                      Create First Plan
                    </Button>
                  </Link>
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Customer</th>
                      <th>Total Price</th>
                      <th>Balance</th>
                      <th>Progress</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {plans.map(plan => {
                      const paid = plan.deposit_paid + plan.amount_paid
                      const pct = Math.round((paid / plan.total_price) * 100)
                      return (
                        <tr key={plan.id} onClick={() => navigate(`/plans/${plan.id}`)}>
                          <td>
                            <div className="table-cell-primary">Customer #{plan.customer_id}</div>
                            <div className="table-cell-sub">{plan.product_name}</div>
                          </td>
                          <td>
                            <PrivacyMask>{fmt(plan.total_price)}</PrivacyMask>
                          </td>
                          <td>
                            <PrivacyMask>{fmt(plan.balance)}</PrivacyMask>
                          </td>
                          <td style={{ width: '180px' }}>
                            <Progress value={pct} variant="gradient" showLabel label={`${pct}%`} />
                          </td>
                          <td>{getStatusBadge(plan.status)}</td>
                          <td>
                            <Link 
                              to={`/plans/${plan.id}`} 
                              onClick={e => e.stopPropagation()}
                              className="table-link"
                            >
                              View <ArrowRightIcon />
                            </Link>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </Layout>
  )
}
