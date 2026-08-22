import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi, type NotebookCreateInput } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useCreateNotebook() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (data: NotebookCreateInput) => notebooksApi.createNotebook(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: notebooksKeys.all })
        },
    })
}
