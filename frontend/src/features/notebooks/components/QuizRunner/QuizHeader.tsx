import { RotateCcw } from 'lucide-react'

interface QuizHeaderProps {
    title: string
    correctCount: number
    totalQuestions: number
    onReset: () => void
}

export function QuizHeader({
    title,
    correctCount,
    totalQuestions,
    onReset,
}: QuizHeaderProps) {
    return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100 flex-shrink-0 font-sans">
            {/* Title */}
            <div className="min-w-0 flex-1">
                <h1 className="text-lg font-extrabold text-slate-900 tracking-tight leading-snug break-words">
                    {title}
                </h1>
            </div>

            {/* Actions & Stats */}
            <div className="flex items-center gap-3 shrink-0 justify-between sm:justify-end">
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-extrabold bg-indigo-50 border border-indigo-100 text-indigo-700 select-none shadow-3xs">
                    Điểm số: {correctCount} / {totalQuestions}
                </span>

                <button
                    onClick={onReset}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-indigo-650 hover:bg-slate-50 border border-slate-200 active:bg-slate-100 px-3 py-1.5 rounded-xl transition cursor-pointer shadow-3xs"
                    title="Làm lại tất cả câu hỏi"
                >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Làm lại từ đầu</span>
                </button>
            </div>
        </div>
    )
}
