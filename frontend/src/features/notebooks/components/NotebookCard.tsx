import { Link } from 'react-router-dom'
import { BookOpen, Sparkles, FileText, Clock } from 'lucide-react'
import type { Notebook } from '../api'
import { formatRelativeTime } from '../../../utils/formatters'

interface NotebookCardProps {
    notebook: Notebook
}

export function NotebookCard({ notebook }: NotebookCardProps) {
    const hasSubject = !!notebook.subject_name

    return (
        <Link
            to={`/me/workspace/${notebook.id}`}
            className="flex flex-col justify-between h-44 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-500 hover:shadow-md group"
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
    )
}
