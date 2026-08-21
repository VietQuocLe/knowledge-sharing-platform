import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useCreateDepartment() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: taxonomyApi.createDepartment,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
