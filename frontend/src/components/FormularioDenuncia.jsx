import { useState } from 'react'
import { api } from '../api/puntos'

const MOTIVOS = {
  no_existe: 'El punto no existe',
  datos_falsos: 'Información falsa',
  duplicado: 'Punto duplicado',
  spam: 'Spam o publicidad',
  inseguro: 'Lugar inseguro o trato inadecuado',
  otro: 'Otro',
}

/** Denunciar un punto o uno de sus reportes. Va a la cola de moderación. */
export default function FormularioDenuncia({ punto, onTerminar }) {
  const [motivo, setMotivo] = useState('datos_falsos')
  const [reporte, setReporte] = useState('')
  const [detalle, setDetalle] = useState('')
  const [estado, setEstado] = useState(null)

  const enviar = async (e) => {
    e.preventDefault()
    try {
      await api.denunciar({ punto: punto.id, reporte: reporte || null, motivo, detalle })
      setEstado({ tipo: 'ok', texto: 'Denuncia enviada. La revisará un moderador.' })
      setTimeout(onTerminar, 1500)
    } catch (error) {
      setEstado({ tipo: 'error', texto: error.message })
    }
  }

  return (
    <form className="denuncia" onSubmit={enviar}>
      <label>
        Motivo
        <select value={motivo} onChange={(e) => setMotivo(e.target.value)}>
          {Object.entries(MOTIVOS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </label>
      {punto.ultimos_reportes.length > 0 && (
        <label>
          ¿Sobre qué?
          <select value={reporte} onChange={(e) => setReporte(e.target.value)}>
            <option value="">El punto en general</option>
            {punto.ultimos_reportes.map((r) => (
              <option key={r.id} value={r.id}>Reporte de {r.usuario_nombre} ({r.estado})</option>
            ))}
          </select>
        </label>
      )}
      <label>
        Detalle (opcional)
        <input maxLength={280} value={detalle} onChange={(e) => setDetalle(e.target.value)} />
      </label>
      <button className="boton peligro">Enviar denuncia</button>
      {estado && <p className={`mensaje ${estado.tipo}`}>{estado.texto}</p>}
    </form>
  )
}
