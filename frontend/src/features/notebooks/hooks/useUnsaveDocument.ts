import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useUnsaveDocument(notebookId: number) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (documentId: number) => notebooksApi.unsaveDocument(notebookId, documentId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.detail(notebookId)
            })
        }
    })
}
