import { useQuery } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useSearchSubjects(query: string, limit = 8) {
    const trimmed = query.trim()
    return useQuery({
        queryKey: taxonomyKeys.subjectsSearch(trimmed),
        queryFn: () => taxonomyApi.searchSubjects(trimmed, limit),
        enabled: trimmed.length >= 2,
        staleTime: 5000, // Cache results for 5 seconds
    })
}
