/**
 * Cola de reportes sin conexión (sección 8: "Los reportes se envían cuando
 * vuelve la señal").
 *
 * Si al reportar no hay conexión, el reporte se guarda en el teléfono y se
 * envía solo cuando el navegador avisa de que hay red (evento "online").
 * Las fotos no se encolan: ocupan demasiado para guardarlas en el teléfono.
 */

import { ErrorApi, ErrorConexion, peticion } from './cliente'

const CLAVE = 'mpc.cola-reportes'

function leer() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) ?? []
  } catch {
    return []
  }
}

function guardar(cola) {
  localStorage.setItem(CLAVE, JSON.stringify(cola))
  window.dispatchEvent(new CustomEvent('cola-cambio', { detail: cola.length }))
}

export function pendientes() {
  return leer().length
}

export function encolarReporte({ puntoId, estado, comentario }) {
  guardar([...leer(), { puntoId, estado, comentario: comentario ?? '', encoladoEn: new Date().toISOString() }])
}

let procesando = false

export async function procesarCola() {
  if (procesando || !navigator.onLine) return
  procesando = true
  try {
    let cola = leer()
    while (cola.length) {
      const [primero, ...resto] = cola
      try {
        await peticion(`/puntos/${primero.puntoId}/reportes/`, {
          metodo: 'POST',
          datos: { estado: primero.estado, comentario: primero.comentario },
        })
      } catch (error) {
        if (error instanceof ErrorConexion) break // sigue sin red: lo intentamos luego
        if (!(error instanceof ErrorApi)) break
        // Error de la API (punto retirado, límite...): se descarta ese reporte.
      }
      cola = resto
      guardar(cola)
    }
  } finally {
    procesando = false
  }
}

export function iniciarColaOffline() {
  window.addEventListener('online', procesarCola)
  procesarCola()
}
