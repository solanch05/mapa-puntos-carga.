/** Funciones de la API agrupadas por recurso. Las páginas solo usan estas. */

import { ErrorConexion, peticion } from './cliente'
import { encolarReporte } from './colaOffline'

const CLAVE_ULTIMA = 'mpc.ultima-consulta'

export const api = {
  config: () => peticion('/config/'),

  /**
   * Lista de puntos para el mapa. Guarda la última respuesta en el teléfono
   * para enseñarla sin conexión con su hora ("último estado conocido").
   */
  async listarPuntos(filtros) {
    try {
      const datos = await peticion('/puntos/', { params: filtros })
      localStorage.setItem(CLAVE_ULTIMA, JSON.stringify({ guardadoEn: new Date().toISOString(), puntos: datos.results }))
      return { puntos: datos.results, sinConexion: false }
    } catch (error) {
      if (!(error instanceof ErrorConexion)) throw error
      const guardado = JSON.parse(localStorage.getItem(CLAVE_ULTIMA) ?? 'null')
      return { puntos: guardado?.puntos ?? [], sinConexion: true, guardadoEn: guardado?.guardadoEn }
    }
  },
  obtenerPunto: (id) => peticion(`/puntos/${id}/`),
  crearPunto: (datos) => peticion('/puntos/', { metodo: 'POST', datos }),
  editarPunto: (id, datos) => peticion(`/puntos/${id}/`, { metodo: 'PATCH', datos }),
  retirarPunto: (id) => peticion(`/puntos/${id}/`, { metodo: 'DELETE' }),
  pausarPunto: (id) => peticion(`/puntos/${id}/pausar/`, { metodo: 'POST' }),
  misPuntos: () => peticion('/puntos/mios/'),
  pedirContacto: (id) => peticion(`/puntos/${id}/contacto/`, { metodo: 'POST' }),
  marcarFavorito: (id, marcar) => peticion(`/puntos/${id}/favorito/`, { metodo: marcar ? 'POST' : 'DELETE' }),
  favoritos: () => peticion('/favoritos/'),

  /** Reporte en un toque. Sin conexión (y sin foto) se encola y se envía luego. */
  async reportarEstado(id, { estado, comentario, foto }) {
    const formData = new FormData()
    formData.append('estado', estado)
    if (comentario) formData.append('comentario', comentario)
    if (foto) formData.append('foto', foto)
    try {
      return await peticion(`/puntos/${id}/reportes/`, { metodo: 'POST', formData })
    } catch (error) {
      if (error instanceof ErrorConexion && !foto) {
        encolarReporte({ puntoId: id, estado, comentario })
        return { encolado: true }
      }
      throw error
    }
  },

  denunciar: (datos) => peticion('/denuncias/', { metodo: 'POST', datos }),
  borradorIA: (texto) => peticion('/ia/borrador/', { metodo: 'POST', datos: { texto } }),

  // Autenticación
  registro: (datos) => peticion('/auth/registro/', { metodo: 'POST', datos }),
  login: (datos) => peticion('/auth/token/', { metodo: 'POST', datos, reintentar: false }),
  logout: (refresh) => peticion('/auth/logout/', { metodo: 'POST', datos: { refresh } }),
  yo: () => peticion('/auth/yo/'),
}
