import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { File, Download, FileText, Eye, User, Archive } from 'lucide-react'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { Breadcrumb } from '../components/ui/Breadcrumb'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { documentsApi, documentsKeys, PdfPreviewModal } from '../features/documents'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'
import { formatResourceType, formatFileSize, formatRelativeTime } from '../utils/formatters'

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const documentId = parseRouteId(id)
  const [downloadingAssetId, setDownloadingAssetId] = useState<number | null>(null)

  // PDF Preview states
  const [previewAsset, setPreviewAsset] = useState<any | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isLoadingPreviewUrl, setIsLoadingPreviewUrl] = useState(false)

  async function handlePreview(asset: any) {
    if (documentId === null) return
    setPreviewAsset(asset)
    setPreviewUrl(null)
    setIsLoadingPreviewUrl(true)
    try {
      const { download_url } = await documentsApi.getAssetDownloadUrl(documentId, asset.id)
      setPreviewUrl(download_url)
    } catch (err) {
      console.error('Failed to load preview URL:', err)
    } finally {
      setIsLoadingPreviewUrl(false)
    }
  }

  function handleClosePreview() {
    setPreviewAsset(null)
    setPreviewUrl(null)
    setIsLoadingPreviewUrl(false)
  }

  // 1. Fetch Document Detail
  const {
    data: document,
    isLoading: isLoadingDoc,
    error: errorDoc,
  } = useQuery({
    queryKey: documentsKeys.detailById(documentId!),
    queryFn: () => documentsApi.getDocumentDetail(documentId!),
    enabled: documentId !== null,
  })

  // 2. Fetch Subject Detail
  const subjectId = document?.subject_id
  const { data: subject, isLoading: isLoadingSubject } = useQuery({
    queryKey: taxonomyKeys.subjectDetail(subjectId!),
    queryFn: () => taxonomyApi.getSubjectById(subjectId!),
    enabled: !!subjectId,
  })

  // 3. Fetch Department Detail
  const primaryMajor = subject?.majors?.[0]
  const deptId = primaryMajor?.department_id
  const { data: department, isLoading: isLoadingDept } = useQuery({
    queryKey: taxonomyKeys.departmentDetail(deptId!),
    queryFn: () => taxonomyApi.getDepartmentById(deptId!),
    enabled: !!deptId,
  })

  async function handleDownload(assetId: number) {
    if (documentId === null) return
    setDownloadingAssetId(assetId)
    try {
      const { download_url } = await documentsApi.getAssetDownloadUrl(documentId, assetId)
      window.open(download_url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      console.error('Failed to download asset:', err)
    } finally {
      setDownloadingAssetId(null)
    }
  }

  if (documentId === null) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Mã tài liệu không hợp lệ." />
      </div>
    )
  }

  // Progressive loading check
  const isCurrentlyLoading =
    isLoadingDoc ||
    (!!subjectId && isLoadingSubject) ||
    (!!deptId && isLoadingDept)

  if (isCurrentlyLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (errorDoc) {
    return (
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Không thể tải hoặc hiển thị thông tin tài liệu học tập." />
      </div>
    )
  }

  // Construct breadcrumbs
  const breadcrumbItems = []
  if (department && primaryMajor && subject && document) {
    breadcrumbItems.push(
      { label: department.name, href: `/departments/${department.id}` },
      { label: primaryMajor.name, href: primaryMajor.id ? `/majors/${primaryMajor.id}` : '#' },
      { label: subject.name, href: `/subjects/${subject.id}` },
      { label: document.title },
    )
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PUBLIC':
      case 'APPROVED':
        return <Badge variant="success">Đã duyệt</Badge>
      case 'DRAFT':
        return <Badge variant="warning">Chờ duyệt</Badge>
      case 'DELETED':
        return <Badge variant="danger">Đã xóa</Badge>
      default:
        return <Badge variant="neutral">{status}</Badge>
    }
  }

  const getFileIcon = (fileName: string, fileType: string) => {
    const nameLower = fileName.toLowerCase()
    if (nameLower.endsWith('.pdf') || fileType.includes('pdf')) {
      return <FileText className="h-5 w-5 text-rose-500" />
    }
    if (
      nameLower.endsWith('.zip') ||
      nameLower.endsWith('.rar') ||
      nameLower.endsWith('.7z') ||
      fileType.includes('zip') ||
      fileType.includes('compressed')
    ) {
      return <Archive className="h-5 w-5 text-amber-500" />
    }
    return <File className="h-5 w-5 text-slate-500" />
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6 font-sans">
      {/* Breadcrumbs */}
      {breadcrumbItems.length > 0 && <Breadcrumb items={breadcrumbItems} />}

      {document && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Cột chính bên trái: Chi tiết tài liệu (lg:col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="primary">{formatResourceType(document.resource_type)}</Badge>
                {getStatusBadge(document.status)}
                <span className="text-xs text-slate-500 font-medium">
                  Cập nhật: {formatRelativeTime(document.created_at)}
                </span>
              </div>

              <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl leading-snug">
                {document.title}
              </h1>

              {/* Thông tin tác giả / người đăng */}
              <div className="flex items-center gap-3 py-3 border-y border-slate-100/80 text-xs text-slate-600">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                  <User className="h-4.5 w-4.5" />
                </div>
                <div>
                  <p className="font-bold text-slate-800">Đăng bởi: Quản trị viên</p>
                  <p className="text-slate-450 mt-0.5">Tài khoản Hệ thống đóng góp</p>
                </div>
              </div>
            </div>

            {/* Khối mô tả chi tiết */}
            <Card>
              <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2 mb-3">
                Mô tả chi tiết
              </h2>
              {document.description ? (
                <p className="text-sm text-slate-655 leading-relaxed whitespace-pre-wrap">
                  {document.description}
                </p>
              ) : (
                <p className="text-sm text-slate-450 italic">Không có mô tả chi tiết cho học liệu này.</p>
              )}
            </Card>
          </div>

          {/* Cột bên phải: Tệp tin đính kèm & Tải về (lg:col-span-4) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Danh sách tệp đính kèm */}
            <Card className="p-6">
              <h2 className="text-sm font-bold text-slate-950 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2 flex items-center justify-between">
                <span>Tệp tin đính kèm</span>
                <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-605">
                  {document.assets?.length || 0}
                </span>
              </h2>

              {document.assets && document.assets.length > 0 ? (
                <div className="space-y-4">
                  {document.assets.map((asset) => {
                    const isDownloading = downloadingAssetId === asset.id
                    const isPdf = asset.file_name.toLowerCase().endsWith('.pdf') || asset.file_type.includes('pdf')

                    return (
                      <div
                        key={asset.id}
                        className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition space-y-3"
                      >
                        <div className="flex items-start gap-2.5 min-w-0">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-slate-150 shadow-3xs">
                            {getFileIcon(asset.file_name, asset.file_type)}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h4 className="text-xs font-bold text-slate-800 break-all leading-tight" title={asset.file_name}>
                              {asset.file_name}
                            </h4>
                            <p className="text-3xs font-semibold text-slate-450 uppercase tracking-wider mt-0.5">
                              {formatFileSize(asset.size)}
                            </p>
                          </div>
                        </div>

                        <div className="flex gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => handleDownload(asset.id)}
                            disabled={isDownloading}
                            className="flex-1 flex items-center justify-center gap-1 inline-flex rounded-lg bg-slate-900 hover:bg-slate-750 text-white px-3 py-1.5 text-xs font-bold transition disabled:opacity-60 shadow-sm cursor-pointer"
                          >
                            {isDownloading ? (
                              <>
                                <Spinner size="sm" className="border-t-white" />
                                ...
                              </>
                            ) : (
                              <>
                                <Download className="h-3.5 w-3.5" />
                                Tải về
                              </>
                            )}
                          </button>
                          {isPdf && (
                            <button
                              type="button"
                              onClick={() => handlePreview(asset)}
                              disabled={isDownloading}
                              className="flex-1 flex items-center justify-center gap-1 inline-flex rounded-lg bg-white border border-slate-205 hover:bg-slate-50 text-slate-700 px-3 py-1.5 text-xs font-bold transition disabled:opacity-60 shadow-sm cursor-pointer hover:border-slate-350"
                            >
                              <Eye className="h-3.5 w-3.5 text-slate-400" />
                              Xem trước
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-6 text-slate-455 text-xs italic">
                  Không có tập tin vật lý đính kèm.
                </div>
              )}
            </Card>

            {/* Thông tin đính tham chiếu */}
            <Card>
              <h2 className="text-sm font-bold text-slate-955 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">
                Thông tin tham chiếu
              </h2>
              <dl className="space-y-3.5 text-xs">
                <div>
                  <dt className="font-semibold text-slate-455 uppercase mb-0.5">Môn học</dt>
                  <dd className="font-bold text-slate-800 text-sm leading-snug">{subject?.name || '-'}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-455 uppercase mb-0.5">Mã môn</dt>
                  <dd className="font-semibold text-slate-655">{subject?.code || '-'}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-455 uppercase mb-0.5">Ngành học</dt>
                  <dd className="font-bold text-slate-800 text-sm leading-snug">{primaryMajor?.name || '-'}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-slate-455 uppercase mb-0.5">Khoa quản lý</dt>
                  <dd className="font-semibold text-slate-655">{department?.name || '-'}</dd>
                </div>
              </dl>
            </Card>

            {/* Học liệu hữu ích? */}
            <Card className="bg-indigo-50/40 border-indigo-100">
              <h3 className="text-sm font-bold text-indigo-950 mb-2">Học liệu hữu ích?</h3>
              <p className="text-xs text-indigo-900/80 leading-relaxed mb-4">
                Nếu tài liệu này giúp ích cho quá trình ôn tập hoặc nghiên cứu của bạn, hãy đóng góp thêm nhiều tài liệu khác.
              </p>
              {import.meta.env.VITE_CONTRIBUTE_FORM_URL && (
                <a
                  href={import.meta.env.VITE_CONTRIBUTE_FORM_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-center w-full rounded-lg bg-indigo-650 hover:bg-indigo-755 text-white hover:text-white px-3 py-2 text-xs font-bold transition shadow-2xs cursor-pointer"
                >
                  Gửi học liệu đóng góp
                </a>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* PDF Preview Modal */}
      <PdfPreviewModal
        isOpen={previewAsset !== null}
        onClose={handleClosePreview}
        fileUrl={previewUrl}
        fileName={previewAsset?.file_name || ''}
        isLoadingUrl={isLoadingPreviewUrl}
      />
    </div>
  )
}
