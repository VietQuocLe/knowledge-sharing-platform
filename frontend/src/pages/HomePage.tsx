import { Link } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'
import { TaxonomyView } from '../features/taxonomy/components/TaxonomyView'

export function HomePage() {
  const { user, logout, isLoading } = useAuth()

  if (isLoading) {
    return <div className="p-8 text-slate-600">Đang kiểm tra phiên đăng nhập...</div>
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Nền tảng chia sẻ học liệu</h1>
          <p className="mt-2 text-slate-600">
            Tìm và chia sẻ tài liệu học tập theo Khoa → Ngành → Môn học. Chọn bên dưới để bắt đầu duyệt.
          </p>
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

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Bắt đầu nhanh</h2>
          <p className="mt-2 text-sm text-slate-600">
            {user
              ? 'Bạn có thể duyệt tài liệu công khai, quản lý tài nguyên của mình hoặc đóng góp tài liệu mới.'
              : 'Đăng nhập để đóng góp tài liệu và theo dõi trạng thái kiểm duyệt.'}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              to="/departments"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 transition hover:border-slate-900"
            >
              Duyệt theo khoa
            </Link>
            {user ? (
              <>
                <Link
                  to="/me/resources"
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 transition hover:border-slate-900"
                >
                  Tài liệu của tôi
                </Link>
                <Link
                  to="/resources/create"
                  className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white transition hover:bg-slate-700"
                >
                  Đóng góp tài liệu
                </Link>
              </>
            ) : null}
          </div>
        </div>
        <TaxonomyView />
      </div>
    </div>
  )
}
