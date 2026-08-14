import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { resourcesApi } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'

export function ResourceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const resourceId = parseRouteId(id)

  const {
    data: resource,
    isLoading,
    error,
  } = useQuery({
    queryKey: resourcesKeys.detailById(resourceId!),
    queryFn: () => resourcesApi.getResourceDetail(resourceId!),
    enabled: resourceId !== null,
  })

  if (resourceId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Mã tài nguyên không hợp lệ." />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Không thể tải thông tin tài nguyên" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        <Link to="/" className="text-sm text-slate-600 hover:text-slate-900">
          ← Quay lại
        </Link>
      </div>

      {resource && (
        <>
          <h1 className="text-3xl font-semibold text-slate-900">{resource.title}</h1>

          <div className="mt-4 flex flex-wrap gap-3">
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {resource.resource_type}
            </span>
            <span className="rounded-lg bg-blue-100 px-3 py-1 text-sm text-blue-700">
              {resource.status}
            </span>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {new Date(resource.created_at).toLocaleDateString('vi-VN')}
            </span>
          </div>

          {resource.description && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-slate-900">Mô tả</h2>
              <p className="mt-2 text-slate-700">{resource.description}</p>
            </div>
          )}

          {resource.assets && resource.assets.length > 0 && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-slate-900">Tài liệu đính kèm</h2>
              <div className="mt-4 space-y-2">
                {resource.assets.map((asset) => (
                  <div key={asset.id} className="flex items-center gap-3 rounded-lg border border-slate-200 p-3">
                    <div className="flex-1">
                      <div className="font-medium text-slate-900">{asset.file_name}</div>
                      <div className="text-xs text-slate-500">
                        {asset.file_type} · {(asset.size / 1024).toFixed(2)} KB
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {resource.rejection_reason && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
              <h3 className="font-medium text-red-900">Lý do từ chối</h3>
              <p className="mt-2 text-sm text-red-800">{resource.rejection_reason}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
