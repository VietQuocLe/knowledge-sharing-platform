import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Loader2 } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { useRenameNotebook } from '../hooks/useRenameNotebook'
import type { Notebook } from '../api'
import { toast } from 'react-hot-toast'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'

interface RenameNotebookModalProps {
    isOpen: boolean
    notebook: Notebook
    onClose: () => void
}

interface FormValues {
    title: string
}

export function RenameNotebookModal({ isOpen, notebook, onClose }: RenameNotebookModalProps) {
    const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<FormValues>({
        defaultValues: {
            title: notebook.title,
        },
    })

    // Update form values if notebook changes
    useEffect(() => {
        if (isOpen) {
            setValue('title', notebook.title)
        }
    }, [isOpen, notebook.title, setValue])

    const { mutate: renameNotebook, isPending } = useRenameNotebook()

    const handleClose = () => {
        reset()
        onClose()
    }

    const onSubmit = (data: FormValues) => {
        const trimmedTitle = data.title.trim()
        renameNotebook(
            {
                id: notebook.id,
                title: trimmedTitle,
            },
            {
                onSuccess: () => {
                    toast.success('Đã đổi tên sổ ghi chú thành công!')
                    handleClose()
                },
                onError: (err: any) => {
                    const errMsg = getApiErrorMessage(err, 'Không thể đổi tên sổ ghi chú. Vui lòng thử lại!')
                    toast.error(errMsg)
                },
            }
        )
    }

    return (
        <Modal isOpen={isOpen} title="Đổi tên sổ ghi chú">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Tên sổ ghi chú mới <span className="text-rose-500">*</span>
                    </label>
                    <input
                        type="text"
                        {...register('title', {
                            required: 'Tên sổ ghi chú không được để trống',
                            maxLength: { value: 500, message: 'Tên không được vượt quá 500 ký tự' },
                        })}
                        placeholder="Nhập tên sổ ghi chú mới"
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
                        {isPending ? 'Đang thực hiện...' : 'Lưu lại'}
                    </button>
                </div>
            </form>
        </Modal>
    )
}
