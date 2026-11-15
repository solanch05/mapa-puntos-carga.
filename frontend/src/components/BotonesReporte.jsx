/**
 * Flujo 3 · "¿Hay corriente ahora?"
 * Deliberadamente de UN toque: elegir el estado ya envía el reporte.
 * Comentario y foto son opcionales y van plegados.
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/puntos'
import { useAuth } from '../context/AuthContext'
import { ESTADOS } from '../utils/formato'

const OPCIONES = ['con_energia', 'sin_energia', 'lleno', 'cerrado']

export default function BotonesReporte({ puntoId, onReportado }) {
  const { usuario, refrescarUsuario } = useAuth()
  const [extra, setExtra] = useState(false)
  const [comentario, setComentario] = useState('')
  const [foto, setFoto] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [mensaje, setMensaje] = useState(null)

  if (!usuario) {
    return (
      <p className="nota">
        <Link to={`/entrar?volver=/`}>Entra</Link> para confirmar si hay corriente. Es un solo toque.
      </p>
    )
  }

  const reportar = async (estado) => {
    setEnviando(true)
    setMensaje(null)
    try {
      const resultado = await api.reportarEstado(puntoId, { estado, comentario, foto })
      if (resultado.encolado) {
        setMensaje({ tipo: 'aviso', texto: 'Sin conexión: tu reporte se enviará al volver la señal.' })
      } else {
        setMensaje({ tipo: 'ok', texto: `¡Gracias! Reputación: ★ ${resultado.reputacion}` })
        refrescarUsuario()
        onReportado?.()
      }
      setComentario('')
      setFoto(null)
      setExtra(false)
    } catch (error) {
      setMensaje({ tipo: 'error', texto: error.message })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="reporte" aria-label="¿Hay corriente ahora?">
      <h3>¿Hay corriente ahora?</h3>
      <div className="botones-estado">
        {OPCIONES.map((estado) => (
          <button
            key={estado}
            disabled={enviando}
            style={{ '--color': ESTADOS[estado].color }}
            onClick={() => reportar(estado)}
          >
            {ESTADOS[estado].texto}
          </button>
        ))}
      </div>
      <button className="enlace" onClick={() => setExtra(!extra)}>
        {extra ? 'Ocultar' : 'Añadir'} comentario o foto (opcional)
      </button>
      {extra && (
        <div className="extra-reporte">
          <input
            maxLength={280}
            placeholder="Ej.: queda un enchufe libre"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
          />
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFoto(e.target.files[0] ?? null)} />
          <small>La foto se limpia de metadatos (incluida la ubicación GPS) antes de guardarse.</small>
        </div>
      )}
      {mensaje && <p className={`mensaje ${mensaje.tipo}`}>{mensaje.texto}</p>}
    </section>
  )
}
