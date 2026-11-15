/**
 * Editor de horarios. Para no obligar a rellenar 7 filas, se elige una franja
 * y los días con atajos (todos, lunes a viernes, fin de semana).
 * Se pueden añadir varias franjas.
 */

import { DIAS } from '../utils/formato'

const ATAJOS = { 'Todos': [0, 1, 2, 3, 4, 5, 6], 'L–V': [0, 1, 2, 3, 4], 'Fin de semana': [5, 6] }

/** Convierte la lista plana de la API en franjas editables y viceversa. */
export function agruparFranjas(horarios = []) {
  const mapa = new Map()
  for (const h of horarios) {
    const clave = `${h.hora_inicio.slice(0, 5)}-${h.hora_fin.slice(0, 5)}`
    const franja = mapa.get(clave) ?? { inicio: h.hora_inicio.slice(0, 5), fin: h.hora_fin.slice(0, 5), dias: [] }
    franja.dias.push(h.dia_semana)
    mapa.set(clave, franja)
  }
  return [...mapa.values()]
}

export function aplanarFranjas(franjas) {
  return franjas.flatMap((f) => f.dias.map((dia_semana) => ({ dia_semana, hora_inicio: f.inicio, hora_fin: f.fin })))
}

export default function EditorHorarios({ franjas, onCambio }) {
  const actualizar = (i, cambios) => onCambio(franjas.map((f, j) => (j === i ? { ...f, ...cambios } : f)))
  const alternarDia = (i, dia) => {
    const dias = new Set(franjas[i].dias)
    dias.has(dia) ? dias.delete(dia) : dias.add(dia)
    actualizar(i, { dias: [...dias].sort() })
  }

  return (
    <div className="editor-horarios">
      {franjas.map((f, i) => (
        <fieldset key={i} className="franja">
          <legend>Franja {i + 1}</legend>
          <div className="fila">
            <label>De <input type="time" value={f.inicio} onChange={(e) => actualizar(i, { inicio: e.target.value })} required /></label>
            <label>a <input type="time" value={f.fin} onChange={(e) => actualizar(i, { fin: e.target.value })} required /></label>
            <button type="button" className="enlace" onClick={() => onCambio(franjas.filter((_, j) => j !== i))}>Quitar</button>
          </div>
          <div className="dias">
            {DIAS.map((nombre, dia) => (
              <button
                type="button"
                key={dia}
                className={`chip pequeno ${f.dias.includes(dia) ? 'activo' : ''}`}
                aria-pressed={f.dias.includes(dia)}
                onClick={() => alternarDia(i, dia)}
              >
                {nombre.slice(0, 2)}
              </button>
            ))}
            {Object.entries(ATAJOS).map(([texto, dias]) => (
              <button type="button" key={texto} className="enlace" onClick={() => actualizar(i, { dias })}>{texto}</button>
            ))}
          </div>
        </fieldset>
      ))}
      <button
        type="button"
        className="boton secundario"
        onClick={() => onCambio([...franjas, { inicio: '08:00', fin: '18:00', dias: ATAJOS.Todos }])}
      >
        + Añadir franja horaria
      </button>
      <small>Si la hora de fin es menor que la de inicio, la franja cruza la medianoche. 00:00 a 00:00 = todo el día.</small>
    </div>
  )
}
