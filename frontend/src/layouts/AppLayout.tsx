import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'

export function AppLayout() {
  const isAdmin = useAuth().user?.role === 'ADMIN'

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
        <aside className="w-64 shrink-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Tài nguyên của bạn</h2>
          <nav className="space-y-2 text-sm">
            <Link to="/me/resources" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
              Tài liệu của tôi
            </Link>
            {/* [PAUSED - Admin branch] Contribution link hidden until re-activated
            <Link to="/resources/create" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
              Đóng góp tài liệu
            </Link>
            */}
            {isAdmin ? (
              <>
                <div className="my-3 border-t border-slate-200" />
                <p className="px-3 text-xs font-medium uppercase tracking-wide text-slate-500">Quản trị</p>
                <Link to="/admin/moderation" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
                  Kiểm duyệt
                </Link>
                <Link to="/admin/taxonomy" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
                  Phân loại
                </Link>
              </>
            ) : null}
          </nav>
        </aside>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
