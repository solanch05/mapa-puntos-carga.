import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import './styles.css'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { iniciarColaOffline } from './api/colaOffline'

// Marca de inicio para medir "de la pantalla de inicio a la ficha en < 30 s".
window.__inicioApp = performance.now()
iniciarColaOffline()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
