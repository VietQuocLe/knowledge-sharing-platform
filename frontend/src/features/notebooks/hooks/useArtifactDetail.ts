import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { notebooksKeys } from '../queryKeys'

export function useArtifactDetail(notebookId: number, artifactId: number | null) {
    const validArtifactId = artifactId !== null && !isNaN(artifactId) && artifactId > 0;
    return useQuery({
        queryKey: notebooksKeys.artifactDetail(notebookId, artifactId || 0),
        queryFn: () => notebooksApi.getArtifactDetail(notebookId, artifactId!),
        enabled: !isNaN(notebookId) && notebookId > 0 && validArtifactId,
    })
}
