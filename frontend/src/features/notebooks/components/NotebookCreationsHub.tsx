import { Inbox, Sparkles } from 'lucide-react'
import { useArtifacts } from '../hooks/useArtifacts'
import { ArtifactCard } from './ArtifactCard'

interface NotebookCreationsHubProps {
    notebookId: number
    onSelectArtifact: (id: number) => void
    onOpenGenerateModal?: () => void
}

export function NotebookCreationsHub({
    notebookId,
    onSelectArtifact,
    onOpenGenerateModal,
}: NotebookCreationsHubProps) {
    const { data: artifacts = [], isLoading, error } = useArtifacts(notebookId)

    const handleSelectArtifact = (id: number) => {
        onSelectArtifact(id)
    }

    const quotaCount = artifacts.length
    const totalQuota = 20

    return (
        <div className="space-y-4 flex flex-col font-sans">
            {/* Hub Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-[#0284C7] shrink-0" />
                    Bản tạo AI (Creations Hub)
                </h3>
                <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FEF9C3] text-amber-800 border border-amber-200 text-xs font-semibold whitespace-nowrap">
                        <span className="font-bold">{quotaCount}</span>
                        <span className="text-[10px]"> / {totalQuota} bài ôn tập</span>
                    </span>
                </div>
            </div>

            {/* Quizzes List */}
            <div className="space-y-3">
                {isLoading ? (
                    <div className="py-8 flex justify-center items-center">
                        <span className="h-5 w-5 animate-spin rounded-full border-2 border-[#0D9488] border-t-transparent" />
                    </div>
                ) : error ? (
                    <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-center">
                        <p className="text-xs text-rose-600 font-medium">Không thể tải danh sách bài tập.</p>
                    </div>
                ) : artifacts.length > 0 ? (
                    <div className="grid grid-cols-1 gap-3">
                        {artifacts.map((art) => (
                            <ArtifactCard
                                key={art.id}
                                artifact={art}
                                isActive={false}
                                onSelect={() => handleSelectArtifact(art.id)}
                                onDeleted={() => { }}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="py-10 px-4 border border-dashed border-slate-200 rounded-2xl text-center bg-[#F8F8F6]/60">
                        <Inbox className="h-8 w-8 text-slate-350 mx-auto mb-2" />
                        <h4 className="text-xs font-bold text-slate-700 mb-0.5">Kho trống</h4>
                        <p className="text-[10px] text-slate-450 max-w-[200px] mx-auto leading-relaxed mb-3">
                            Bạn chưa tạo bài trắc nghiệm nào cho sổ ghi chú này.
                        </p>
                        {onOpenGenerateModal && (
                            <button
                                type="button"
                                onClick={onOpenGenerateModal}
                                className="px-3.5 py-1.5 text-[10px] font-bold text-white bg-black hover:bg-slate-800 rounded-xl shadow-xs transition cursor-pointer"
                            >
                                Tạo bài tập ngay
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
