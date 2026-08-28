import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useArtifacts(notebookId: number) {
    return useQuery({
        queryKey: notebooksKeys.artifactsList(notebookId),
        queryFn: () => notebooksApi.getArtifacts(notebookId),
        enabled: !isNaN(notebookId) && notebookId > 0,
    })
}
