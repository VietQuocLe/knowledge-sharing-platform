import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'

type ProtectedRouteProps = {
  children: React.ReactElement
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <div className="p-6 text-slate-600">Đang kiểm tra đăng nhập...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}
