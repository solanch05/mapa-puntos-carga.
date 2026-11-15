/** Textos, colores y utilidades de presentación compartidas. */

export const CENTRO_PILOTO = [22.4067, -79.9646] // centro de Santa Clara
export const ZOOM_INICIAL = 15

export const ESTADOS = {
  con_energia: { texto: 'Con energía', color: '#16a34a' },
  sin_energia: { texto: 'Sin energía', color: '#dc2626' },
  lleno: { texto: 'Lleno', color: '#ea580c' },
  cerrado: { texto: 'Cerrado', color: '#6b7280' },
  sin_confirmar: { texto: 'Sin confirmar', color: '#94a3b8' },
}

export const TIPOS = {
  vivienda: 'Vivienda',
  negocio: 'Negocio',
  institucion: 'Institución',
  espacio_publico: 'Espacio público',
}

export const ACCESOS = {
  libre: 'Libre',
  con_consumo: 'Con consumo',
  previa_solicitud: 'Previa solicitud',
  pago: 'De pago',
}

export const RESPALDOS = {
  ninguno: 'Red eléctrica',
  bateria: 'Batería',
  planta: 'Planta eléctrica',
  solar: 'Paneles solares',
}

export const CONECTORES = { enchufe: 'Enchufe', usb: 'USB', ambos: 'Enchufe y USB' }

export const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

export const PUBLICACION = {
  pendiente: { texto: 'Pendiente de revisión', clase: 'aviso' },
  activo: { texto: 'Publicado', clase: 'ok' },
  pausado: { texto: 'Pausado', clase: 'neutro' },
  oculto: { texto: 'Oculto por moderación', clase: 'error' },
}

/** "hace 12 min", "hace 2 h", "hace 3 días" */
export function haceCuanto(fecha) {
  if (!fecha) return ''
  const minutos = Math.max(0, Math.round((Date.now() - new Date(fecha).getTime()) / 60000))
  if (minutos < 1) return 'hace un momento'
  if (minutos < 60) return `hace ${minutos} min`
  const horas = Math.round(minutos / 60)
  if (horas < 24) return `hace ${horas} h`
  return `hace ${Math.round(horas / 24)} días`
}

export function hora(fecha) {
  return new Date(fecha).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })
}

/** Distancia en metros entre dos puntos [lat, lng] (fórmula del haversine). */
export function distanciaM([lat1, lng1], [lat2, lng2]) {
  const R = 6371000
  const rad = (g) => (g * Math.PI) / 180
  const a =
    Math.sin(rad(lat2 - lat1) / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lng2 - lng1) / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(a))
}

export function textoDistancia(metros) {
  if (metros == null) return ''
  return metros < 1000 ? `${Math.round(metros / 10) * 10} m` : `${(metros / 1000).toFixed(1)} km`
}

/** Abre la ruta a pie en la app de mapas del teléfono. */
export function urlComoLlegar(lat, lng) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=walking`
}

/** Agrupa horarios por franja: "Lunes a Viernes · 09:00–17:00". */
export function resumirHorarios(horarios) {
  if (!horarios?.length) return ['Sin horario indicado']
  const franjas = new Map()
  for (const h of horarios) {
    const clave = `${h.hora_inicio.slice(0, 5)}–${h.hora_fin.slice(0, 5)}`
    franjas.set(clave, [...(franjas.get(clave) ?? []), h.dia_semana])
  }
  return [...franjas].map(([franja, dias]) => {
    const texto = franja === '00:00–00:00' ? 'todo el día' : franja
    return `${nombrarDias(dias)} · ${texto}`
  })
}

function nombrarDias(dias) {
  const ordenados = [...new Set(dias)].sort()
  if (ordenados.length === 7) return 'Todos los días'
  const consecutivos = ordenados.every((d, i) => i === 0 || d === ordenados[i - 1] + 1)
  if (consecutivos && ordenados.length > 2) return `${DIAS[ordenados[0]]} a ${DIAS[ordenados.at(-1)]}`
  return ordenados.map((d) => DIAS[d]).join(', ')
}
