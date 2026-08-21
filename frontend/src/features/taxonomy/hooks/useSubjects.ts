import { useQuery } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useSubjects(majorId?: number | null) {
    return useQuery({
        queryKey: taxonomyKeys.subjectsList(majorId ?? undefined),
        queryFn: () => {
            if (majorId !== undefined && majorId !== null) {
                return taxonomyApi.getSubjectsByMajor(majorId)
            }
            return taxonomyApi.getSubjects()
        },
        enabled: majorId === undefined || (majorId !== null && majorId > 0),
    })
}
