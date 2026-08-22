import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { GraduationCap, Home, FolderGit2, PlusCircle, LogIn, LogOut, UserPlus, Menu, X } from 'lucide-react'
import { AdminNavLinks } from '../components/AdminNavLinks'
import { useAuth } from '../features/auth/context/AuthContext'
import { SubjectSearchInput } from '../features/taxonomy'

export function PublicLayout() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const contributeUrl = import.meta.env.VITE_CONTRIBUTE_FORM_URL

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen)
  const closeMobileMenu = () => setIsMobileMenuOpen(false)

  const handleLogout = () => {
    logout()
    setIsMobileMenuOpen(false)
  }

  // Style cho nav link active ở sidebar
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${isActive
      ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
    }`

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans antialiased text-slate-800">
      {/* ========================================================= */}
      {/* 1. DESKTOP LEFT SIDEBAR (Cố định chiều dài h-screen)        */}
      {/* ========================================================= */}
      <aside className="hidden md:flex w-64 flex-col justify-between border-r border-slate-200 bg-white p-5 sticky top-0 h-screen z-30">
        <div className="space-y-6">
          {/* Logo & Tên dự án */}
          <Link to="/" className="flex items-center gap-3 px-2 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm transition group-hover:bg-slate-800">
              <GraduationCap className="h-5 w-5" />
            </div>
            <span className="text-base font-bold tracking-tight text-slate-900">
              HCMC-VAULT
            </span>
          </Link>

          {/* Menu Điều hướng */}
          <nav className="space-y-1">
            <NavLink to="/" end className={navLinkClass}>
              <Home className="h-4 w-4" />
              <span>Home</span>
            </NavLink>
            {user && (
              <NavLink to="/me/resources" className={navLinkClass}>
                <FolderGit2 className="h-4 w-4" />
                <span>Workspace</span>
              </NavLink>
            )}
            {isAdmin && (
              <div className="pt-3 mt-3 border-t border-slate-100 px-1">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Quản trị
                </p>
                <AdminNavLinks />
              </div>
            )}
          </nav>
        </div>

        {/* Box CTA Google Form ở đáy Sidebar */}
        {contributeUrl && (
          <div className="rounded-2xl bg-indigo-50/70 border border-indigo-100 p-4 text-center">
            <p className="text-[11px] text-slate-500 mb-3 leading-relaxed">
              Cùng xây dựng kho tài liệu chất lượng cho sinh viên.
            </p>
            <a
              href={contributeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-1.5 w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              Đóng góp tài liệu
            </a>
          </div>
        )}
      </aside>

      {/* ========================================================= */}
      {/* 2. KHU VỰC CHÍNH BÊN PHẢI (Topbar + Main Content)          */}
      {/* ========================================================= */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-20 h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          {/* Trái (Mobile): Nút Hamburger + Logo */}
          <div className="flex items-center gap-3 md:hidden">
            <button
              type="button"
              onClick={toggleMobileMenu}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 focus:outline-none"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
            <span className="font-bold text-slate-900 text-sm">Chia sẻ học liệu</span>
          </div>

          {/* Giữa (Desktop): Thanh tìm kiếm */}
          <div className="hidden md:block w-full max-w-md">
            <SubjectSearchInput />
          </div>

          {/* Phải: Auth Controls */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-slate-700 hidden sm:inline-block">
                  {user.full_name || user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-rose-600 transition"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Đăng xuất
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                >
                  <LogIn className="h-3.5 w-3.5" />
                  Đăng nhập
                </Link>
                <Link
                  to="/register"
                  className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 shadow-xs transition"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </header>

        {/* Drawer Menu cho Mobile */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-b border-slate-200 bg-white px-4 py-4 space-y-2 shadow-lg">
            <Link
              to="/"
              onClick={closeMobileMenu}
              className="block rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Trang chủ
            </Link>
            <Link
              to="/departments"
              onClick={closeMobileMenu}
              className="block rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Khoa & Ngành
            </Link>
            {contributeUrl && (
              <a
                href={contributeUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={closeMobileMenu}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-indigo-700 bg-indigo-50"
              >
                <PlusCircle className="h-4 w-4" />
                Đóng góp tài liệu
              </a>
            )}
          </div>
        )}

        {/* Vùng render nội dung từng trang */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}