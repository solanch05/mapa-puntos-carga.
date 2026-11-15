import { Navigate, Route, Routes } from 'react-router-dom'
import AvisoConexion from './components/AvisoConexion'
import BarraSuperior from './components/BarraSuperior'
import { useAuth } from './context/AuthContext'
import FavoritosPage from './pages/FavoritosPage'
import LoginPage from './pages/LoginPage'
import MapaPage from './pages/MapaPage'
import MisPuntosPage from './pages/MisPuntosPage'
import PuntoFormPage from './pages/PuntoFormPage'
import RegistroPage from './pages/RegistroPage'

/** Rutas que exigen sesión: si no la hay, se va al login y luego se vuelve. */
function Privada({ children }) {
  const { usuario, cargando } = useAuth()
  if (cargando) return <p className="centrado">Cargando…</p>
  if (!usuario) return <Navigate to={`/entrar?volver=${encodeURIComponent(location.pathname)}`} replace />
  return children
}

export default function App() {
  return (
    <div className="app">
      <BarraSuperior />
      <AvisoConexion />
      <main className="contenido">
        <Routes>
          <Route path="/" element={<MapaPage />} />
          <Route path="/entrar" element={<LoginPage />} />
          <Route path="/registro" element={<RegistroPage />} />
          <Route path="/agregar" element={<Privada><PuntoFormPage /></Privada>} />
          <Route path="/puntos/:id/editar" element={<Privada><PuntoFormPage /></Privada>} />
          <Route path="/mis-puntos" element={<Privada><MisPuntosPage /></Privada>} />
          <Route path="/favoritos" element={<Privada><FavoritosPage /></Privada>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
