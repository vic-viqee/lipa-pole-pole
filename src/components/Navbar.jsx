export default function Navbar({ title }) {
  return (
    <header style={styles.navbar}>
      <h2 style={styles.title}>{title}</h2>
    </header>
  )
}

const styles = {
  navbar: { background: 'var(--white)', borderBottom: '1px solid #E5E7EB', padding: '1rem 2rem', position: 'sticky', top: 0, zIndex: 10 },
  title: { fontWeight: 700, fontSize: '1.2rem', color: 'var(--gray-900)' }
}