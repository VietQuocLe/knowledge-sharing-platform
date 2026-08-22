import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { FileText, Tags, Menu, X } from 'lucide-react'
import { useAuth } from '../features/auth/context/AuthContext'

export function AppLayout() {
  const isAdmin = useAuth().user?.role === 'ADMIN'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const handleLinkClick = () => {
    setIsSidebarOpen(false)
  }

  const navContent = (
    <>
      <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Tài nguyên của bạn
      </h2>
      <nav className="space-y-1 text-sm font-medium">
        <Link
          to="/me/resources"
          onClick={handleLinkClick}
          className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
        >
          <FileText className="h-4 w-4 text-slate-400" />
          Tài liệu của tôi
        </Link>
        {/* [PAUSED - Admin branch] Contribution link hidden until re-activated
        <Link to="/resources/create" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100">
          Đóng góp tài liệu
        </Link>
        */}
        {isAdmin ? (
          <>
            <div className="my-4 border-t border-slate-200" />
            <p className="px-3 mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Quản trị
            </p>
            {/* [PAUSED - Admin branch] Moderation path commented out in Router
            <Link
              to="/admin/moderation"
              onClick={handleLinkClick}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <ShieldCheck className="h-4 w-4 text-slate-400" />
              Kiểm duyệt
            </Link>
            */}
            <Link
              to="/admin/taxonomy"
              onClick={handleLinkClick}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <Tags className="h-4 w-4 text-slate-400" />
              Phân loại
            </Link>
          </>
        ) : null}
      </nav>
    </>
  )

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-7xl flex-col md:flex-row gap-6 px-4 sm:px-6 lg:px-8 py-6 md:py-8">

        {/* Mobile Sidebar Toggle Button */}
        <div className="flex items-center justify-between md:hidden rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <span className="text-sm font-bold text-slate-900">Danh mục quản lý</span>
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="inline-flex items-center justify-center rounded-lg border border-slate-300 p-2 text-slate-700 bg-slate-50 hover:bg-slate-100"
            aria-expanded={isSidebarOpen}
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Sidebar Drawer Menu */}
        {isSidebarOpen && (
          <div className="md:hidden rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            {navContent}
          </div>
        )}

        {/* Desktop Sidebar */}
        <aside className="hidden md:block w-64 shrink-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sticky top-24 self-start">
          {navContent}
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
