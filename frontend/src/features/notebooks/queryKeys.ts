export const notebooksKeys = {
    all: ['notebooks'] as const,
    list: () => [...notebooksKeys.all, 'list'] as const,
    detail: (id: number) => [...notebooksKeys.all, 'detail', id] as const,
    artifactsList: (notebookId: number) => [...notebooksKeys.all, 'artifacts', 'list', notebookId] as const,
    artifactDetail: (notebookId: number, id: number) => [...notebooksKeys.all, 'artifacts', 'detail', notebookId, id] as const,
} as const
