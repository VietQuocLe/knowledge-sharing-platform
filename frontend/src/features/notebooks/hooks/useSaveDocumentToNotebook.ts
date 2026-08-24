import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useSaveDocumentToNotebook(notebookId: number) {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (documentId: number) => notebooksApi.saveDocument(notebookId, documentId),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: notebooksKeys.detail(notebookId),
            })
        },
    })
}
