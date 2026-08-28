import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'
import { toast } from 'react-hot-toast'

interface UseDeleteArtifactOptions {
    onSuccess?: () => void
}

export function useDeleteArtifact(notebookId: number, options?: UseDeleteArtifactOptions) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (artifactId: number) => notebooksApi.deleteArtifact(notebookId, artifactId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.artifactsList(notebookId),
            })
            options?.onSuccess?.()
        },
        onError: (err) => {
            const errorMsg = getApiErrorMessage(err, 'Không thể xóa bài trắc nghiệm. Vui lòng thử lại!')
            toast.error(errorMsg)
        },
    })
}
