import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import Dashboard from './pages/vendor/Dashboard'
import Customers from './pages/vendor/Customers'
import AddCustomer from './pages/vendor/AddCustomer'
import PlanDetails from './pages/vendor/PlanDetails'
import BalanceView from './pages/customer/BalanceView'

const ProtectedRoute = ({ children }) => {
  const { vendor, loading } = useAuth()
  if (loading) return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-base)', color: 'var(--text-muted)' }}>Loading...</div>
  return vendor ? children : <Navigate to="/login" />
}

function App() {
  return (
    <HelmetProvider>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/track/:trackingToken" element={<BalanceView />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/customers" element={<ProtectedRoute><Customers /></ProtectedRoute>} />
          <Route path="/customers/add" element={<ProtectedRoute><AddCustomer /></ProtectedRoute>} />
          <Route path="/plans/:planId" element={<ProtectedRoute><PlanDetails /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </HelmetProvider>
  )
}

export default App
