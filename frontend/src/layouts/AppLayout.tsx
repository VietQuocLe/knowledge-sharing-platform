import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  GraduationCap,
  Home,
  BookOpen,
  Tags,
  LogOut,
  Menu,
  X,
  PanelLeftClose,
  ArrowLeft,
} from 'lucide-react'
import { useAuth } from '../features/auth/context/AuthContext'
import { type AuthUser } from '../features/auth/api'
import { SubjectSearchInput } from '../features/taxonomy'
import { useSidebar } from '../hooks/useSidebar'
import { PageTransition } from '../components/PageTransition'

// --- Module-scope component (stable identity) ---
function AuthControls({ user, onLogout }: { user: AuthUser | null; onLogout: () => void }) {
  if (!user) return null
  return (
    <div className="flex items-center gap-2.5 shrink-0">
      <span className="text-xs font-medium text-slate-600 hidden sm:inline-block truncate max-w-[120px]">
        {user.full_name || user.email}
      </span>
      <button
        onClick={onLogout}
        className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-rose-600 transition cursor-pointer"
      >
        <LogOut className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Đăng xuất</span>
      </button>
    </div>
  )
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const hideSearch = location.pathname.startsWith('/me/workspace')
  const isWorkspaceEditor = location.pathname.startsWith('/me/workspace/') && location.pathname !== '/me/workspace'
  const isViewingQuiz = new URLSearchParams(location.search).has('artifact')
  const isAdmin = user?.role === 'ADMIN'
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { isCollapsed, setIsCollapsed } = useSidebar()

  const getBackToNotebookUrl = () => {
    const params = new URLSearchParams(location.search)
    params.delete('artifact')
    const searchString = params.toString()
    return searchString ? `${location.pathname}?${searchString}` : location.pathname
  }

  const closeMobileMenu = () => setIsMobileMenuOpen(false)
  const toggleMobileMenu = () => setIsMobileMenuOpen((prev) => !prev)
  const handleLogout = () => {
    logout()
    setIsMobileMenuOpen(false)
  }

  // Xử lý click mở rộng khi nhấn vào vùng trống của sidebar
  const handleSidebarRailClick = (e: React.MouseEvent<HTMLElement>) => {
    if (!isCollapsed) return
    // Nếu click trúng link hoặc button thì bỏ qua
    if ((e.target as HTMLElement).closest('a, button')) {
      return
    }
    setIsCollapsed(false)
  }

  const sidebarContent = (collapsed: boolean) => {
    const linkClass = (isActive: boolean) =>
      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all cursor-pointer ${collapsed ? 'justify-center' : ''
      } ${isActive
        ? 'bg-white/10 text-white font-semibold'
        : 'text-slate-300 hover:bg-white/5 hover:text-white'
      }`

    return (
      <div className="flex flex-col h-full select-none">
        {/* Header: logo + collapse/expand button */}
        <div
          className={`flex items-center px-4 py-4 ${collapsed ? 'justify-center flex-col gap-2' : 'justify-between'
            }`}
          onClick={(e) => {
            if (collapsed) {
              // Click vào header khi collapsed sẽ mở rộng
              if (!(e.target as HTMLElement).closest('a, button')) {
                setIsCollapsed(false)
              }
            }
          }}
        >
          <Link
            to="/"
            onClick={(e) => {
              e.stopPropagation()
              closeMobileMenu()
            }}
            className="flex items-center gap-3 group shrink-0 cursor-pointer"
            title="HCMC-VAULT"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-white shadow-sm transition group-hover:bg-white/15 shrink-0">
              <GraduationCap className="h-5 w-5 pointer-events-none" />
            </div>
            {!collapsed && (
              <span className="text-base font-bold tracking-tight text-white whitespace-nowrap">
                HCMC-VAULT
              </span>
            )}
          </Link>

          {!collapsed && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setIsCollapsed(true)
              }}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition shrink-0 cursor-pointer"
              title="Thu gọn sidebar"
            >
              <PanelLeftClose className="h-4 w-4 pointer-events-none" />
            </button>
          )}
        </div>

        {/* Nav links */}
        <nav className="px-3 py-2 space-y-1">
          <NavLink
            to="/"
            end
            onClick={(e) => e.stopPropagation()}
            className={({ isActive }) => linkClass(isActive)}
            title={collapsed ? 'Trang chủ' : undefined}
          >
            <Home className="h-4 w-4 shrink-0 pointer-events-none" />
            {!collapsed && <span>Trang chủ</span>}
          </NavLink>

          {user && (
            <NavLink
              to="/me/workspace"
              onClick={(e) => e.stopPropagation()}
              className={({ isActive }) => linkClass(isActive)}
              title={collapsed ? 'Workspace cá nhân' : undefined}
            >
              <BookOpen className="h-4 w-4 shrink-0 pointer-events-none" />
              {!collapsed && <span>Workspace cá nhân</span>}
            </NavLink>
          )}

          {isAdmin && (
            <>
              {!collapsed && (
                <p className="px-3 pt-5 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Quản trị
                </p>
              )}
              {collapsed && <div className="my-3 mx-3 border-t border-white/10" />}
              <NavLink
                to="/admin/taxonomy"
                onClick={(e) => e.stopPropagation()}
                className={({ isActive }) => linkClass(isActive)}
                title={collapsed ? 'Phân loại học liệu' : undefined}
              >
                <Tags className="h-4 w-4 shrink-0 pointer-events-none" />
                {!collapsed && <span>Phân loại học liệu</span>}
              </NavLink>
            </>
          )}
        </nav>

        {/* Vùng trống bên dưới chiếm toàn bộ không gian còn lại (nhấn vào để mở rộng) */}
        <div
          className={`flex-1 w-full ${collapsed ? 'cursor-col-resize' : ''}`}
          title={collapsed ? 'Nhấn vào vùng trống để mở rộng sidebar' : undefined}
        />
      </div>
    )
  }

  return (
    <div className="h-screen bg-[#FAF9F6] flex font-sans antialiased text-slate-800 overflow-hidden">
      {/* ======================================================== */}
      {/* 1. DESKTOP LEFT SIDEBAR                                   */}
      {/* ======================================================== */}
      <aside
        className={`
          hidden md:flex flex-col bg-[#13141A] h-full z-30
          transition-all duration-300
          ${isCollapsed ? 'w-20 cursor-col-resize' : 'w-64'}
        `}
        onClick={handleSidebarRailClick}
      >
        {sidebarContent(isCollapsed)}
      </aside>

      {/* ======================================================== */}
      {/* 2. MOBILE OVERLAY DRAWER (always expanded)               */}
      {/* ======================================================== */}
      {isMobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={closeMobileMenu}
            aria-hidden="true"
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 flex flex-col bg-[#13141A] md:hidden shadow-2xl">
            {sidebarContent(false)}
          </aside>
        </>
      )}

      {/* ======================================================== */}
      {/* 3. MAIN CONTENT AREA                                      */}
      {/* ======================================================== */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Mobile sticky bar */}
        <div className="md:hidden sticky top-0 z-20 flex items-center gap-2 bg-[#FAF9F6]/90 backdrop-blur-md border-b border-slate-200/60 px-3 h-14">
          <button
            type="button"
            onClick={toggleMobileMenu}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 focus:outline-none shrink-0 cursor-pointer"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="flex-1 min-w-0 flex items-center gap-2">
            {isWorkspaceEditor && (
              <Link
                to={isViewingQuiz ? getBackToNotebookUrl() : "/me/workspace"}
                className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-slate-800 transition shrink-0"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Quay lại</span>
              </Link>
            )}
            {!hideSearch && <SubjectSearchInput />}
          </div>
          <AuthControls user={user} onLogout={handleLogout} />
        </div>

        {/* Desktop top bar */}
        <div className="hidden md:flex items-center justify-between gap-4 px-8 pt-6 pb-4">
          <div className="flex-1 max-w-md flex items-center gap-4">
            {isWorkspaceEditor && (
              <Link
                to={isViewingQuiz ? getBackToNotebookUrl() : "/me/workspace"}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 hover:bg-slate-100 px-3 py-1.5 rounded-lg transition shrink-0"
              >
                <ArrowLeft className="h-4 w-4" />
                {isViewingQuiz ? 'Quay lại Sổ ghi chú' : 'Quay lại Workspace'}
              </Link>
            )}
            {!hideSearch && <SubjectSearchInput />}
          </div>
          <AuthControls user={user} onLogout={handleLogout} />
        </div>

        <main className={
          isWorkspaceEditor
            ? "flex-1 overflow-hidden w-full h-full p-0 flex flex-col min-h-0"
            : "flex-1 overflow-y-auto px-6 pb-8 md:px-8 md:pb-10 max-w-7xl w-full mx-auto"
        }>
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  )
}