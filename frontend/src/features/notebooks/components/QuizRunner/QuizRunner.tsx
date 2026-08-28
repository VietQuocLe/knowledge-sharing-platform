import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { useArtifactDetail } from '../../hooks/useArtifactDetail'
import { QuizHeader } from './QuizHeader'
import { QuizQuestionItem } from './QuizQuestionItem'

interface QuizRunnerProps {
    notebookId: number
    artifactId: number
    onBack: () => void
}

export function QuizRunner({
    notebookId,
    artifactId,
    onBack,
}: QuizRunnerProps) {
    const { data: artifact, isLoading, error } = useArtifactDetail(notebookId, artifactId)
    const [userAnswers, setUserAnswers] = useState<Record<number, string>>({})

    const is404 = (error as any)?.response?.status === 404

    // Fire toast on 404 to draw attention
    useEffect(() => {
        if (error && is404) {
            toast.error('Bài trắc nghiệm không còn tồn tại')
        }
    }, [error, is404])

    // Loading Skeletons
    if (isLoading) {
        return (
            <div className="flex-1 flex flex-col gap-6 animate-pulse w-full py-6 font-sans">
                {/* Header Skeleton */}
                <div className="flex flex-col gap-3 pb-5 border-b border-slate-100 flex-shrink-0">
                    <div className="flex justify-between">
                        <div className="h-6 w-32 bg-slate-150 rounded-lg" />
                        <div className="h-8 w-24 bg-slate-150 rounded-lg" />
                    </div>
                    <div className="flex justify-between items-center mt-2">
                        <div className="h-8 w-64 bg-slate-150 rounded-lg" />
                        <div className="h-6 w-20 bg-slate-150 rounded-lg" />
                    </div>
                </div>
                {/* Question Items Skeletons */}
                <div className="space-y-6">
                    {[1, 2].map((i) => (
                        <div key={i} className="border border-slate-150 rounded-2xl p-5 space-y-4">
                            <div className="flex justify-between">
                                <div className="h-5 w-24 bg-slate-150 rounded-lg" />
                                <div className="h-4 w-40 bg-slate-150 rounded-lg" />
                            </div>
                            <div className="h-5 w-[85%] bg-slate-150 rounded-lg animate-pulse" />
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                {[1, 2, 3, 4].map((j) => (
                                    <div key={j} className="h-10 bg-slate-100 rounded-xl" />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    // 404 or other errors redirect box
    if (error) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-150 rounded-2xl space-y-4 font-sans max-w-md mx-auto my-12 animate-in fade-in duration-200">
                <AlertCircle className="h-12 w-12 text-rose-500 shrink-0" />
                <div className="text-center space-y-1.5">
                    <h3 className="text-sm font-bold text-slate-800">
                        {is404 ? 'Bài trắc nghiệm không còn tồn tại' : 'Lỗi tải dữ liệu'}
                    </h3>
                    <p className="text-xs text-slate-500 leading-relaxed">
                        {is404
                            ? 'Không tìm thấy nội dung bài tập trắc nghiệm này. Bài có thể đã bị xóa ở nơi khác.'
                            : 'Không thể hiển thị bài ôn tập do trục trặc đường truyền.'}
                    </p>
                </div>
                <button
                    type="button"
                    onClick={onBack}
                    className="px-5 py-2.5 text-xs font-bold text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition cursor-pointer shadow-3xs"
                >
                    Đóng và Quay lại
                </button>
            </div>
        )
    }

    if (!artifact?.content) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-150 rounded-2xl space-y-4 font-sans max-w-md mx-auto my-12">
                <AlertCircle className="h-12 w-12 text-amber-500 shrink-0" />
                <div className="text-center space-y-1">
                    <h3 className="text-sm font-bold text-slate-800">Dữ liệu trống</h3>
                    <p className="text-xs text-slate-500 leading-relaxed">
                        Bài trắc nghiệm học tập này hiện không chứa bất kỳ câu hỏi nào.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={onBack}
                    className="px-4 py-2 text-xs font-bold text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition cursor-pointer"
                >
                    Quay lại
                </button>
            </div>
        )
    }

    const title = artifact.content.title || artifact.title || 'Bài tập ôn tập'
    const questions = artifact.content.questions || []
    const totalQuestions = questions.length
    const correctCount = questions.filter(
        (q) => userAnswers[q.id] === q.correct_answer
    ).length

    const handleSelectOption = (questionId: number, optionKey: 'A' | 'B' | 'C' | 'D') => {
        if (userAnswers[questionId]) return
        setUserAnswers((prev) => ({
            ...prev,
            [questionId]: optionKey,
        }))
    }

    const handleReset = () => {
        setUserAnswers({})
    }

    return (
        <div className="flex-1 flex flex-col gap-6 w-full py-4 overflow-y-auto pr-0.5">
            {/* Header Area */}
            <QuizHeader
                title={title}
                correctCount={correctCount}
                totalQuestions={totalQuestions}
                onReset={handleReset}
            />

            {/* Questions List */}
            <div className="space-y-6 pb-12">
                {questions.map((q, idx) => (
                    <QuizQuestionItem
                        key={q.id}
                        question={q}
                        index={idx}
                        selectedAnswer={userAnswers[q.id]}
                        onSelect={(key) => handleSelectOption(q.id, key)}
                    />
                ))}
            </div>
        </div>
    )
}
