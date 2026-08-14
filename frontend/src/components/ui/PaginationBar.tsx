type PaginationBarProps = {
  page: number
  total: number
  pageSize: number
  onPageChange: (page: number) => void
}

export function PaginationBar({ page, total, pageSize, onPageChange }: PaginationBarProps) {
  if (total <= 0) {
    return null
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="mt-6 flex items-center justify-between border-t border-slate-200 pt-4">
      <div className="text-sm text-slate-600">
        Trang {page} / {totalPages} (tổng {total})
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm transition disabled:opacity-50 hover:enabled:border-slate-900"
        >
          ← Trước
        </button>
        <button
          type="button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm transition disabled:opacity-50 hover:enabled:border-slate-900"
        >
          Sau →
        </button>
      </div>
    </div>
  )
}
