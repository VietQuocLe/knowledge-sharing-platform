import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useUploadNotebookAsset(notebookId: number) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (file: File) => notebooksApi.uploadAsset(notebookId, file),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.detail(notebookId)
            })
        }
    })
}
