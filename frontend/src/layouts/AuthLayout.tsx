import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'
import { Spinner } from '../components/ui/Spinner'
import { PageTransition } from '../components/PageTransition'

/**
 * Layout for authentication pages (/login, /register).
 * - Shows loading spinner while auth state is resolving.
 * - Redirects to home page if already authenticated.
 * - Renders standalone full-screen auth layout if unauthenticated.
 */
export function AuthLayout() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f4f5fa]">
        <Spinner size="lg" />
      </div>
    )
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen bg-[#f4f5fa]">
      <PageTransition>
        <Outlet />
      </PageTransition>
    </div>
  )
}
