import { useState } from 'react'
import { Sparkles, Clock, Trash2, MoreVertical, FileQuestion } from 'lucide-react'
import { useClickOutside } from '../../../hooks/useClickOutside'
import { formatRelativeTime } from '../../../utils/formatters'
import { DeleteArtifactModal } from './DeleteArtifactModal'
import type { ArtifactSummary } from '../api'

interface ArtifactCardProps {
    artifact: ArtifactSummary
    isActive: boolean
    onSelect: () => void
    onDeleted: () => void
}

export function ArtifactCard({ artifact, isActive, onSelect, onDeleted }: ArtifactCardProps) {
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const [isDeleteOpen, setIsDeleteOpen] = useState(false)

    const menuRef = useClickOutside<HTMLDivElement>(() => setIsMenuOpen(false))

    const handleKebabClick = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsMenuOpen(!isMenuOpen)
    }

    const handleDeleteTrigger = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsMenuOpen(false)
        setIsDeleteOpen(true)
    }

    return (
        <>
            <div
                onClick={onSelect}
                className={`p-4 rounded-2xl border transition duration-150 flex flex-col justify-between gap-3 relative group cursor-pointer ${isActive
                    ? 'border-indigo-500 bg-indigo-50/30'
                    : 'border-slate-200 bg-white hover:border-slate-350 hover:shadow-2xs'
                    }`}
            >
                {/* Card Content Row */}
                <div className="flex items-start gap-4 min-w-0 pr-6">
                    <div
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border shadow-3xs group-hover:scale-105 transition ${isActive
                            ? 'bg-indigo-100 border-indigo-250 text-indigo-700'
                            : 'bg-slate-50 border-slate-150 text-slate-650'
                            }`}
                    >
                        <FileQuestion className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                        <h4
                            className={`text-xs font-bold text-slate-800 break-all leading-snug line-clamp-2 hover:text-indigo-650 transition ${isActive ? 'text-indigo-900' : ''
                                }`}
                            title={artifact.title}
                        >
                            {artifact.title}
                        </h4>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            <span className="text-[10px] text-slate-455 font-medium flex items-center gap-1">
                                <Sparkles className="h-3 w-3 text-indigo-500" />
                                <span>Quiz • {artifact.total_items ?? 0} câu hỏi</span>
                            </span>
                        </div>
                    </div>
                </div>

                {/* Bottom timestamp */}
                <div className="flex items-center gap-1.5 text-[10px] text-slate-450 pt-2 border-t border-slate-50">
                    <Clock className="h-3 w-3 shrink-0" />
                    <span>Tạo {formatRelativeTime(artifact.created_at)}</span>
                </div>

                {/* Kebab action menu anchor */}
                <div className="absolute top-3.5 right-3.5" ref={menuRef}>
                    <button
                        type="button"
                        onClick={handleKebabClick}
                        className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-655 transition cursor-pointer"
                        title="Thao tác"
                    >
                        <MoreVertical className="h-4 w-4" />
                    </button>

                    {isMenuOpen && (
                        <div className="absolute right-0 mt-1 w-32 bg-white border border-slate-150 rounded-xl shadow-lg py-1 z-35 font-sans">
                            <button
                                type="button"
                                onClick={handleDeleteTrigger}
                                className="w-full px-3 py-2 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50 flex items-center gap-2 transition cursor-pointer"
                            >
                                <Trash2 className="h-3.5 w-3.5 text-rose-455" />
                                Xóa bài tập
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {isDeleteOpen && (
                <DeleteArtifactModal
                    isOpen={isDeleteOpen}
                    notebookId={artifact.notebook_id}
                    artifactId={artifact.id}
                    artifactTitle={artifact.title}
                    onClose={() => setIsDeleteOpen(false)}
                    onDeleted={onDeleted}
                />
            )}
        </>
    )
}
