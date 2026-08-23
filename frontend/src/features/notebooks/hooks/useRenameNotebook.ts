import { useMutation, useQueryClient } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

interface RenameParams {
    id: number
    title: string
}

export function useRenameNotebook() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, title }: RenameParams) => notebooksApi.renameNotebook(id, title),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: notebooksKeys.all })
        },
    })
}
