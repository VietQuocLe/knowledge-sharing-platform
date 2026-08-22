import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'

export function NotebookDetailPage() {
    const { notebookId } = useParams<{ notebookId: string }>()

    return (
        <div className="mx-auto max-w-xl px-4 py-16 text-center sm:px-6 lg:px-8">
            <div className="flex justify-center">
                <div className="p-4 rounded-2xl bg-indigo-50 text-indigo-650 animate-pulse">
                    <Sparkles className="h-10 w-10" />
                </div>
            </div>
            <h1 className="mt-6 text-2xl font-bold tracking-tight text-slate-900">
                AI Workspace Notebook
            </h1>
            <p className="mt-2 text-sm text-slate-500">
                Tính năng đang được phát triển (Sổ ghi chú ID: {notebookId})
            </p>
            <div className="mt-8 flex justify-center">
                <Link
                    to="/me/workspace"
                    className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 transition focus:outline-none"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Quay lại Workspace của tôi
                </Link>
            </div>
        </div>
    )
}
