import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, type AuthUser } from '../api'
import { getStoredToken, setStoredToken, clearStoredToken } from '../tokenStorage'

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  loginWithGoogle: (credential: string, rememberMe?: boolean) => Promise<void>
  register: (email: string, full_name: string, password: string) => Promise<void>
  refreshUser: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(getStoredToken())
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      const storedToken = getStoredToken()
      if (!storedToken) {
        setIsLoading(false)
        return
      }

      try {
        const currentUser = await authApi.me()
        setUser(currentUser)
        setToken(storedToken)
      } catch {
        clearStoredToken()
        setToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    void loadUser()
  }, [])

  const login = async (email: string, password: string, rememberMe: boolean = false) => {
    const response = await authApi.login({ email, password })
    setStoredToken(response.access_token, rememberMe)
    setToken(response.access_token)
    setUser(response.user)
  }

  const loginWithGoogle = async (credential: string, rememberMe: boolean = false) => {
    const response = await authApi.googleLogin({ credential })
    setStoredToken(response.access_token, rememberMe)
    setToken(response.access_token)
    setUser(response.user)
  }

  const register = async (email: string, full_name: string, password: string) => {
    const response = await authApi.register({ email, full_name, password })
    setStoredToken(response.access_token, true)
    setToken(response.access_token)
    setUser(response.user)
  }

  const refreshUser = async () => {
    try {
      const currentUser = await authApi.me()
      setUser(currentUser)
    } catch {
      // Giữ nguyên state nếu refresh lỗi
    }
  }

  const logout = () => {
    clearStoredToken()
    setToken(null)
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, isLoading, login, loginWithGoogle, register, refreshUser, logout }),
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
