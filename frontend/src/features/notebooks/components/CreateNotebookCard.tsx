import { Plus } from 'lucide-react'

interface CreateNotebookCardProps {
    onClick: () => void
}

export function CreateNotebookCard({ onClick }: CreateNotebookCardProps) {
    return (
        <button
            onClick={onClick}
            className="flex flex-col items-center justify-center h-44 rounded-2xl border-2 border-dashed border-slate-200/80 bg-[#F8F8F6] p-5 shadow-xs hover:border-slate-400 hover:bg-white group transition duration-250 focus:outline-none cursor-pointer"
        >
            <div className="p-3 rounded-2xl bg-white border border-slate-200/80 group-hover:bg-black group-hover:border-black group-hover:scale-105 transition duration-250 text-slate-500 group-hover:text-white shadow-3xs">
                <Plus className="h-5 w-5" />
            </div>
            <span className="mt-3.5 font-bold text-xs text-slate-600 group-hover:text-slate-900 transition">
                Tạo sổ ghi chú mới
            </span>
        </button>
    )
}
