import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useCreateMajor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: taxonomyApi.createMajor,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
