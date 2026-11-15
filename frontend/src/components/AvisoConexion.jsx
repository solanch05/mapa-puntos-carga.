import { useEffect, useState } from 'react'
import { pendientes } from '../api/colaOffline'

/** Banda que avisa de que no hay conexión y de los reportes en espera. */
export default function AvisoConexion() {
  const [enLinea, setEnLinea] = useState(navigator.onLine)
  const [enCola, setEnCola] = useState(pendientes())

  useEffect(() => {
    const online = () => setEnLinea(true)
    const offline = () => setEnLinea(false)
    const cola = (e) => setEnCola(e.detail)
    window.addEventListener('online', online)
    window.addEventListener('offline', offline)
    window.addEventListener('cola-cambio', cola)
    return () => {
      window.removeEventListener('online', online)
      window.removeEventListener('offline', offline)
      window.removeEventListener('cola-cambio', cola)
    }
  }, [])

  if (enLinea && enCola === 0) return null
  return (
    <div className="aviso-conexion" role="status">
      {!enLinea && 'Sin conexión: ves el último estado conocido. '}
      {enCola > 0 && `${enCola} reporte(s) se enviarán cuando vuelva la señal.`}
    </div>
  )
}
