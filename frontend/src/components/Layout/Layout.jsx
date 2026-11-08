import Navbar from './Navbar'
import './Layout.css'

export default function Layout({ children }) {
  return (
    <div className="layout">
      <Navbar />
      <main className="layout-main">
        {children}
      </main>
      <footer className="layout-footer">
        Designed &amp; Developed by{' '}
        <a href="https://viqsystems.tech" target="_blank" rel="noopener noreferrer">
          Viq Systems
        </a>
      </footer>
    </div>
  )
}
