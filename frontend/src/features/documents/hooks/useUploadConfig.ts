import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '../api'
import { documentsKeys } from '../queryKeys'

export function useUploadConfig() {
    return useQuery({
        queryKey: documentsKeys.uploadConfig(),
        queryFn: () => documentsApi.getUploadConfig(),
        staleTime: 60 * 60 * 1000, // 1 hour (almost static)
    })
}
