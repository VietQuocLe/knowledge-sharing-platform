import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

type User = {
  id: string
  email: string
}

type AuthContextValue = {
  user: User | null
  login: (email: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  const login = (email: string) => {
    setUser({
      id: `${Date.now()}`,
      email,
    })
  }

  const logout = () => {
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, login, logout }),
    [user],
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
