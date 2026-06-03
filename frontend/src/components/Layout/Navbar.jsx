import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui'
import './Navbar.css'

const LogoIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 6v12M8 10h8M8 14h8"/>
  </svg>
)

const LogoutIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
)

export default function Navbar() {
  const { vendor, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="navbar-logo">
            <LogoIcon />
          </div>
          <span className="navbar-name">Lipa Polepole</span>
        </Link>

        <div className="navbar-right">
          {vendor && (
            <>
              <span className="navbar-shop">
                <span className="navbar-shop-label">Shop:</span> {vendor.shop_name}
              </span>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={handleLogout}
              >
                <LogoutIcon />
                <span className="navbar-logout-text">Logout</span>
              </Button>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
