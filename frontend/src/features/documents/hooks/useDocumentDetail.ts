import { useQuery } from '@tanstack/react-query'
import { documentsApi } from '../api'
import { documentsKeys } from '../queryKeys'

export function useDocumentDetail(id: number | null) {
    return useQuery({
        queryKey: documentsKeys.detailById(id!),
        queryFn: () => documentsApi.getDocumentDetail(id!),
        enabled: id !== null,
    })
}
