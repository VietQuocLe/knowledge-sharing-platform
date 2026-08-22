import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useNotebooks() {
    return useQuery({
        queryKey: notebooksKeys.list(),
        queryFn: notebooksApi.getMyNotebooks,
    })
}
