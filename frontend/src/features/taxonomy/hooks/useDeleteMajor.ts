import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useDeleteMajor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: taxonomyApi.deleteMajor,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
