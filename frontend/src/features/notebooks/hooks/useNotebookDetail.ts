import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useNotebookDetail(id: number) {
    return useQuery({
        queryKey: notebooksKeys.detail(id),
        queryFn: () => notebooksApi.getNotebookDetail(id),
        enabled: !isNaN(id) && id > 0,
    })
}
