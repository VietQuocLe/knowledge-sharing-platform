import { Check, X } from 'lucide-react'
import type { QuizQuestion } from '../../api'

interface QuizQuestionItemProps {
    question: QuizQuestion
    index: number
    selectedAnswer?: string
    onSelect: (key: 'A' | 'B' | 'C' | 'D') => void
}

export function QuizQuestionItem({
    question,
    index,
    selectedAnswer,
    onSelect,
}: QuizQuestionItemProps) {
    const isAnswered = Boolean(selectedAnswer)
    const isUserCorrect = selectedAnswer === question.correct_answer

    return (
        <div className="border border-slate-150 rounded-2xl p-5 bg-white shadow-3xs font-sans space-y-4 transition duration-200">
            {/* Header: Question label and Status badge */}
            <div className="flex items-center justify-between gap-3 flex-shrink-0">
                <span className="text-[11px] font-extrabold text-slate-800 uppercase tracking-wider">
                    Câu {index + 1}
                </span>

                {isAnswered && (
                    <span
                        className={`px-2.5 py-0.5 rounded-lg text-[9px] font-extrabold uppercase tracking-wide flex items-center gap-1 ${isUserCorrect
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-150'
                                : 'bg-rose-50 text-rose-700 border border-rose-150'
                            }`}
                    >
                        {isUserCorrect ? (
                            <>
                                <Check className="h-3 w-3 shrink-0" />
                                <span>Chính xác</span>
                            </>
                        ) : (
                            <>
                                <X className="h-3 w-3 shrink-0" />
                                <span>Chưa đúng</span>
                            </>
                        )}
                    </span>
                )}
            </div>

            {/* Question Text */}
            <h4 className="text-xs font-bold text-slate-800 leading-relaxed">
                {question.question}
            </h4>

            {/* Options grid */}
            <div className="grid grid-cols-1 gap-3 pt-1">
                {question.options.map((opt) => {
                    const optKey = opt.key
                    const isSelected = selectedAnswer === optKey
                    const isCorrectOption = optKey === question.correct_answer

                    // Styling state calculations
                    let cardStyle = 'border-slate-205 bg-white text-slate-705 shadow-3xs hover:border-sky-300 hover:bg-slate-50 cursor-pointer'
                    let badgeStyle = 'bg-slate-100 text-slate-500 border border-slate-200'
                    let badgeValue: React.ReactNode = optKey

                    if (isAnswered) {
                        if (isSelected && isCorrectOption) {
                            // User selected + correct
                            cardStyle = 'border-emerald-500 bg-emerald-50/60 text-emerald-900 font-medium'
                            badgeStyle = 'bg-emerald-500 text-white'
                            badgeValue = <Check className="h-3.5 w-3.5" />
                        } else if (isSelected && !isCorrectOption) {
                            // User selected + incorrect
                            cardStyle = 'border-rose-500 bg-rose-50/60 text-rose-900 font-medium'
                            badgeStyle = 'bg-rose-500 text-white'
                            badgeValue = <X className="h-3.5 w-3.5" />
                        } else if (!isSelected && isCorrectOption) {
                            // Correct answer (but user did not select it)
                            cardStyle = 'border-emerald-500 bg-emerald-50/40 text-emerald-800'
                            badgeStyle = 'bg-emerald-500 text-white'
                            badgeValue = optKey
                        } else {
                            // Other options unselected
                            cardStyle = 'opacity-50 border-slate-200 bg-slate-50 text-slate-400'
                            badgeStyle = 'bg-slate-200 text-slate-400'
                        }
                    }

                    return (
                        <div
                            key={optKey}
                            onClick={() => {
                                if (!isAnswered) {
                                    onSelect(optKey)
                                }
                            }}
                            className={`flex items-center gap-3 p-3.5 rounded-xl border text-xs transition duration-150 ${cardStyle}`}
                        >
                            <span className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${badgeStyle}`}>
                                {badgeValue}
                            </span>
                            <span className="leading-snug break-words">{opt.text}</span>
                        </div>
                    )
                })}
            </div>

            {/* Explanation box */}
            {isAnswered && question.explanation && (
                <div className="bg-slate-50/80 border border-slate-150 rounded-xl p-4 text-[11px] leading-relaxed text-slate-600 space-y-1 animate-in fade-in duration-200">
                    <span className="font-extrabold text-slate-700 uppercase tracking-wide text-[9px]">
                        Giải thích đáp án
                    </span>
                    <p className="font-medium text-slate-600">{question.explanation}</p>
                </div>
            )}
        </div>
    )
}
