import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useDeleteNotebook() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (id: number) => notebooksApi.deleteNotebook(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: notebooksKeys.all })
        },
    })
}
