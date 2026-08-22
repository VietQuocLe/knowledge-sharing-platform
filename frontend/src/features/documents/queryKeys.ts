/**
 * Query Key Factory for Documents
 * Convention: keys are organized hierarchically for better cache invalidation
 */

export const documentsKeys = {
  all: ['documents'] as const,

  uploadConfig: () => [...documentsKeys.all, 'uploadConfig'] as const,

  // Public document list (paginated, filterable by subject/type)
  list: () => [...documentsKeys.all, 'list'] as const,
  listPaginated: (params?: { subjectId?: number; page?: number; type?: string }) =>
    params ? [...documentsKeys.list(), params] : [...documentsKeys.list()],

  // Document details
  detail: () => [...documentsKeys.all, 'detail'] as const,
  detailById: (id: number) => [...documentsKeys.detail(), id] as const,
} as const
