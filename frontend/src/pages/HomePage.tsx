import { Link } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'
import { ResourceList } from '../features/resources/components/ResourceList'
import { TaxonomyView } from '../features/taxonomy/components/TaxonomyView'

export function HomePage() {
  const { user, logout, isLoading } = useAuth()

  if (isLoading) {
    return <div className="p-8 text-slate-600">Đang kiểm tra session...</div>
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Knowledge Sharing Platform</h1>
          <p className="text-slate-600">Cấu trúc frontend đã được tái tổ chức theo feature-based.</p>
        </div>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-700">Xin chào, {user.full_name}</span>
            <button className="rounded-lg border border-slate-300 px-3 py-2 text-sm" onClick={logout}>
              Đăng xuất
            </button>
          </div>
        ) : (
          <div className="flex gap-3">
            <Link className="rounded-lg border border-slate-300 px-3 py-2 text-sm" to="/login">
              Đăng nhập
            </Link>
            <Link className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white" to="/register">
              Đăng ký
            </Link>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Trạng thái Auth</h2>
          <p className="mt-2 text-sm text-slate-600">
            {user ? `Đã đăng nhập với ${user.email}` : 'Chưa đăng nhập'}
          </p>
        </div>
        <div className="space-y-6">
          <ResourceList />
          <TaxonomyView />
        </div>
      </div>
    </div>
  )
}
