import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '../api'
import { resourcesKeys } from '../queryKeys'

export function useUploadConfig() {
    return useQuery({
        queryKey: resourcesKeys.uploadConfig(),
        queryFn: () => resourcesApi.getUploadConfig(),
        staleTime: 60 * 60 * 1000, // 1 hour (almost static)
    })
}
