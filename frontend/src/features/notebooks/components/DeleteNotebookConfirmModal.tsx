import { Loader2 } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { useDeleteNotebook } from '../hooks/useDeleteNotebook'
import type { Notebook } from '../api'
import { toast } from 'react-hot-toast'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'

interface DeleteNotebookConfirmModalProps {
    isOpen: boolean
    notebook: Notebook
    onClose: () => void
}

export function DeleteNotebookConfirmModal({ isOpen, notebook, onClose }: DeleteNotebookConfirmModalProps) {
    const { mutate: deleteNotebook, isPending } = useDeleteNotebook()

    const handleDelete = () => {
        deleteNotebook(notebook.id, {
            onSuccess: () => {
                toast.success('Đã xóa sổ ghi chú thành công!')
                onClose()
            },
            onError: (err: any) => {
                const errMsg = getApiErrorMessage(err, 'Không thể xóa sổ ghi chú. Vui lòng thử lại!')
                toast.error(errMsg)
            },
        })
    }

    return (
        <Modal isOpen={isOpen} title="Xóa sổ ghi chú">
            <div className="space-y-4">
                <p className="text-sm text-slate-600">
                    Bạn có chắc chắn muốn xóa sổ ghi chú <span className="font-semibold text-slate-805">"{notebook.title}"</span> không? Hành động này sẽ xóa vĩnh viễn sổ ghi chú, các tài liệu đính kèm bên trong và không thể hoàn tác.
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
                        onClick={handleDelete}
                        disabled={isPending}
                        className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 active:bg-rose-800 rounded-xl shadow-md shadow-rose-600/10 hover:shadow-rose-600/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                        {isPending ? 'Đang xóa...' : 'Xóa sổ'}
                    </button>
                </div>
            </div>
        </Modal>
    )
}
