import { useDeleteArtifact } from '../hooks/useDeleteArtifact'

interface DeleteArtifactModalProps {
    isOpen: boolean
    notebookId: number
    artifactId: number
    artifactTitle: string
    onClose: () => void
    onDeleted: () => void
}

export function DeleteArtifactModal({
    isOpen,
    notebookId,
    artifactId,
    artifactTitle,
    onClose,
    onDeleted,
}: DeleteArtifactModalProps) {
    const { mutate: deleteArtifact, isPending } = useDeleteArtifact(notebookId)

    if (!isOpen) return null

    const handleConfirm = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        deleteArtifact(artifactId, {
            onSuccess: () => {
                onDeleted()
                onClose()
            },
        })
    }

    return (
        <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-3xs z-50 flex items-center justify-center p-4"
            onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isPending) onClose()
            }}
        >
            <div
                className="bg-white rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-xl font-sans text-left"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="text-sm font-bold text-slate-800">
                    Xóa bài tập trắc nghiệm
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                    Bạn có chắc chắn muốn xóa bài trắc nghiệm "{artifactTitle}"? Thao tác này sẽ xóa vĩnh viễn và không thể khôi phục.
                </p>
                <div className="flex justify-end gap-2 text-xs font-bold pt-1">
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            onClose()
                        }}
                        className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-xl transition cursor-pointer disabled:opacity-50"
                    >
                        Hủy
                    </button>
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={handleConfirm}
                        className="px-4 py-2 bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 rounded-xl shadow-sm transition cursor-pointer flex items-center gap-1 disabled:opacity-50"
                    >
                        {isPending ? (
                            <>
                                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                <span>Đang xóa...</span>
                            </>
                        ) : (
                            <span>Đồng ý</span>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
