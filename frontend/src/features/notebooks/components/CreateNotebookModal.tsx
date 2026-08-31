import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { X, BookOpen, Loader2 } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { SubjectSearchInput } from '../../taxonomy/components/SubjectSearchInput'
import { useCreateNotebook } from '../hooks/useCreateNotebook'
import { toast } from 'react-hot-toast'

interface CreateNotebookModalProps {
    isOpen: boolean
    onClose: () => void
}

interface FormValues {
    title: string
}

export function CreateNotebookModal({ isOpen, onClose }: CreateNotebookModalProps) {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
        defaultValues: {
            title: '',
        },
    })

    const [selectedSubject, setSelectedSubject] = useState<{ id: number; name: string; code: string } | null>(null)
    const { mutate: createNotebook, isPending } = useCreateNotebook()

    const handleClose = () => {
        reset()
        setSelectedSubject(null)
        onClose()
    }

    const onSubmit = (data: FormValues) => {
        createNotebook(
            {
                title: data.title.trim(),
                subject_id: selectedSubject ? selectedSubject.id : null,
            },
            {
                onSuccess: () => {
                    toast.success('Đã tạo sổ ghi chú mới thành công!')
                    handleClose()
                },
                onError: (err: any) => {
                    const errMsg = err.response?.data?.detail || 'Không thể tạo sổ ghi chú. Vui lòng thử lại!'
                    toast.error(errMsg)
                },
            }
        )
    }

    return (
        <Modal isOpen={isOpen} title="Tạo sổ ghi chú mới">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Tên sổ ghi chú <span className="text-rose-500">*</span>
                    </label>
                    <input
                        type="text"
                        {...register('title', {
                            required: 'Tên sổ ghi chú không được để trống',
                            maxLength: { value: 500, message: 'Tên không được vượt quá 500 ký tự' },
                        })}
                        placeholder="Nhập tên sổ ghi chú (ví dụ: Học phần Đại Số, ôn thi cuối kỳ...)"
                        className={`w-full rounded-xl border py-2.5 px-4 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 transition ${errors.title
                            ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20'
                            : 'border-slate-200 focus:border-sky-500 focus:ring-sky-500/20'
                            }`}
                    />
                    {errors.title && (
                        <span className="text-xs text-rose-500 mt-1 block">
                            {errors.title.message}
                        </span>
                    )}
                </div>

                <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Môn học liên kết (Không bắt buộc)
                    </label>
                    {selectedSubject ? (
                        <div className="flex items-center justify-between rounded-xl border border-sky-100 bg-sky-50/50 px-4 py-2.5">
                            <div className="flex items-center gap-2.5 min-w-0">
                                <BookOpen className="h-4 w-4 shrink-0 text-sky-500" />
                                <span className="font-mono text-[9px] bg-sky-100 text-slate-800 border border-sky-200 px-1.5 py-0.5 rounded shrink-0">
                                    {selectedSubject.code}
                                </span>
                                <span className="text-sm text-slate-750 font-medium truncate">
                                    {selectedSubject.name}
                                </span>
                            </div>
                            <button
                                type="button"
                                onClick={() => setSelectedSubject(null)}
                                className="p-1 rounded-full text-slate-400 hover:bg-sky-100 hover:text-sky-600 transition shrink-0"
                            >
                                <X className="h-3.5 w-3.5" />
                            </button>
                        </div>
                    ) : (
                        <SubjectSearchInput
                            placeholder="Tìm kiếm môn học để liên kết..."
                            onSelect={(subject) => setSelectedSubject(subject)}
                        />
                    )}
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={handleClose}
                        className="px-4 py-2 text-sm font-medium text-slate-650 hover:bg-slate-100 rounded-xl transition cursor-pointer"
                    >
                        Hủy
                    </button>
                    <button
                        type="submit"
                        disabled={isPending}
                        className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-black hover:bg-slate-800 active:scale-[0.98] rounded-xl shadow-md shadow-slate-200 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                        {isPending ? 'Đang tạo...' : 'Tạo sổ'}
                    </button>
                </div>
            </form>
        </Modal>
    )
}
