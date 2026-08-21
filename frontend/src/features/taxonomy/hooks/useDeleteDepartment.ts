import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useDeleteDepartment() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: taxonomyApi.deleteDepartment,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
