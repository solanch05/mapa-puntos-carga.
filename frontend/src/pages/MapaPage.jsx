/**
 * Flujo 1 · Encontrar dónde cargar.
 * 1. El mapa se centra en tu ubicación (con permiso previo).
 * 2. Filtro "con energía ahora" (y tipo, tomas, abierto ahora).
 * 3. Tocar un pin abre la ficha con "confirmado hace X min".
 * 4. "Cómo llegar" abre la ruta a pie en la app de mapas del teléfono.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/puntos'
import FichaPunto from '../components/FichaPunto'
import Filtros from '../components/Filtros'
import MapaPuntos from '../components/MapaPuntos'
import { CENTRO_PILOTO, ESTADOS, distanciaM, haceCuanto, hora, textoDistancia } from '../utils/formato'

const FILTROS_INICIALES = { conEnergia: false, abiertoAhora: false, tipos: [], minTomas: 0 }

export default function MapaPage() {
  const [filtros, setFiltros] = useState(FILTROS_INICIALES)
  const [vista, setVista] = useState(null)
  const [puntos, setPuntos] = useState([])
  const [sinConexion, setSinConexion] = useState(null)
  const [seleccionado, setSeleccionado] = useState(null)
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [avisoUbicacion, setAvisoUbicacion] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [verLista, setVerLista] = useState(false)
  const fichaMedida = useRef(false)

  // 1. Ubicación del usuario. Solo se usa en el teléfono: NO se envía ni se guarda.
  const pedirUbicacion = useCallback(() => {
    if (!navigator.geolocation) return setAvisoUbicacion('Tu navegador no permite obtener la ubicación.')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setMiUbicacion([pos.coords.latitude, pos.coords.longitude])
        setAvisoUbicacion(null)
      },
      () => setAvisoUbicacion('Sin permiso de ubicación: te mostramos la zona piloto.'),
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 },
    )
  }, [])
  useEffect(pedirUbicacion, [pedirUbicacion])

  // Consulta de puntos cada vez que cambian el área visible o los filtros.
  const cargarPuntos = useCallback(async () => {
    if (!vista) return
    setCargando(true)
    try {
      const resultado = await api.listarPuntos({
        lat: vista.lat.toFixed(5),
        lng: vista.lng.toFixed(5),
        radio_km: Math.min(Math.max(vista.radioKm, 0.5), 20).toFixed(2),
        con_energia: filtros.conEnergia ? 1 : undefined,
        abierto_ahora: filtros.abiertoAhora ? 1 : undefined,
        tipo: filtros.tipos.join(','),
        min_tomas: filtros.minTomas || undefined,
      })
      setPuntos(resultado.puntos)
      setSinConexion(resultado.sinConexion ? resultado.guardadoEn : null)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }, [vista, filtros])

  useEffect(() => {
    const t = setTimeout(cargarPuntos, 250) // espera a que el usuario deje de mover el mapa
    return () => clearTimeout(t)
  }, [cargarPuntos])

  // Métrica del piloto: tiempo desde abrir la app hasta ver la primera ficha.
  const alCargarFicha = useCallback(() => {
    if (fichaMedida.current) return
    fichaMedida.current = true
    const segundos = (performance.now() - window.__inicioApp) / 1000
    window.__segundosHastaFicha = segundos
    console.info(`[métrica] De la pantalla de inicio a la ficha: ${segundos.toFixed(1)} s`)
  }, [])

  const ordenados = useMemo(() => {
    const ref = miUbicacion ?? (vista ? [vista.lat, vista.lng] : CENTRO_PILOTO)
    return puntos
      .map((p) => ({ ...p, distancia: distanciaM(ref, [p.lat, p.lng]) }))
      .sort((a, b) => a.distancia - b.distancia)
  }, [puntos, miUbicacion, vista])

  return (
    <div className="pagina-mapa">
      <Filtros filtros={filtros} onCambio={setFiltros} />

      <div className="estado-mapa">
        {cargando ? 'Buscando…' : `${puntos.length} punto(s) en esta zona`}
        {sinConexion && ` · sin conexión, datos de las ${hora(sinConexion)}`}
        {avisoUbicacion && ` · ${avisoUbicacion}`}
        {error && <span className="mensaje error"> · {error}</span>}
      </div>

      <div className="zona-mapa">
        <MapaPuntos
          puntos={puntos}
          centroInicial={CENTRO_PILOTO}
          miUbicacion={miUbicacion}
          seleccionado={seleccionado}
          onSeleccionar={setSeleccionado}
          onMover={setVista}
        />
        <div className="botones-flotantes">
          <button onClick={pedirUbicacion} title="Centrar en mi ubicación" aria-label="Centrar en mi ubicación">◎</button>
          <button onClick={() => setVerLista(!verLista)} aria-pressed={verLista}>{verLista ? 'Mapa' : 'Lista'}</button>
        </div>
        <Leyenda />

        {verLista && !seleccionado && (
          <ul className="lista-puntos" aria-label="Puntos cercanos">
            {ordenados.map((p) => (
              <li key={p.id}>
                <button onClick={() => setSeleccionado(p.id)}>
                  <span className="punto-color" style={{ background: ESTADOS[p.estado_actual].color }} />
                  <span className="lista-nombre">{p.nombre}</span>
                  <span className="lista-meta">
                    {ESTADOS[p.estado_actual].texto}
                    {p.confirmado_en && ` · ${haceCuanto(p.confirmado_en)}`} · {textoDistancia(p.distancia)}
                  </span>
                </button>
              </li>
            ))}
            {!ordenados.length && <li className="vacio">No hay puntos con estos filtros. Prueba a quitar alguno.</li>}
          </ul>
        )}

        {seleccionado && (
          <FichaPunto
            id={seleccionado}
            miUbicacion={miUbicacion}
            onCerrar={() => setSeleccionado(null)}
            onCargada={alCargarFicha}
            onActualizado={cargarPuntos}
          />
        )}
      </div>
    </div>
  )
}

function Leyenda() {
  return (
    <div className="leyenda" aria-label="Leyenda">
      {Object.entries(ESTADOS).map(([clave, { texto, color }]) => (
        <span key={clave}><i style={{ background: color }} />{texto}</span>
      ))}
    </div>
  )
}
