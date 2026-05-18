import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [vendor, setVendor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [privacyMode, setPrivacyMode] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const savedVendor = localStorage.getItem('vendor')
    const savedPrivacy = localStorage.getItem('privacyMode')
    
    if (token && savedVendor) {
      setVendor(JSON.parse(savedVendor))
    }
    if (savedPrivacy === 'true') {
      setPrivacyMode(true)
    }
    setLoading(false)
  }, [])

  const togglePrivacyMode = () => {
    const newVal = !privacyMode
    setPrivacyMode(newVal)
    localStorage.setItem('privacyMode', newVal.toString())
  }

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('vendor', JSON.stringify(res.data.vendor))
    setVendor(res.data.vendor)
    return res.data
  }

  const register = async (shop_name, email, phone, password) => {
    const res = await api.post('/auth/register', { shop_name, email, phone, password })
    return res.data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('vendor')
    setVendor(null)
  }

  return (
    <AuthContext.Provider value={{ vendor, login, register, logout, loading, privacyMode, togglePrivacyMode }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}