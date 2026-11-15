import { useEffect, useState } from 'react'
import { api } from '../api/puntos'
import { ESTADOS, TIPOS, haceCuanto } from '../utils/formato'

/** Favoritos. En la fase 2 tendrán avisos cuando cambie su estado. */
export default function FavoritosPage() {
  const [puntos, setPuntos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.favoritos().then(setPuntos).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="pagina">
      <h1>Favoritos</h1>
      {error && <p className="mensaje error">{error}</p>}
      {puntos?.length === 0 && <p>Marca puntos con ☆ desde su ficha para tenerlos a mano.</p>}
      <ul className="tarjetas">
        {puntos?.map((p) => (
          <li key={p.id} className="tarjeta">
            <div className="fila">
              <strong>{p.nombre}</strong>
              <span className="etiqueta" style={{ background: ESTADOS[p.estado_actual].color, color: '#fff' }}>
                {ESTADOS[p.estado_actual].texto}
              </span>
            </div>
            <small>{TIPOS[p.tipo]}{p.confirmado_en && ` · confirmado ${haceCuanto(p.confirmado_en)}`}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}
