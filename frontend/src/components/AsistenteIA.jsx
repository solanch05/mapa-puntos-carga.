/**
 * Extra del demo · Alta asistida con IA.
 * 1. Pegas un mensaje ("hay corriente en casa de Pedro, de 6 a 10 de la noche, dos enchufes").
 * 2. El servidor devuelve un BORRADOR con los campos rellenados.
 * 3. Tú corriges y confirmas. Nada se publica sin esa confirmación.
 */

import { useState } from 'react'
import { api } from '../api/puntos'

export default function AsistenteIA({ onBorrador }) {
  const [texto, setTexto] = useState('')
  const [estado, setEstado] = useState(null)
  const [cargando, setCargando] = useState(false)

  const generar = async () => {
    setCargando(true)
    setEstado(null)
    try {
      const { borrador, avisos, origen } = await api.borradorIA(texto)
      onBorrador(borrador)
      setEstado({ avisos, origen })
    } catch (error) {
      setEstado({ error: error.message })
    } finally {
      setCargando(false)
    }
  }

  return (
    <section className="asistente">
      <h3>✨ Rellenar a partir de un mensaje</h3>
      <p className="nota">Pega el aviso tal como lo escribirías en un grupo. Te proponemos los campos y tú los revisas.</p>
      <textarea
        rows={3}
        maxLength={600}
        placeholder="hay corriente en casa de Pedro, de 6 a 10 de la noche, dos enchufes"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      <button type="button" className="boton secundario" disabled={cargando || texto.trim().length < 10} onClick={generar}>
        {cargando ? 'Analizando…' : 'Generar borrador'}
      </button>
      {estado?.error && <p className="mensaje error">{estado.error}</p>}
      {estado?.avisos && (
        <div className="mensaje aviso">
          <strong>Borrador listo{estado.origen === 'reglas' ? ' (extractor sin conexión)' : ''}. Revisa:</strong>
          <ul>{estado.avisos.map((a) => <li key={a}>{a}</li>)}</ul>
        </div>
      )}
    </section>
  )
}
