/** Mis puntos: estado de publicación, nota del moderador, pausar, editar, retirar. */

import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../api/puntos'
import { ESTADOS, PUBLICACION, TIPOS, haceCuanto } from '../utils/formato'

export default function MisPuntosPage() {
  const { state } = useLocation()
  const [puntos, setPuntos] = useState(null)
  const [error, setError] = useState(null)

  const cargar = useCallback(() => api.misPuntos().then(setPuntos).catch((e) => setError(e.message)), [])
  useEffect(() => {
    cargar()
  }, [cargar])

  const accion = async (fn) => {
    try {
      await fn()
      cargar()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="pagina">
      <h1>Mis puntos</h1>
      {state?.recienCreado && (
        <p className={`mensaje ${state.estado === 'activo' ? 'ok' : 'aviso'}`}>
          {state.estado === 'activo'
            ? 'Tu punto ya está publicado en el mapa.'
            : 'Recibido. Tu punto está pendiente de revisión; te avisamos aquí cuando cambie.'}
        </p>
      )}
      {error && <p className="mensaje error">{error}</p>}
      {puntos?.length === 0 && (
        <p>Aún no has compartido ningún punto. <Link to="/agregar">Agregar el primero</Link></p>
      )}
      <ul className="tarjetas">
        {puntos?.map((p) => {
          const pub = PUBLICACION[p.estado_publicacion]
          return (
            <li key={p.id} className="tarjeta">
              <div className="fila">
                <strong>{p.nombre}</strong>
                <span className={`etiqueta ${pub.clase}`}>{pub.texto}</span>
              </div>
              <small>
                {TIPOS[p.tipo]} · {ESTADOS[p.estado_actual].texto}
                {p.confirmado_en && ` ${haceCuanto(p.confirmado_en)}`}
              </small>
              {p.nota_moderacion && <p className="mensaje aviso">Moderación: {p.nota_moderacion}</p>}
              <div className="acciones">
                <Link className="boton secundario" to={`/puntos/${p.id}/editar`}>Editar</Link>
                {['activo', 'pausado'].includes(p.estado_publicacion) && (
                  <button className="boton secundario" onClick={() => accion(() => api.pausarPunto(p.id))}>
                    {p.estado_publicacion === 'activo' ? 'Pausar' : 'Reanudar'}
                  </button>
                )}
                <button
                  className="boton peligro"
                  onClick={() => confirm(`¿Retirar «${p.nombre}» del mapa? No se puede deshacer.`) && accion(() => api.retirarPunto(p.id))}
                >
                  Retirar
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
