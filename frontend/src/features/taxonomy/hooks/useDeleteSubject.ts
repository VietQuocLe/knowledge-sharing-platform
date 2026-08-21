import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useDeleteSubject() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: taxonomyApi.deleteSubject,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
