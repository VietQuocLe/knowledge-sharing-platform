import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Sparkles, FileText, Clock, MoreVertical, Edit2, Trash2 } from 'lucide-react'
import type { Notebook } from '../api'
import { formatRelativeTime } from '../../../utils/formatters'
import { useClickOutside } from '../../../hooks/useClickOutside'
import { RenameNotebookModal } from './RenameNotebookModal'
import { DeleteNotebookConfirmModal } from './DeleteNotebookConfirmModal'

interface NotebookCardProps {
    notebook: Notebook
}

export function NotebookCard({ notebook }: NotebookCardProps) {
    const hasSubject = !!notebook.subject_name
    const [isDropdownOpen, setIsDropdownOpen] = useState(false)
    const [isRenameOpen, setIsRenameOpen] = useState(false)
    const [isDeleteOpen, setIsDeleteOpen] = useState(false)

    const dropdownRef = useClickOutside<HTMLDivElement>(() => setIsDropdownOpen(false))

    return (
        <>
            <Link
                to={`/me/workspace/${notebook.id}`}
                className="flex flex-col justify-between h-44 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-500 hover:shadow-md group relative"
            >
                <div>
                    <div className="flex items-start justify-between">
                        <div className={`p-2.5 rounded-xl transition group-hover:scale-110 ${hasSubject ? 'bg-indigo-50 text-indigo-600' : 'bg-amber-50 text-amber-500'
                            }`}>
                            {hasSubject ? (
                                <BookOpen className="h-5 w-5" />
                            ) : (
                                <Sparkles className="h-5 w-5" />
                            )}
                        </div>

                        <div className="relative" ref={dropdownRef}>
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault()
                                    e.stopPropagation()
                                    setIsDropdownOpen(!isDropdownOpen)
                                }}
                                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition shrink-0"
                            >
                                <MoreVertical className="h-5 w-5" />
                            </button>

                            {isDropdownOpen && (
                                <div className="absolute right-0 mt-1.5 w-36 rounded-xl border border-slate-200 bg-white py-1 shadow-lg z-10 text-sm text-slate-700 animate-in fade-in slide-in-from-top-1 duration-150">
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.preventDefault()
                                            e.stopPropagation()
                                            setIsRenameOpen(true)
                                            setIsDropdownOpen(false)
                                        }}
                                        className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 text-slate-705 transition font-medium"
                                    >
                                        <Edit2 className="h-4 w-4 text-slate-450" />
                                        <span>Đổi tên</span>
                                    </button>
                                    <button
                                        type="button"
                                        onClick={(e) => {
                                            e.preventDefault()
                                            e.stopPropagation()
                                            setIsDeleteOpen(true)
                                            setIsDropdownOpen(false)
                                        }}
                                        className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 text-rose-650 transition font-medium"
                                    >
                                        <Trash2 className="h-4 w-4 text-rose-450" />
                                        <span>Xóa</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    <h3 className="mt-4 font-semibold text-slate-800 line-clamp-1 group-hover:text-indigo-600 transition">
                        {notebook.title}
                    </h3>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-3">
                    <div className="flex items-center gap-1">
                        <FileText className="h-3.5 w-3.5 text-slate-400" />
                        <span>{notebook.source_count} tài liệu</span>
                    </div>
                    <div className="flex items-center gap-1 text-[11px]">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        <span>Cập nhật {formatRelativeTime(notebook.updated_at)}</span>
                    </div>
                </div>

            </Link>
            <RenameNotebookModal
                isOpen={isRenameOpen}
                notebook={notebook}
                onClose={() => setIsRenameOpen(false)}
            />
            <DeleteNotebookConfirmModal
                isOpen={isDeleteOpen}
                notebook={notebook}
                onClose={() => setIsDeleteOpen(false)}
            />
        </>
    )
}
