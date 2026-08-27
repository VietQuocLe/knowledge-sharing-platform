import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Loader2 } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { notebooksApi } from '../api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'

interface RenameSessionModalProps {
    isOpen: boolean
    notebookId: number
    session: { id: number; title: string }
    onClose: () => void
}

interface FormValues {
    title: string
}

export function RenameSessionModal({ isOpen, notebookId, session, onClose }: RenameSessionModalProps) {
    const queryClient = useQueryClient()
    const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<FormValues>({
        defaultValues: {
            title: session.title,
        },
    })

    useEffect(() => {
        if (isOpen) {
            setValue('title', session.title)
        }
    }, [isOpen, session.title, setValue])

    const { mutate: renameSession, isPending } = useMutation({
        mutationFn: ({ title }: { title: string }) => notebooksApi.renameSession(notebookId, session.id, title),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ['notebooks', notebookId, 'sessions']
            })
            toast.success('Đã đổi tên cuộc hội thoại thành công!')
            handleClose()
        },
        onError: (err: any) => {
            const errMsg = getApiErrorMessage(err, 'Không thể đổi tên cuộc hội thoại. Vui lòng thử lại!')
            toast.error(errMsg)
        }
    })

    const handleClose = () => {
        reset()
        onClose()
    }

    const onSubmit = (data: FormValues) => {
        const trimmedTitle = data.title.trim()
        renameSession({ title: trimmedTitle })
    }

    return (
        <Modal isOpen={isOpen} title="Đổi tên cuộc hội thoại">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Tên hội thoại mới <span className="text-rose-500">*</span>
                    </label>
                    <input
                        type="text"
                        {...register('title', {
                            required: 'Tên cuộc hội thoại không được để trống',
                            maxLength: { value: 500, message: 'Tên không được vượt quá 500 ký tự' },
                        })}
                        placeholder="Nhập tên cuộc hội thoại mới"
                        className={`w-full rounded-xl border py-2.5 px-4 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 transition ${errors.title
                            ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20'
                            : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-500/20'
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
                        className="px-4 py-2 text-sm font-medium text-slate-650 hover:bg-slate-100 rounded-xl transition"
                    >
                        Hủy
                    </button>
                    <button
                        type="submit"
                        disabled={isPending}
                        className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-705 active:bg-indigo-800 rounded-xl shadow-md shadow-indigo-600/10 hover:shadow-indigo-600/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                        {isPending ? 'Đang thực hiện...' : 'Lưu lại'}
                    </button>
                </div>
            </form>
        </Modal>
    )
}
