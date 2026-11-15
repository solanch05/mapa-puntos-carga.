/**
 * Cliente HTTP de la API.
 *
 * - Añade el token JWT de acceso a cada petición.
 * - Si el token caducó (401), usa el token de refresco UNA vez y repite.
 * - Convierte los errores de DRF en un mensaje legible.
 */

const BASE = import.meta.env.VITE_API_URL ?? '/api'
const CLAVE_TOKENS = 'mpc.tokens'

export const tokens = {
  leer() {
    try {
      return JSON.parse(localStorage.getItem(CLAVE_TOKENS)) ?? {}
    } catch {
      return {}
    }
  },
  guardar(t) {
    localStorage.setItem(CLAVE_TOKENS, JSON.stringify(t))
  },
  borrar() {
    localStorage.removeItem(CLAVE_TOKENS)
  },
}

export class ErrorApi extends Error {
  constructor(status, cuerpo) {
    super(mensajeDeError(cuerpo) || `Error ${status}`)
    this.status = status
    this.cuerpo = cuerpo
  }
}

/** Errores de conexión (sin internet): el llamador puede encolar la acción. */
export class ErrorConexion extends Error {}

function mensajeDeError(cuerpo) {
  if (!cuerpo) return ''
  if (typeof cuerpo === 'string') return cuerpo
  if (cuerpo.detail) return cuerpo.detail
  return Object.entries(cuerpo)
    .map(([campo, valor]) => {
      const texto = Array.isArray(valor) ? valor.join(' ') : typeof valor === 'object' ? mensajeDeError(valor) : valor
      return campo === 'non_field_errors' || campo === 'detalle' ? texto : `${campo}: ${texto}`
    })
    .join(' · ')
}

let refrescando = null

async function refrescarToken() {
  const { refresh } = tokens.leer()
  if (!refresh) return false
  // Si varias peticiones caducan a la vez, solo se refresca una vez.
  refrescando ??= fetch(`${BASE}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
    .then(async (r) => {
      if (!r.ok) return false
      const nuevos = await r.json()
      tokens.guardar({ ...tokens.leer(), ...nuevos })
      return true
    })
    .catch(() => false)
    .finally(() => {
      refrescando = null
    })
  return refrescando
}

export async function peticion(ruta, { metodo = 'GET', datos, formData, params, reintentar = true } = {}) {
  const url = new URL(`${BASE}${ruta}`, window.location.origin)
  Object.entries(params ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== false) url.searchParams.set(k, v)
  })

  const headers = {}
  const { access } = tokens.leer()
  if (access) headers.Authorization = `Bearer ${access}`
  let body
  if (formData) body = formData
  else if (datos !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(datos)
  }

  let respuesta
  try {
    respuesta = await fetch(url, { method: metodo, headers, body })
  } catch {
    throw new ErrorConexion('Sin conexión con el servidor')
  }

  if (respuesta.status === 401 && reintentar && (await refrescarToken())) {
    return peticion(ruta, { metodo, datos, formData, params, reintentar: false })
  }
  if (respuesta.status === 401 && access) {
    tokens.borrar() // sesión caducada del todo
    window.dispatchEvent(new Event('sesion-caducada'))
  }

  const tipo = respuesta.headers.get('content-type') ?? ''
  const cuerpo = tipo.includes('application/json') ? await respuesta.json() : null
  if (!respuesta.ok) throw new ErrorApi(respuesta.status, cuerpo)
  return cuerpo
}
