/**
 * Mapa interactivo con Leaflet + OpenStreetMap (sin claves ni cuotas).
 * Cada punto es un círculo del color de su estado actual.
 */

import { Fragment, useEffect } from 'react'
import { Circle, CircleMarker, MapContainer, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import { ESTADOS, ZOOM_INICIAL } from '../utils/formato'

const TILES_URL = import.meta.env.VITE_TILES_URL ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

/** Avisa al padre cuando el usuario mueve el mapa, con centro y radio visibles. */
function EscuchaMovimiento({ onMover }) {
  const mapa = useMapEvents({
    moveend: () => avisar(),
  })
  const avisar = () => {
    const centro = mapa.getCenter()
    const radioKm = centro.distanceTo(mapa.getBounds().getNorthEast()) / 1000
    onMover({ lat: centro.lat, lng: centro.lng, radioKm })
  }
  useEffect(avisar, []) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

function Recentrar({ centro }) {
  const mapa = useMap()
  useEffect(() => {
    if (centro) mapa.setView(centro, Math.max(mapa.getZoom(), ZOOM_INICIAL))
  }, [centro, mapa])
  return null
}

export default function MapaPuntos({ puntos, centroInicial, miUbicacion, seleccionado, onSeleccionar, onMover }) {
  return (
    <MapContainer center={centroInicial} zoom={ZOOM_INICIAL} className="mapa" zoomControl={false}>
      <TileLayer
        url={TILES_URL}
        maxZoom={19}
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      <EscuchaMovimiento onMover={onMover} />
      <Recentrar centro={miUbicacion} />

      {miUbicacion && (
        <CircleMarker center={miUbicacion} radius={7} pathOptions={{ color: '#fff', weight: 3, fillColor: '#2563eb', fillOpacity: 1 }}>
          <Tooltip>Estás aquí</Tooltip>
        </CircleMarker>
      )}

      {puntos.map((p) => {
        const { color, texto } = ESTADOS[p.estado_actual] ?? ESTADOS.sin_confirmar
        const elegido = seleccionado === p.id
        return (
          <Fragment key={p.id}>
            {p.ubicacion_aproximada && (
              <Circle
                center={[p.lat, p.lng]}
                radius={120}
                pathOptions={{ color, weight: 1, dashArray: '4 4', fillOpacity: 0.08 }}
                interactive={false}
              />
            )}
            <CircleMarker
              center={[p.lat, p.lng]}
              radius={elegido ? 14 : 10}
              pathOptions={{ color: '#fff', weight: 2, fillColor: color, fillOpacity: 0.95 }}
              className={`pin pin-${p.id}`}
              eventHandlers={{ click: () => onSeleccionar(p.id) }}
            >
              <Tooltip direction="top" offset={[0, -8]}>
                {p.nombre} · {texto}
              </Tooltip>
            </CircleMarker>
          </Fragment>
        )
      })}
    </MapContainer>
  )
}
