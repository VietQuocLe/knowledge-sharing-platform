export const notebooksKeys = {
    all: ['notebooks'] as const,
    list: () => [...notebooksKeys.all, 'list'] as const,
} as const
