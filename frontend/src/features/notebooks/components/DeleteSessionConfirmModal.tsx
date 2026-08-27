import { useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { notebooksApi } from '../api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'

interface DeleteSessionConfirmModalProps {
    isOpen: boolean
    notebookId: number
    session: { id: number; title: string }
    onClose: () => void
}

export function DeleteSessionConfirmModal({ isOpen, notebookId, session, onClose }: DeleteSessionConfirmModalProps) {
    const queryClient = useQueryClient()
    const [searchParams, setSearchParams] = useSearchParams()

    const { mutate: deleteSession, isPending } = useMutation({
        mutationFn: () => notebooksApi.deleteSession(notebookId, session.id),
        onSuccess: () => {
            toast.success('Đã xóa cuộc hội thoại thành công!')

            // If the deleted session was the active one, clear it from URL search parameters
            if (searchParams.get('session') === String(session.id)) {
                const nextParams = new URLSearchParams(searchParams)
                nextParams.delete('session')
                setSearchParams(nextParams)
            }

            queryClient.invalidateQueries({
                queryKey: ['notebooks', notebookId, 'sessions']
            })
            onClose()
        },
        onError: (err: any) => {
            const errMsg = getApiErrorMessage(err, 'Không thể xóa cuộc hội thoại. Vui lòng thử lại!')
            toast.error(errMsg)
        }
    })

    return (
        <Modal isOpen={isOpen} title="Xóa cuộc hội thoại">
            <div className="space-y-4">
                <p className="text-sm text-slate-600">
                    Bạn có chắc chắn muốn xóa cuộc hội thoại <span className="font-semibold text-slate-800">"{session.title}"</span> không? Hành động này sẽ xóa vĩnh viễn cuộc hội thoại cùng toàn bộ tin nhắn liên quan và không thể hoàn tác.
                </p>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-slate-650 hover:bg-slate-100 rounded-xl transition"
                    >
                        Hủy
                    </button>
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={() => deleteSession()}
                        className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-rose-605 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 rounded-xl shadow-md shadow-rose-600/10 hover:shadow-rose-600/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                        {isPending ? 'Đang xóa...' : 'Xóa hội thoại'}
                    </button>
                </div>
            </div>
        </Modal>
    )
}
