import { TIPOS } from '../utils/formato'

/**
 * Filtros del mapa (sección 4): con energía ahora, abierto ahora, tipo de
 * punto y número mínimo de tomas.
 */
export default function Filtros({ filtros, onCambio }) {
  const cambiar = (campo, valor) => onCambio({ ...filtros, [campo]: valor })
  const alternarTipo = (tipo) => {
    const actuales = new Set(filtros.tipos)
    actuales.has(tipo) ? actuales.delete(tipo) : actuales.add(tipo)
    cambiar('tipos', [...actuales])
  }

  return (
    <div className="filtros" role="group" aria-label="Filtros">
      <button
        className={`chip ${filtros.conEnergia ? 'activo verde' : ''}`}
        aria-pressed={filtros.conEnergia}
        onClick={() => cambiar('conEnergia', !filtros.conEnergia)}
      >
        ⚡ Con energía ahora
      </button>
      <button
        className={`chip ${filtros.abiertoAhora ? 'activo' : ''}`}
        aria-pressed={filtros.abiertoAhora}
        onClick={() => cambiar('abiertoAhora', !filtros.abiertoAhora)}
      >
        🕒 Abierto ahora
      </button>
      {Object.entries(TIPOS).map(([valor, texto]) => (
        <button
          key={valor}
          className={`chip ${filtros.tipos.includes(valor) ? 'activo' : ''}`}
          aria-pressed={filtros.tipos.includes(valor)}
          onClick={() => alternarTipo(valor)}
        >
          {texto}
        </button>
      ))}
      <label className="chip selector">
        Tomas
        <select value={filtros.minTomas} onChange={(e) => cambiar('minTomas', Number(e.target.value))}>
          <option value={0}>todas</option>
          <option value={2}>2+</option>
          <option value={4}>4+</option>
          <option value={6}>6+</option>
        </select>
      </label>
    </div>
  )
}
