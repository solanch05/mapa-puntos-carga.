import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navegar = useNavigate()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  // Solo rutas internas: evita redirecciones abiertas a otros sitios.
  const volver = params.get('volver')?.startsWith('/') && !params.get('volver').startsWith('//') ? params.get('volver') : '/'

  const enviar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    try {
      await login(email, password)
      navegar(volver, { replace: true })
    } catch (err) {
      setError(err.status === 401 ? 'Email o contraseña incorrectos.' : err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="pagina formulario estrecho" onSubmit={enviar}>
      <h1>Entrar</h1>
      <label>Email <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
      <label>Contraseña <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
      {error && <p className="mensaje error">{error}</p>}
      <button className="boton primario ancho" disabled={enviando}>Entrar</button>
      <p>¿No tienes cuenta? <Link to={`/registro?volver=${encodeURIComponent(volver)}`}>Crear una</Link></p>
    </form>
  )
}
