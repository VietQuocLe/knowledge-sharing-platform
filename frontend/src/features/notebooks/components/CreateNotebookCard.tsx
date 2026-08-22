import { Plus } from 'lucide-react'

interface CreateNotebookCardProps {
    onClick: () => void
}

export function CreateNotebookCard({ onClick }: CreateNotebookCardProps) {
    return (
        <button
            onClick={onClick}
            className="flex flex-col items-center justify-center h-44 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-5 shadow-sm hover:border-indigo-500 hover:bg-indigo-50/30 group transition focus:outline-none"
        >
            <div className="p-3 rounded-full bg-slate-100 group-hover:bg-indigo-100 group-hover:scale-110 transition text-slate-400 group-hover:text-indigo-600">
                <Plus className="h-6 w-6" />
            </div>
            <span className="mt-4 font-semibold text-sm text-slate-500 group-hover:text-indigo-600 transition">
                Tạo sổ ghi chú mới
            </span>
        </button>
    )
}
