/**
 * Ficha de un punto (flujo 1, paso 3): nombre, horario, tomas, acceso y
 * "confirmado hace X min". Desde aquí se reporta, se marca favorito, se pide
 * el contacto y se denuncia.
 */

import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/puntos'
import { useAuth } from '../context/AuthContext'
import {
  ACCESOS, CONECTORES, ESTADOS, RESPALDOS, TIPOS,
  distanciaM, haceCuanto, resumirHorarios, textoDistancia, urlComoLlegar,
} from '../utils/formato'
import BotonesReporte from './BotonesReporte'
import FormularioDenuncia from './FormularioDenuncia'

export default function FichaPunto({ id, miUbicacion, onCerrar, onCargada, onActualizado }) {
  const { usuario } = useAuth()
  const [punto, setPunto] = useState(null)
  const [error, setError] = useState(null)
  const [contacto, setContacto] = useState(null)
  const [denunciando, setDenunciando] = useState(false)

  const cargar = useCallback(async () => {
    try {
      setPunto(await api.obtenerPunto(id))
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [id])

  useEffect(() => {
    setPunto(null)
    setContacto(null)
    setDenunciando(false)
    cargar()
  }, [cargar])

  useEffect(() => {
    if (punto) onCargada?.(punto)
  }, [punto, onCargada])

  if (error) return <aside className="ficha"><p className="mensaje error">{error}</p></aside>
  if (!punto) return <aside className="ficha"><p>Cargando…</p></aside>

  const estado = ESTADOS[punto.estado_actual] ?? ESTADOS.sin_confirmar
  const distancia = miUbicacion ? distanciaM(miUbicacion, [punto.lat, punto.lng]) : null

  const alternarFavorito = async () => {
    const r = await api.marcarFavorito(punto.id, !punto.es_favorito)
    setPunto({ ...punto, es_favorito: r.es_favorito })
  }

  const verContacto = async () => {
    try {
      setContacto((await api.pedirContacto(punto.id)).contacto)
    } catch (e) {
      setContacto(e.message)
    }
  }

  return (
    <aside className="ficha" aria-label={`Ficha de ${punto.nombre}`}>
      <button className="cerrar" aria-label="Cerrar ficha" onClick={onCerrar}>✕</button>
      <h2>{punto.nombre}</h2>
      <p className="subtitulo">
        {TIPOS[punto.tipo]}
        {distancia != null && ` · a ${textoDistancia(distancia)}`}
        {punto.abierto_ahora ? ' · abierto ahora' : ' · fuera de horario'}
      </p>

      <div className="estado" style={{ '--color': estado.color }} data-testid="estado-actual">
        <strong>{estado.texto}</strong>
        <span>
          {punto.confirmado_en
            ? `confirmado ${haceCuanto(punto.confirmado_en)}`
            : 'nadie lo ha confirmado en las últimas horas'}
        </span>
      </div>

      <a className="boton primario ancho" href={urlComoLlegar(punto.lat, punto.lng)} target="_blank" rel="noreferrer">
        🚶 Cómo llegar
      </a>

      <BotonesReporte
        puntoId={punto.id}
        onReportado={() => {
          cargar()
          onActualizado?.()
        }}
      />

      <dl className="datos">
        <dt>Horario</dt>
        <dd>{resumirHorarios(punto.horarios).map((l) => <div key={l}>{l}</div>)}</dd>
        <dt>Tomas</dt>
        <dd>{punto.numero_tomas} · {CONECTORES[punto.tipo_conector]}</dd>
        <dt>Acceso</dt>
        <dd>{ACCESOS[punto.acceso]}</dd>
        <dt>Respaldo</dt>
        <dd>{RESPALDOS[punto.respaldo]}</dd>
        {punto.descripcion && (<><dt>Cómo encontrarlo</dt><dd>{punto.descripcion}</dd></>)}
      </dl>

      {punto.ubicacion_aproximada && (
        <p className="nota">
          📍 Ubicación aproximada (unos 200 m) para proteger la privacidad del anfitrión. Pide el contacto o la
          referencia exacta antes de ir.
        </p>
      )}
      {punto.tipo === 'vivienda' && (
        <p className="nota buenas-practicas">
          Buenas prácticas: avisa antes de llegar, ve acompañado si es de noche, respeta el horario y no te quedes
          más tiempo del necesario.
        </p>
      )}

      {usuario && (
        <div className="acciones">
          <button onClick={alternarFavorito}>{punto.es_favorito ? '★ En favoritos' : '☆ Favorito'}</button>
          {punto.tiene_contacto && !contacto && <button onClick={verContacto}>Ver contacto</button>}
          {contacto && <span className="contacto">📞 {contacto}</span>}
          {!punto.es_mio && <button onClick={() => setDenunciando(!denunciando)}>Denunciar</button>}
        </div>
      )}
      {denunciando && <FormularioDenuncia punto={punto} onTerminar={() => setDenunciando(false)} />}

      {punto.ultimos_reportes.length > 0 && (
        <section>
          <h3>Últimos reportes</h3>
          <ul className="reportes">
            {punto.ultimos_reportes.map((r) => (
              <li key={r.id}>
                <span className="punto-color" style={{ background: ESTADOS[r.estado].color }} />
                <span>
                  <strong>{ESTADOS[r.estado].texto}</strong> · {r.usuario_nombre} · {haceCuanto(r.creado_en)}
                  {r.comentario && <em> — {r.comentario}</em>}
                </span>
                {r.foto && <a href={r.foto} target="_blank" rel="noreferrer">foto</a>}
              </li>
            ))}
          </ul>
        </section>
      )}
      <p className="pie-ficha">Publicado por {punto.creado_por_nombre}</p>
    </aside>
  )
}
