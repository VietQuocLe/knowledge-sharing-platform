import { useQuery } from '@tanstack/react-query'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function useDepartments() {
    return useQuery({
        queryKey: taxonomyKeys.departmentsList(),
        queryFn: taxonomyApi.getDepartments,
    })
}
