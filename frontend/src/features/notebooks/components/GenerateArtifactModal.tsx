import { useState } from 'react'
import { X, Sparkles, FileText, AlertTriangle } from 'lucide-react'
import { useGenerateQuiz } from '../hooks/useGenerateQuiz'
import type { NotebookSource } from '../api'

interface GenerateArtifactModalProps {
    isOpen: boolean
    notebookId: number
    sources: NotebookSource[]
    onClose: () => void
    onSuccess: (artifactId: number) => void
}

export function GenerateArtifactModal({
    isOpen,
    notebookId,
    sources,
    onClose,
    onSuccess,
}: GenerateArtifactModalProps) {
    const [selectedAssetIds, setSelectedAssetIds] = useState<number[]>([])
    const [numQuestions, setNumQuestions] = useState<number>(5)

    const { mutate: generateQuiz, isPending } = useGenerateQuiz(notebookId, {
        onSuccess: (data) => {
            onSuccess(data.id)
        },
    })

    if (!isOpen) return null

    const handleToggleAsset = (assetId: number) => {
        if (isPending) return
        setSelectedAssetIds((prev) =>
            prev.includes(assetId)
                ? prev.filter((id) => id !== assetId)
                : [...prev, assetId]
        )
    }

    const handleSelectAll = () => {
        if (isPending) return
        const completedAssetIds = sources
            .filter((src) => src.asset_id && src.ingestion_status === 'COMPLETED')
            .map((src) => src.asset_id!)

        if (selectedAssetIds.length === completedAssetIds.length) {
            setSelectedAssetIds([])
        } else {
            setSelectedAssetIds(completedAssetIds)
        }
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (selectedAssetIds.length === 0 || isPending) return

        generateQuiz({
            selected_asset_ids: selectedAssetIds,
            num_questions: numQuestions,
        })
    }

    const questionOptions = [5, 10, 15, 20]
    const completedSources = sources.filter((src) => src.asset_id && src.ingestion_status === 'COMPLETED')

    return (
        <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-3xs z-50 flex items-center justify-center p-4"
            onClick={() => {
                if (!isPending) onClose()
            }}
        >
            <div
                className="bg-white rounded-2xl w-full max-w-lg shadow-xl overflow-hidden font-sans flex flex-col max-h-[90vh]"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                    <div>
                        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                            <Sparkles className="h-4 w-4 text-indigo-500 fill-indigo-50" />
                            Tạo bài trắc nghiệm ôn tập
                        </h3>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                            Hệ thống AI sẽ tự động đọc nội dung tài liệu và biên soạn bộ câu hỏi.
                        </p>
                    </div>
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={onClose}
                        className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 transition disabled:opacity-50"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-5">
                    {/* Source Selection */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="text-[11px] font-extrabold text-slate-800 uppercase tracking-wide">
                                1. Chọn tài liệu nguồn ôn tập
                            </label>
                            {completedSources.length > 0 && (
                                <button
                                    type="button"
                                    disabled={isPending}
                                    onClick={handleSelectAll}
                                    className="text-[11px] font-bold text-indigo-650 hover:underline disabled:opacity-50"
                                >
                                    {selectedAssetIds.length === completedSources.length
                                        ? 'Bỏ chọn tất cả'
                                        : 'Chọn tất cả sẵn sàng'}
                                </button>
                            )}
                        </div>

                        {sources.length === 0 ? (
                            <div className="p-6 border border-dashed border-slate-200 rounded-xl text-center bg-slate-50">
                                <p className="text-xs text-slate-500">Chưa có tài liệu nguồn nào. Vui lòng thêm tài liệu trước khi tạo quiz.</p>
                            </div>
                        ) : (
                            <div className="border border-slate-150 rounded-xl divide-y divide-slate-100 max-h-48 overflow-y-auto">
                                {sources.map((src) => {
                                    const hasAssetId = !!src.asset_id
                                    const isReady = hasAssetId && src.ingestion_status === 'COMPLETED'
                                    const isPendingConversion = src.conversion_status === 'PENDING'
                                    const isProcessingIngestion = src.ingestion_status === 'PENDING' || src.ingestion_status === 'PROCESSING'
                                    const isErrorState = src.conversion_status === 'FAILED' || src.ingestion_status === 'FAILED'

                                    return (
                                        <div
                                            key={`${src.type}-${src.id}`}
                                            className={`p-3 flex items-start justify-between gap-3 text-xs ${isReady
                                                    ? 'hover:bg-slate-50 cursor-pointer'
                                                    : 'bg-slate-50/50 cursor-not-allowed'
                                                }`}
                                            onClick={() => {
                                                if (isReady) handleToggleAsset(src.asset_id!)
                                            }}
                                        >
                                            <div className="flex items-start gap-2.5 min-w-0">
                                                <input
                                                    type="checkbox"
                                                    disabled={!isReady || isPending}
                                                    checked={isReady && selectedAssetIds.includes(src.asset_id!)}
                                                    onChange={() => { }} // click on parent div handles state
                                                    className="mt-0.5 h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer disabled:cursor-not-allowed"
                                                />
                                                <div className="min-w-0">
                                                    <span className="font-bold text-slate-800 break-all leading-snug flex items-center gap-1.5">
                                                        <FileText className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                                                        {src.title}
                                                    </span>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <span className="text-[10px] text-slate-400 font-medium">
                                                            {src.type === 'local' ? 'Tải lên' : 'Thư viện'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Status badges */}
                                            <div className="shrink-0 pt-0.5">
                                                {!hasAssetId && (
                                                    <span className="text-[9px] leading-none font-bold text-rose-700 bg-rose-50 border border-rose-150 px-1 py-0.5 rounded flex items-center gap-1">
                                                        <AlertTriangle className="h-2.5 w-2.5" />
                                                        Thiếu dữ liệu tệp
                                                    </span>
                                                )}
                                                {hasAssetId && !isReady && (
                                                    <span
                                                        className={`text-[9px] leading-none font-bold px-1.5 py-0.5 rounded flex items-center gap-1 border ${isErrorState
                                                                ? 'text-rose-700 bg-rose-50 border-rose-150'
                                                                : isPendingConversion || isProcessingIngestion
                                                                    ? 'text-amber-700 bg-amber-50 border-amber-150 animate-pulse'
                                                                    : 'text-slate-500 bg-slate-50 border-slate-200'
                                                            }`}
                                                    >
                                                        {isErrorState ? (
                                                            <>
                                                                <AlertTriangle className="h-2.5 w-2.5" />
                                                                Lỗi xử lý tài liệu
                                                            </>
                                                        ) : (
                                                            'Đang xử lý nội dung...'
                                                        )}
                                                    </span>
                                                )}
                                                {isReady && (
                                                    <span className="text-[9px] leading-none font-bold text-emerald-700 bg-emerald-50 border border-emerald-150 px-1.5 py-0.5 rounded">
                                                        Đã sẵn sàng
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </div>

                    {/* Question count options layout */}
                    <div className="space-y-2">
                        <label className="text-[11px] font-extrabold text-slate-800 uppercase tracking-wide">
                            2. Số lượng câu hỏi ôn tập
                        </label>
                        <div className="flex gap-2">
                            {questionOptions.map((qty) => (
                                <button
                                    key={qty}
                                    type="button"
                                    disabled={isPending}
                                    onClick={() => setNumQuestions(qty)}
                                    className={`flex-1 py-2 text-xs font-bold rounded-xl border transition-all ${numQuestions === qty
                                            ? 'border-indigo-650 bg-indigo-50 text-indigo-705 shadow-3xs'
                                            : 'border-slate-205 bg-white text-slate-505 hover:bg-slate-50'
                                        }`}
                                >
                                    {qty} câu hỏi
                                </button>
                            ))}
                        </div>
                    </div>
                </form>

                {/* Footer buttons row */}
                <div className="p-5 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50 flex-shrink-0">
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={onClose}
                        className="px-4 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition cursor-pointer disabled:opacity-50"
                    >
                        Hủy
                    </button>
                    <button
                        type="button"
                        disabled={selectedAssetIds.length === 0 || isPending}
                        onClick={handleSubmit}
                        className="px-5 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-705 active:bg-indigo-805 rounded-xl shadow-xs transition flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isPending ? (
                            <>
                                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                <span>Đang biên soạn...</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4 shrink-0" />
                                <span>Tạo bài ôn tập</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
