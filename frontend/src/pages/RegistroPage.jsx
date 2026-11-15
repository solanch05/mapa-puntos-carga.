import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Registro con correo y contraseña. Pedimos solo los datos necesarios. */
export default function RegistroPage() {
  const { registro } = useAuth()
  const navegar = useNavigate()
  const [params] = useSearchParams()
  const [datos, setDatos] = useState({ nombre: '', email: '', password: '' })
  const [error, setError] = useState(null)

  const volver = params.get('volver')?.startsWith('/') && !params.get('volver').startsWith('//') ? params.get('volver') : '/'
  const campo = (n) => ({ value: datos[n], onChange: (e) => setDatos({ ...datos, [n]: e.target.value }) })

  const enviar = async (e) => {
    e.preventDefault()
    try {
      await registro(datos)
      navegar(volver, { replace: true })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="pagina formulario estrecho" onSubmit={enviar}>
      <h1>Crear cuenta</h1>
      <label>Nombre <input {...campo('nombre')} required maxLength={80} autoComplete="given-name" /></label>
      <label>Email <input type="email" {...campo('email')} required autoComplete="email" /></label>
      <label>
        Contraseña <input type="password" {...campo('password')} required minLength={8} autoComplete="new-password" />
        <small>Mínimo 8 caracteres, que no sea solo números ni una contraseña común.</small>
      </label>
      {error && <p className="mensaje error">{error}</p>}
      <button className="boton primario ancho">Crear cuenta</button>
      <p>¿Ya tienes cuenta? <Link to="/entrar">Entrar</Link></p>
    </form>
  )
}
