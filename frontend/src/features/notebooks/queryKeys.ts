export const notebooksKeys = {
    all: ['notebooks'] as const,
    list: () => [...notebooksKeys.all, 'list'] as const,
    detail: (id: number) => [...notebooksKeys.all, 'detail', id] as const,
} as const
