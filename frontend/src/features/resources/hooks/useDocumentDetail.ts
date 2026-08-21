import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '../api'
import { documentsKeys } from '../queryKeys'

export function useDocumentDetail(id: number | null) {
    return useQuery({
        queryKey: documentsKeys.detailById(id!),
        queryFn: () => resourcesApi.getDocumentDetail(id!),
        enabled: id !== null,
    })
}
