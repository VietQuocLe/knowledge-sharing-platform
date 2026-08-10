import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, type AuthUser } from '../api'

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, full_name: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      const storedToken = localStorage.getItem('access_token')
      if (!storedToken) {
        setIsLoading(false)
        return
      }

      try {
        const currentUser = await authApi.me()
        setUser(currentUser)
        setToken(storedToken)
      } catch {
        localStorage.removeItem('access_token')
        setToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    void loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authApi.login({ email, password })
    localStorage.setItem('access_token', response.access_token)
    setToken(response.access_token)
    setUser(response.user)
  }

  const register = async (email: string, full_name: string, password: string) => {
    const response = await authApi.register({ email, full_name, password })
    localStorage.setItem('access_token', response.access_token)
    setToken(response.access_token)
    setUser(response.user)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, isLoading, login, register, logout }),
    [isLoading, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
