const pendingItems = [
  { id: 1, title: 'Tài nguyên mới 1', owner: 'user1@example.com' },
  { id: 2, title: 'Tài nguyên mới 2', owner: 'user2@example.com' },
]

export function AdminModerationPage() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Moderation</h1>
      <p className="mt-2 text-sm text-slate-600">Danh sách mock cho các tài nguyên chờ duyệt.</p>
      <div className="mt-6 space-y-3">
        {pendingItems.map((item) => (
          <div key={item.id} className="rounded-xl border border-slate-200 p-4">
            <h2 className="font-medium text-slate-900">{item.title}</h2>
            <p className="text-sm text-slate-600">Người gửi: {item.owner}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
