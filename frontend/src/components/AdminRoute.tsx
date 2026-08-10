import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'

type AdminRouteProps = {
  children: React.ReactElement
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <div className="p-6 text-slate-600">Đang kiểm tra quyền admin...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (user.role !== 'ADMIN') {
    return <Navigate to="/" replace />
  }

  return children
}
