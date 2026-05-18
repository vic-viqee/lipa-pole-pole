import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCustomers } from '../../services/customerService'
import { getPlans } from '../../services/paymentService'
import { Button } from '../../components/ui'
import Layout from '../../components/Layout'
import '../../styles/pages.css'

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
)

const EmptyIcon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
)

export default function Customers() {
  const [customers, setCustomers] = useState([])
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchData() {
      try {
        const [customersRes, plansRes] = await Promise.all([getCustomers(), getPlans()])
        setCustomers(customersRes.data)
        setPlans(plansRes.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load customers')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const statsByCustomer = useMemo(() => {
    const map = new Map()
    for (const plan of plans) {
      const current = map.get(plan.customer_id) || { plans: 0, outstanding: 0 }
      current.plans += 1
      current.outstanding += Number(plan.balance || 0)
      map.set(plan.customer_id, current)
    }
    return map
  }, [plans])

  const fmt = (n) => `KSh ${Number(n).toLocaleString('en-KE')}`

  return (
    <Layout>
      <div className="page-header animate-slideUp">
        <div>
          <h1 className="page-title">Customers</h1>
          <p className="page-subtitle">All customers and how many plans each has</p>
        </div>
        <Link to="/customers/add">
          <Button>
            <PlusIcon />
            Add Customer
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>National ID</th>
                <th>Plans</th>
                <th>Outstanding</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map(i => (
                <tr key={i}>
                  <td><div className="skeleton skeleton-text" style={{ width: '120px' }} /></td>
                  <td><div className="skeleton skeleton-text" style={{ width: '100px' }} /></td>
                  <td><div className="skeleton skeleton-text" style={{ width: '80px' }} /></td>
                  <td><div className="skeleton skeleton-text" style={{ width: '30px' }} /></td>
                  <td><div className="skeleton skeleton-text" style={{ width: '90px' }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : error ? (
        <div className="auth-error">{error}</div>
      ) : (
        <div className="table-container animate-slideUp">
          {customers.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <EmptyIcon />
              </div>
              <h3 className="empty-state-title">No customers yet</h3>
              <p className="empty-state-description">
                Add your first customer to start creating installment plans
              </p>
              <Link to="/customers/add">
                <Button>
                  <PlusIcon />
                  Add Customer
                </Button>
              </Link>
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>National ID</th>
                  <th>Plans</th>
                  <th>Outstanding</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => {
                  const stats = statsByCustomer.get(customer.id) || { plans: 0, outstanding: 0 }
                  return (
                    <tr key={customer.id}>
                      <td className="table-cell-primary">{customer.full_name}</td>
                      <td>{customer.phone}</td>
                      <td>{customer.national_id}</td>
                      <td>{stats.plans}</td>
                      <td style={{ color: 'oklch(70% 0.14 85)' }}>{fmt(stats.outstanding)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </Layout>
  )
}
