const resources = [
  { id: 1, title: 'Bài giảng OOP', status: 'PROCESSING' },
  { id: 2, title: 'Tài liệu SQL', status: 'READY' },
  { id: 3, title: 'Chuyên đề FastAPI', status: 'PENDING_REVIEW' },
  { id: 4, title: 'Notebook AI', status: 'PUBLIC' },
]

const statusLabel: Record<string, string> = {
  PROCESSING: 'Đang xử lý',
  READY: 'Sẵn sàng',
  PENDING_REVIEW: 'Chờ duyệt',
  PUBLIC: 'Công khai',
}

export function MyResourcesPage() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Tài nguyên của tôi</h1>
      <p className="mt-2 text-sm text-slate-600">Danh sách mock cho khu vực user đã đăng nhập.</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {resources.map((resource) => (
          <div key={resource.id} className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-medium text-slate-900">{resource.title}</h2>
            <p className="mt-2 text-sm text-slate-600">Trạng thái: {statusLabel[resource.status]}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
