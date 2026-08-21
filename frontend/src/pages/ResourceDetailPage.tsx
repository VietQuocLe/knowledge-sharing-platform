import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { resourcesApi, resourcesKeys } from '../features/resources'
import { parseRouteId } from '../utils/parseRouteId'

export function ResourceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const documentId = parseRouteId(id)
  const [downloadingAssetId, setDownloadingAssetId] = useState<number | null>(null)

  const {
    data: document,
    isLoading,
    error,
  } = useQuery({
    queryKey: resourcesKeys.detailById(documentId!),
    queryFn: () => resourcesApi.getDocumentDetail(documentId!),
    enabled: documentId !== null,
  })

  async function handleDownload(assetId: number) {
    if (documentId === null) return
    setDownloadingAssetId(assetId)
    try {
      const { download_url } = await resourcesApi.getAssetDownloadUrl(documentId, assetId)
      window.open(download_url, '_blank', 'noopener,noreferrer')
    } finally {
      setDownloadingAssetId(null)
    }
  }

  if (documentId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Mã tài liệu không hợp lệ." />
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
        <ErrorMessage message="Không thể tải thông tin tài liệu" />
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

      {document && (
        <>
          <h1 className="text-3xl font-semibold text-slate-900">{document.title}</h1>

          <div className="mt-4 flex flex-wrap gap-3">
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {document.resource_type}
            </span>
            <span className="rounded-lg bg-blue-100 px-3 py-1 text-sm text-blue-700">
              {document.status}
            </span>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {new Date(document.created_at).toLocaleDateString('vi-VN')}
            </span>
          </div>

          {document.description && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-slate-900">Mô tả</h2>
              <p className="mt-2 text-slate-700">{document.description}</p>
            </div>
          )}

          {document.assets && document.assets.length > 0 && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold text-slate-900">Tài liệu đính kèm</h2>
              <div className="mt-4 space-y-2">
                {document.assets.map((asset) => (
                  <div
                    key={asset.id}
                    className="flex items-center gap-3 rounded-lg border border-slate-200 p-3"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-slate-900">{asset.file_name}</div>
                      <div className="text-xs text-slate-500">
                        {asset.file_type} · {(asset.size / 1024).toFixed(2)} KB
                      </div>
                    </div>
                    <button
                      onClick={() => handleDownload(asset.id)}
                      disabled={downloadingAssetId === asset.id}
                      className="shrink-0 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-60"
                    >
                      {downloadingAssetId === asset.id ? 'Đang tải…' : 'Tải về'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
