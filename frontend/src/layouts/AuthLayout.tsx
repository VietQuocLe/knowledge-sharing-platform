import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'
import { Spinner } from '../components/ui/Spinner'
import { PageTransition } from '../components/PageTransition'

/**
 * Layout cho các trang xác thực (/login, /register).
 * - Nếu đang kiểm tra auth (isLoading): hiển thị spinner.
 * - Nếu đã đăng nhập: redirect ngay về trang chủ.
 * - Nếu chưa đăng nhập: render trang auth toàn màn hình (không có sidebar).
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
