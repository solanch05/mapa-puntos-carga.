/**
 * Estado de sesión compartido por toda la app.
 * Guarda los tokens en localStorage y expone usuario, login, registro, logout.
 */

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { tokens } from '../api/cliente'
import { api } from '../api/puntos'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(tokens.leer().access))

  const refrescarUsuario = useCallback(async () => {
    if (!tokens.leer().access) return setUsuario(null)
    try {
      setUsuario(await api.yo())
    } catch {
      setUsuario(null)
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    refrescarUsuario()
    const alCaducar = () => setUsuario(null)
    window.addEventListener('sesion-caducada', alCaducar)
    return () => window.removeEventListener('sesion-caducada', alCaducar)
  }, [refrescarUsuario])

  const login = async (email, password) => {
    tokens.guardar(await api.login({ email, password }))
    await refrescarUsuario()
  }

  const registro = async (datos) => {
    const { access, refresh, usuario: nuevo } = await api.registro(datos)
    tokens.guardar({ access, refresh })
    setUsuario(nuevo)
  }

  const logout = async () => {
    const { refresh } = tokens.leer()
    try {
      if (refresh) await api.logout(refresh)
    } finally {
      tokens.borrar()
      setUsuario(null)
    }
  }

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, registro, logout, refrescarUsuario }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
