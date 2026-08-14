import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { resourcesApi, type ResourceStatus, type VisibilityEnum } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'

const visibilityBadge: Record<VisibilityEnum, { label: string; className: string }> = {
  PRIVATE: { label: 'Riêng tư', className: 'bg-slate-100 text-slate-700' },
  PENDING_REVIEW: { label: 'Chờ duyệt', className: 'bg-amber-100 text-amber-800' },
  PUBLIC: { label: 'Công khai', className: 'bg-emerald-100 text-emerald-800' },
}

const statusLabel: Record<ResourceStatus, string> = {
  PROCESSING: 'Đang xử lý',
  READY: 'Sẵn sàng',
  FAILED: 'Xử lý thất bại',
  DELETED: 'Đã xóa',
}

export function MyResourcesPage() {
  const {
    data: resourcesPage,
    isLoading,
    error,
  } = useQuery({
    queryKey: resourcesKeys.me(),
    queryFn: () => resourcesApi.getMyResources({ size: 100 }),
  })

  const resources = resourcesPage?.items ?? []

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Tài nguyên của tôi</h1>
      <p className="mt-2 text-sm text-slate-600">Theo dõi trạng thái và tiếp tục hoàn thiện các tài nguyên của bạn.</p>

      {isLoading ? (
        <div className="mt-6 flex justify-center py-8">
          <Spinner />
        </div>
      ) : error ? (
        <div className="mt-6">
          <ErrorMessage message="Không thể tải tài nguyên của bạn" />
        </div>
      ) : resources.length > 0 ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {resources.map((resource) => {
            const visibility = visibilityBadge[resource.visibility]

            return (
              <article key={resource.id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="font-medium text-slate-900">{resource.title}</h2>
                  <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${visibility.className}`}>
                    {visibility.label}
                  </span>
                </div>

                {resource.description ? (
                  <p className="mt-2 text-sm text-slate-600 line-clamp-2">{resource.description}</p>
                ) : null}

                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <span className="rounded bg-slate-100 px-2 py-1 text-slate-700">{resource.resource_type}</span>
                  <span className="rounded bg-slate-100 px-2 py-1 text-slate-700">{statusLabel[resource.status]}</span>
                  <span className="rounded bg-slate-100 px-2 py-1 text-slate-700">
                    {new Date(resource.created_at).toLocaleDateString('vi-VN')}
                  </span>
                </div>

                {resource.rejection_reason ? (
                  <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                    <span className="font-medium">Lý do từ chối: </span>{resource.rejection_reason}
                  </div>
                ) : null}

                {resource.visibility === 'PRIVATE' ? (
                  <Link
                    to={`/resources/${resource.id}/upload`}
                    className="mt-4 inline-flex rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
                  >
                    Đính kèm file / gửi duyệt
                  </Link>
                ) : null}
              </article>
            )
          })}
        </div>
      ) : (
        <p className="mt-6 text-sm text-slate-600">Bạn chưa có tài nguyên nào.</p>
      )}
    </div>
  )
}
