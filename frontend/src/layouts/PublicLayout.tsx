import { Link, Outlet } from 'react-router-dom'
import { AdminNavLinks } from '../components/AdminNavLinks'
import { useAuth } from '../features/auth/context/AuthContext'

export function PublicLayout() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-lg font-semibold text-slate-900">
            Nền tảng chia sẻ học liệu
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/departments" className="text-sm text-slate-600 hover:text-slate-900">
              Duyệt theo khoa
            </Link>
            <Link to="/" className="text-sm text-slate-600 hover:text-slate-900">
              Trang chủ
            </Link>
            {user ? (
              <>
                <Link to="/me/resources" className="text-sm text-slate-600 hover:text-slate-900">
                  Tài liệu của tôi
                </Link>
                <Link to="/resources/create" className="text-sm text-slate-600 hover:text-slate-900">
                  Đóng góp tài liệu
                </Link>
                {isAdmin ? <AdminNavLinks /> : null}
                <span className="text-sm text-slate-700">{user.full_name}</span>
                <button onClick={logout} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  Đăng xuất
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                  Đăng nhập
                </Link>
                <Link to="/register" className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
