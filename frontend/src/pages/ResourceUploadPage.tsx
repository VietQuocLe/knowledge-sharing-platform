import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type ChangeEvent } from 'react'
import toast from 'react-hot-toast'
import { useParams } from 'react-router-dom'
import { getApiErrorMessage } from '../api/getApiErrorMessage'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import {
  MAX_ASSETS_PER_RESOURCE,
  MAX_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_MB,
} from '../features/resources/config'
import { resourcesApi, type Resource } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'

const allowedExtensions = ['.pdf', '.docx']

function validateFile(file: File): string | null {
  const fileName = file.name.toLowerCase()

  if (!allowedExtensions.some((extension) => fileName.endsWith(extension))) {
    return 'Chỉ hỗ trợ file PDF hoặc DOCX.'
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `Dung lượng mỗi file không được vượt quá ${MAX_FILE_SIZE_MB} MB.`
  }

  return null
}

function formatFileSize(size: number) {
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

function ResourceUploadPageContent({ resource }: { resource: Resource }) {
  const queryClient = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const isPrivate = resource.visibility === 'PRIVATE'
  const canUpload = isPrivate && resource.assets.length < MAX_ASSETS_PER_RESOURCE
  const canSubmit = isPrivate && resource.assets.length > 0

  const refreshResourceQueries = async (resourceId: number, options?: { notifyAdmin?: boolean }) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: resourcesKeys.me() }),
      queryClient.invalidateQueries({ queryKey: resourcesKeys.myDetailById(resourceId) }),
      ...(options?.notifyAdmin
        ? [queryClient.invalidateQueries({ queryKey: resourcesKeys.adminList() })]
        : []),
    ])
  }

  const uploadMutation = useMutation({
    mutationFn: ({ resourceId, file }: { resourceId: number; file: File }) =>
      resourcesApi.uploadResourceAsset(resourceId, file),
    onSuccess: async (updatedResource) => {
      setSelectedFile(null)
      await refreshResourceQueries(updatedResource.id)
      toast.success('Đã đính kèm tài liệu.')
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, 'Không thể upload file. Vui lòng thử lại.'))
    },
  })

  const submitMutation = useMutation({
    mutationFn: resourcesApi.submitResourceForReview,
    onSuccess: async (updatedResource) => {
      await refreshResourceQueries(updatedResource.id, { notifyAdmin: true })
      toast.success('Đã gửi tài nguyên để kiểm duyệt.')
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, 'Không thể gửi kiểm duyệt. Vui lòng thử lại.'))
    },
  })

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    if (!file) return

    const validationMessage = validateFile(file)
    if (validationMessage) {
      event.target.value = ''
      setSelectedFile(null)
      toast.error(validationMessage)
      return
    }

    setSelectedFile(file)
  }

  const handleUpload = () => {
    if (!selectedFile) {
      toast.error('Vui lòng chọn file trước khi upload.')
      return
    }

    const validationMessage = validateFile(selectedFile)
    if (validationMessage) {
      toast.error(validationMessage)
      return
    }

    uploadMutation.mutate({ resourceId: resource.id, file: selectedFile })
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Đính kèm tài liệu</h1>
      <p className="mt-2 text-sm text-slate-600">Bước 2/2: upload file PDF/DOCX, sau đó gửi tài nguyên để kiểm duyệt.</p>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-medium text-slate-900">{resource.title}</h2>
            <p className="mt-1 text-sm text-slate-600">Trạng thái: {resource.visibility === 'PRIVATE' ? 'Riêng tư' : 'Đã gửi kiểm duyệt'}</p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${
            resource.visibility === 'PRIVATE' ? 'bg-slate-200 text-slate-700' : 'bg-amber-100 text-amber-800'
          }`}>
            {resource.visibility}
          </span>
        </div>
      </div>

      {!isPrivate ? (
        <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Tài nguyên đã ở trạng thái {resource.visibility === 'PENDING_REVIEW' ? 'chờ kiểm duyệt' : resource.visibility}; upload đã được khóa.
        </div>
      ) : null}

      <section className="mt-6">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Tài liệu đã đính kèm</h2>
          <span className="text-sm text-slate-600">{resource.assets.length}/{MAX_ASSETS_PER_RESOURCE} file</span>
        </div>

        {resource.assets.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {resource.assets.map((asset) => (
              <li key={asset.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <span className="min-w-0 truncate font-medium text-slate-800">{asset.file_name}</span>
                <span className="shrink-0 text-slate-500">{asset.file_type} · {formatFileSize(asset.size)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-600">Chưa có tài liệu nào được đính kèm.</p>
        )}
      </section>

      <section className="mt-6 border-t border-slate-200 pt-6">
        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Chọn file</span>
          <input
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            disabled={!canUpload || uploadMutation.isPending || submitMutation.isPending}
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-800 hover:file:bg-slate-200 disabled:cursor-not-allowed"
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">Chỉ nhận PDF/DOCX, tối đa {MAX_FILE_SIZE_MB} MB mỗi file và {MAX_ASSETS_PER_RESOURCE} file cho mỗi tài nguyên.</p>
        {selectedFile ? <p className="mt-2 text-sm text-slate-700">Đã chọn: {selectedFile.name}</p> : null}

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleUpload}
            disabled={!canUpload || !selectedFile || uploadMutation.isPending || submitMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 transition hover:border-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploadMutation.isPending ? <Spinner size="sm" /> : null}
            {uploadMutation.isPending ? 'Đang upload...' : 'Upload file'}
          </button>
          <button
            type="button"
            onClick={() => submitMutation.mutate(resource.id)}
            disabled={!canSubmit || uploadMutation.isPending || submitMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitMutation.isPending ? <Spinner size="sm" className="border-slate-500 border-t-white" /> : null}
            {submitMutation.isPending ? 'Đang gửi...' : 'Gửi kiểm duyệt'}
          </button>
        </div>
      </section>
    </div>
  )
}

export function ResourceUploadPage() {
  const { id } = useParams()
  const resourceId = Number(id)
  const resourceQuery = useQuery({
    queryKey: resourcesKeys.myDetailById(resourceId),
    queryFn: () => resourcesApi.getMyResourceById(resourceId),
    enabled: Number.isInteger(resourceId) && resourceId > 0,
  })

  if (!Number.isInteger(resourceId) || resourceId <= 0) {
    return <ErrorMessage message="Mã tài nguyên không hợp lệ." />
  }

  if (resourceQuery.isLoading) {
    return <div className="flex justify-center py-10"><Spinner /></div>
  }

  if (resourceQuery.error) {
    return <ErrorMessage message="Không thể tải thông tin tài nguyên." />
  }

  if (!resourceQuery.data) {
    return <ErrorMessage message="Không tìm thấy tài nguyên của bạn." />
  }

  return <ResourceUploadPageContent resource={resourceQuery.data} />
}
