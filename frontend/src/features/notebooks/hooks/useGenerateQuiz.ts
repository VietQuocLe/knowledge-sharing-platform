import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi, type QuizGenerateRequest, type ArtifactDetail } from '../api'
import { notebooksKeys } from '../queryKeys'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'
import { toast } from 'react-hot-toast'

interface UseGenerateQuizOptions {
    onSuccess?: (data: ArtifactDetail) => void
}

export function useGenerateQuiz(notebookId: number, options?: UseGenerateQuizOptions) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (data: QuizGenerateRequest) => notebooksApi.generateQuiz(notebookId, data),
        onSuccess: (data) => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.artifactsList(notebookId),
            })
            queryClient.setQueryData(
                notebooksKeys.artifactDetail(notebookId, data.id),
                data
            )
            options?.onSuccess?.(data)
        },
        onError: (err) => {
            const errorMsg = getApiErrorMessage(err, 'Không thể sinh bài trắc nghiệm. Vui lòng thử lại!')
            toast.error(errorMsg)
        },
    })
}
