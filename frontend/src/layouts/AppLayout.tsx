import { Link, Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
        <aside className="w-64 shrink-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Tài nguyên của bạn</h2>
          <nav className="space-y-2 text-sm">
            <Link to="/me/resources" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
              Tài nguyên của tôi
            </Link>
            <Link to="/resources/new" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
              Tạo tài nguyên mới
            </Link>
            <Link to="/resources/1/upload" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
              Upload tài liệu
            </Link>
          </nav>
        </aside>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
