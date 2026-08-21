import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'
import type { DepartmentPayload } from '../api'

export function useUpdateDepartment() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: DepartmentPayload }) =>
            taxonomyApi.updateDepartment(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
