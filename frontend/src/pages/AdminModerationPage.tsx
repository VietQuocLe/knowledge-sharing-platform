import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { getApiErrorMessage } from '../api/getApiErrorMessage'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Modal } from '../components/ui/Modal'
import { Spinner } from '../components/ui/Spinner'
import { resourcesApi, type Resource } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'

export function AdminModerationPage() {
  const queryClient = useQueryClient()
  const [rejectingResource, setRejectingResource] = useState<Resource | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [deletingResource, setDeletingResource] = useState<Resource | null>(null)
  const pendingQuery = useQuery({
    queryKey: resourcesKeys.adminListFiltered({ visibility: 'PENDING_REVIEW' }),
    queryFn: () => resourcesApi.getAdminResources({ visibility: 'PENDING_REVIEW' }),
  })
  const invalidateAfterModeration = async (resourceId: number) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: resourcesKeys.adminList() }),
      queryClient.invalidateQueries({ queryKey: resourcesKeys.list() }),
      queryClient.invalidateQueries({ queryKey: resourcesKeys.detailById(resourceId) }),
      queryClient.invalidateQueries({ queryKey: resourcesKeys.me() }),
    ])
  }
  const approveMutation = useMutation({
    mutationFn: resourcesApi.approveResource,
    onSuccess: async (_data, resourceId) => {
      await invalidateAfterModeration(resourceId)
      toast.success('Đã duyệt tài nguyên.')
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể duyệt tài nguyên.')),
  })
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => resourcesApi.rejectResource(id, reason),
    onSuccess: async (_data, { id }) => {
      setRejectingResource(null)
      setRejectionReason('')
      await invalidateAfterModeration(id)
      toast.success('Đã từ chối tài nguyên.')
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể từ chối tài nguyên.')),
  })
  const deleteMutation = useMutation({
    mutationFn: resourcesApi.deleteResource,
    onSuccess: async (_data, resourceId) => {
      setDeletingResource(null)
      await invalidateAfterModeration(resourceId)
      toast.success('Đã xóa tài nguyên.')
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể xóa tài nguyên.')),
  })

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Kiểm duyệt</h1>
      <p className="mt-2 text-sm text-slate-600">Các tài nguyên đang chờ kiểm duyệt.</p>
      {pendingQuery.isLoading ? <div className="mt-6 flex justify-center py-8"><Spinner /></div> : null}
      {pendingQuery.error ? <div className="mt-6"><ErrorMessage message="Không thể tải danh sách chờ duyệt." /></div> : null}
      {!pendingQuery.isLoading && !pendingQuery.error && (pendingQuery.data?.items.length ?? 0) === 0 ? (
        <p className="mt-6 text-sm text-slate-600">Không có tài nguyên nào chờ duyệt.</p>
      ) : null}
      <div className="mt-6 space-y-3">
        {pendingQuery.data?.items.map((resource) => {
          const isPending = approveMutation.isPending || rejectMutation.isPending || deleteMutation.isPending
          return <article key={resource.id} className="rounded-xl border border-slate-200 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-medium text-slate-900">{resource.title}</h2>
                <p className="mt-1 text-sm text-slate-600">Loại: {resource.resource_type} · Chủ sở hữu #{resource.owner_id}</p>
                {resource.description ? <p className="mt-2 text-sm text-slate-600">{resource.description}</p> : null}
                <p className="mt-2 text-xs text-slate-500">{resource.assets.length} file đính kèm</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => approveMutation.mutate(resource.id)} disabled={isPending} className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-60">
                  {approveMutation.isPending ? <Spinner size="sm" className="border-emerald-300 border-t-white" /> : null} Duyệt
                </button>
                <button onClick={() => setRejectingResource(resource)} disabled={isPending} className="rounded-lg bg-amber-500 px-3 py-2 text-sm text-white disabled:opacity-60">Từ chối</button>
                <button onClick={() => setDeletingResource(resource)} disabled={isPending} className="rounded-lg bg-red-600 px-3 py-2 text-sm text-white disabled:opacity-60">Xóa</button>
              </div>
            </div>
          </article>
        })}
      </div>

      <Modal isOpen={rejectingResource !== null} title="Từ chối tài nguyên">
        <label className="block text-sm font-medium text-slate-700">Lý do từ chối (không bắt buộc)
          <textarea value={rejectionReason} onChange={(event) => setRejectionReason(event.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 p-2" />
        </label>
        <div className="mt-4 flex justify-end gap-2"><button onClick={() => setRejectingResource(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => rejectingResource && rejectMutation.mutate({ id: rejectingResource.id, reason: rejectionReason })} disabled={rejectMutation.isPending} className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-3 py-2 text-sm text-white disabled:opacity-60">{rejectMutation.isPending ? <Spinner size="sm" className="border-amber-300 border-t-white" /> : null}Xác nhận từ chối</button></div>
      </Modal>
      <Modal isOpen={deletingResource !== null} title="Xác nhận xóa">
        <p className="text-sm text-slate-600">Bạn có chắc muốn xóa “{deletingResource?.title}”? Tài nguyên sẽ bị ẩn khỏi hệ thống.</p>
        <div className="mt-4 flex justify-end gap-2"><button onClick={() => setDeletingResource(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => deletingResource && deleteMutation.mutate(deletingResource.id)} disabled={deleteMutation.isPending} className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm text-white disabled:opacity-60">{deleteMutation.isPending ? <Spinner size="sm" className="border-red-300 border-t-white" /> : null}Xóa</button></div>
      </Modal>
    </div>
  )
}
