/**
 * Flujo 2 · Compartir un punto (y editarlo).
 * 1. Sesión iniciada (la ruta es privada).
 * 2. Colocar el pin en el mapa.
 * 3. Tipo, tomas, horario y acceso. Vivienda => ubicación aproximada.
 * 4. Enviar: queda "pendiente de revisión" (salvo usuarios de confianza).
 */

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/puntos'
import AsistenteIA from '../components/AsistenteIA'
import EditorHorarios, { agruparFranjas, aplanarFranjas } from '../components/EditorHorarios'
import SelectorUbicacion from '../components/SelectorUbicacion'
import { ACCESOS, CONECTORES, RESPALDOS, TIPOS } from '../utils/formato'

const VACIO = {
  nombre: '', tipo: 'negocio', descripcion: '', numero_tomas: 1, tipo_conector: 'enchufe',
  respaldo: 'ninguno', acceso: 'libre', contacto: '', ubicacion_aproximada: false,
}

export default function PuntoFormPage() {
  const { id } = useParams()
  const navegar = useNavigate()
  const [datos, setDatos] = useState(VACIO)
  const [ubicacion, setUbicacion] = useState(null)
  const [franjas, setFranjas] = useState([{ inicio: '08:00', fin: '18:00', dias: [0, 1, 2, 3, 4, 5, 6] }])
  const [iaHabilitada, setIaHabilitada] = useState(false)
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    api.config().then((c) => setIaHabilitada(c.ia_habilitada)).catch(() => {})
  }, [])

  // Modo edición: cargar el punto (el dueño recibe la ubicación exacta).
  useEffect(() => {
    if (!id) return
    api.obtenerPunto(id).then((p) => {
      setDatos({ ...VACIO, ...Object.fromEntries(Object.keys(VACIO).map((k) => [k, p[k] ?? VACIO[k]])) })
      setUbicacion({ lat: p.lat_exacta ?? p.lat, lng: p.lng_exacta ?? p.lng })
      setFranjas(agruparFranjas(p.horarios))
    }).catch((e) => setError(e.message))
  }, [id])

  const campo = (nombre) => ({
    name: nombre,
    value: datos[nombre],
    onChange: (e) => setDatos({ ...datos, [nombre]: e.target.type === 'number' ? Number(e.target.value) : e.target.value }),
  })
  const esVivienda = datos.tipo === 'vivienda'

  const aplicarBorrador = (borrador) => {
    const { horarios, ...resto } = borrador
    setDatos((actual) => ({ ...actual, ...resto }))
    if (horarios?.length) setFranjas(agruparFranjas(horarios))
  }

  const enviar = async (e) => {
    e.preventDefault()
    if (!ubicacion) return setError('Coloca el pin en el mapa.')
    setEnviando(true)
    setError(null)
    const cuerpo = {
      ...datos,
      ubicacion_aproximada: esVivienda || datos.ubicacion_aproximada,
      lat: Number(ubicacion.lat.toFixed(6)),
      lng: Number(ubicacion.lng.toFixed(6)),
      horarios: aplanarFranjas(franjas),
    }
    try {
      const punto = id ? await api.editarPunto(id, cuerpo) : await api.crearPunto(cuerpo)
      navegar('/mis-puntos', { state: { recienCreado: punto.id, estado: punto.estado_publicacion } })
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="pagina formulario" onSubmit={enviar}>
      <h1>{id ? 'Editar punto' : 'Agregar un punto de carga'}</h1>

      {iaHabilitada && !id && <AsistenteIA onBorrador={aplicarBorrador} />}

      <label>
        Nombre del lugar
        <input {...campo('nombre')} required minLength={3} maxLength={120} placeholder="Cafetería El Portal" />
      </label>

      <label>
        Tipo de lugar
        <select {...campo('tipo')}>
          {Object.entries(TIPOS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </label>

      <fieldset>
        <legend>Ubicación</legend>
        <SelectorUbicacion valor={ubicacion} onCambio={setUbicacion} />
        {esVivienda ? (
          <p className="nota">🔒 Es una vivienda: se mostrará con <strong>ubicación aproximada</strong> (unos 200 m) para no exponer tu dirección.</p>
        ) : (
          <label className="casilla">
            <input
              type="checkbox"
              checked={datos.ubicacion_aproximada}
              onChange={(e) => setDatos({ ...datos, ubicacion_aproximada: e.target.checked })}
            />
            Mostrar solo una ubicación aproximada
          </label>
        )}
        <label>
          Referencias para llegar
          <textarea {...campo('descripcion')} rows={2} maxLength={500} placeholder='"Frente al parque, portal azul"' />
        </label>
      </fieldset>

      <div className="dos-columnas">
        <label>
          Número de tomas
          <input type="number" min={1} max={50} {...campo('numero_tomas')} />
        </label>
        <label>
          Conector
          <select {...campo('tipo_conector')}>
            {Object.entries(CONECTORES).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </label>
        <label>
          Respaldo
          <select {...campo('respaldo')}>
            {Object.entries(RESPALDOS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </label>
        <label>
          Acceso
          <select {...campo('acceso')}>
            {Object.entries(ACCESOS).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </label>
      </div>

      <fieldset>
        <legend>Horario</legend>
        <EditorHorarios franjas={franjas} onCambio={setFranjas} />
      </fieldset>

      <label>
        Contacto (opcional)
        <input {...campo('contacto')} maxLength={120} placeholder="Teléfono o cómo avisar" />
        <small>No se muestra en la ficha: solo lo ve quien lo pida estando registrado.</small>
      </label>

      {error && <p className="mensaje error">{error}</p>}
      <button className="boton primario ancho" disabled={enviando}>
        {enviando ? 'Enviando…' : id ? 'Guardar cambios' : 'Enviar punto'}
      </button>
      <p className="nota">Los puntos nuevos pasan por una revisión rápida antes de aparecer en el mapa.</p>
    </form>
  )
}
