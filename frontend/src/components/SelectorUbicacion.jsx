/**
 * Colocar el pin a mano (sección 8: el mapa base puede estar incompleto,
 * así que no dependemos de buscar direcciones). Tocar el mapa mueve el pin.
 */

import { CircleMarker, MapContainer, TileLayer, useMapEvents } from 'react-leaflet'
import { CENTRO_PILOTO } from '../utils/formato'

const TILES_URL = import.meta.env.VITE_TILES_URL ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

function AlTocar({ onElegir }) {
  useMapEvents({ click: (e) => onElegir({ lat: e.latlng.lat, lng: e.latlng.lng }) })
  return null
}

export default function SelectorUbicacion({ valor, onCambio }) {
  const centro = valor ? [valor.lat, valor.lng] : CENTRO_PILOTO

  const usarMiUbicacion = () =>
    navigator.geolocation?.getCurrentPosition((pos) =>
      onCambio({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
    )

  return (
    <div className="selector-ubicacion">
      <div data-testid="selector-ubicacion">
      <MapContainer center={centro} zoom={16} className="mapa-pequeno">
        <TileLayer url={TILES_URL} attribution="&copy; OpenStreetMap" />
        <AlTocar onElegir={onCambio} />
        {valor && (
          <CircleMarker
            center={[valor.lat, valor.lng]}
            radius={11}
            pathOptions={{ color: '#fff', weight: 3, fillColor: '#2563eb', fillOpacity: 1 }}
          />
        )}
      </MapContainer>
      </div>
      <div className="fila">
        <small>{valor ? `Pin en ${valor.lat.toFixed(5)}, ${valor.lng.toFixed(5)}` : 'Toca el mapa para colocar el pin.'}</small>
        <button type="button" className="enlace" onClick={usarMiUbicacion}>Usar mi ubicación</button>
      </div>
    </div>
  )
}
