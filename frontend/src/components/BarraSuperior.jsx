import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function BarraSuperior() {
  const { usuario, logout } = useAuth()
  const [abierto, setAbierto] = useState(false)
  const navegar = useNavigate()
  const cerrar = () => setAbierto(false)

  return (
    <header className="barra">
      <Link to="/" className="marca" onClick={cerrar}>
        <img src="/icon.svg" alt="" width="28" height="28" />
        <span>Puntos de Carga</span>
      </Link>
      <button className="boton-menu" aria-label="Menú" aria-expanded={abierto} onClick={() => setAbierto(!abierto)}>
        ☰
      </button>
      <nav className={`menu ${abierto ? 'abierto' : ''}`} onClick={cerrar}>
        <NavLink to="/" end>Mapa</NavLink>
        <NavLink to="/agregar">Agregar punto</NavLink>
        {usuario ? (
          <>
            <NavLink to="/mis-puntos">Mis puntos</NavLink>
            <NavLink to="/favoritos">Favoritos</NavLink>
            {usuario.es_moderador && <a href="/admin/">Moderar</a>}
            <span className="reputacion" title="Tu reputación sube cada vez que confirmas un punto">
              ★ {usuario.reputacion}
            </span>
            <button
              className="enlace"
              onClick={async () => {
                await logout()
                navegar('/')
              }}
            >
              Salir
            </button>
          </>
        ) : (
          <NavLink to="/entrar">Entrar</NavLink>
        )}
      </nav>
    </header>
  )
}
