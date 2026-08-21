import { useQuery } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useMajors(departmentId?: number | null) {
    return useQuery({
        queryKey: taxonomyKeys.majorsList(departmentId ?? undefined),
        queryFn: () => {
            if (departmentId !== undefined && departmentId !== null) {
                return taxonomyApi.getMajorsByDepartment(departmentId)
            }
            return taxonomyApi.getMajors()
        },
        enabled: departmentId === undefined || (departmentId !== null && departmentId > 0),
    })
}
