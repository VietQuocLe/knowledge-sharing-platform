import { useMutation, useQueryClient } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'
import type { MajorPayload } from '../api'

export function useUpdateMajor() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: MajorPayload }) =>
            taxonomyApi.updateMajor(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })
        },
    })
}
