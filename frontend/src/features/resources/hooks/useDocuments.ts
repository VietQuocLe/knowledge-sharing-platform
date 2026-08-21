import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '../api'
import { documentsKeys } from '../queryKeys'

export function useDocuments(params?: {
    subjectId?: number
    resourceType?: string
    page?: number
    size?: number
}) {
    return useQuery({
        queryKey: documentsKeys.listPaginated({
            subjectId: params?.subjectId,
            page: params?.page,
            type: params?.resourceType,
        }),
        queryFn: () => resourcesApi.getDocumentList(params),
    })
}
