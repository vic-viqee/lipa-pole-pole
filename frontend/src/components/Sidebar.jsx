import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/customers', label: 'Customers', icon: '👥' },
  { path: '/customers/add', label: 'Add Customer', icon: '➕' },
]

export default function Sidebar() {
  const { vendor, logout, privacyMode, togglePrivacyMode } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside style={styles.sidebar}>
      <div style={styles.brand}>
        <span style={styles.brandIcon}>💚</span>
        <span style={styles.brandName}>Lipa Polepole</span>
      </div>

      <div style={styles.shopName}>{vendor?.shop_name}</div>

      <nav style={styles.nav}>
        {navItems.map(({ path, label, icon }) => (
          <Link
            key={path}
            to={path}
            style={{
              ...styles.navItem,
              ...(location.pathname === path ? styles.navItemActive : {})
            }}
          >
            <span>{icon}</span>
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      <div style={styles.divider} />

      <button 
        style={{
          ...styles.privacyToggle,
          ...(privacyMode ? styles.privacyToggleActive : {})
        }} 
        onClick={togglePrivacyMode}
        title={privacyMode ? "Show sensitive info" : "Hide sensitive info"}
      >
        <span>{privacyMode ? '👁️' : '🙈'}</span>
        <span>{privacyMode ? 'Show Balances' : 'Hide Balances'}</span>
      </button>

      <button style={styles.logout} onClick={handleLogout}>
        🚪 Logout
      </button>
    </aside>
  )
}

const styles = {
  sidebar: { width: '240px', minHeight: '100vh', background: 'var(--white)', borderRight: '1px solid #E5E7EB', display: 'flex', flexDirection: 'column', padding: '1.5rem 1rem', position: 'fixed', top: 0, left: 0 },
  brand: { display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' },
  brandIcon: { fontSize: '1.5rem' },
  brandName: { fontWeight: 800, fontSize: '1.1rem', color: 'var(--black)' },
  shopName: { fontSize: '0.8rem', color: 'var(--gray-400)', marginBottom: '2rem', paddingLeft: '0.25rem' },
  nav: { display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 },
  navItem: { display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', borderRadius: '8px', textDecoration: 'none', color: 'var(--gray-700)', fontWeight: 500, fontSize: '0.95rem', transition: 'all 0.15s' },
  navItemActive: { background: 'var(--green-light)', color: 'var(--green-dark)', fontWeight: 700 },
  divider: { height: '1px', background: '#E5E7EB', margin: '1rem 0' },
  privacyToggle: { display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid transparent', background: 'var(--gray-50)', color: 'var(--gray-700)', cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem', marginBottom: '0.5rem', transition: 'all 0.15s' },
  privacyToggleActive: { background: 'var(--color-primary-subtle)', color: 'var(--color-primary)', border: '1px solid var(--color-primary-border)' },
  logout: { background: 'none', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0.75rem', cursor: 'pointer', color: 'var(--gray-700)', fontWeight: 500, fontSize: '0.95rem' }
}