import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useDeleteNotebookAsset(notebookId: number) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (assetId: number) => notebooksApi.deleteAsset(notebookId, assetId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.detail(notebookId)
            })
        }
    })
}
