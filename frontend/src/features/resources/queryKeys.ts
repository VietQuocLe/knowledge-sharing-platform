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

  // [PAUSED - Admin branch] me / adminList keys removed until re-activated
  // me: () => [...documentsKeys.all, 'me'] as const,
  // myList: () => [...documentsKeys.me(), 'list'] as const,
  // myListPaginated: (params?) => ...
  // myDetail: () => [...documentsKeys.me(), 'detail'] as const,
  // myDetailById: (id: number) => ...
  // adminList: () => [...documentsKeys.all, 'adminList'] as const,
  // adminListFiltered: (params?) => ...
} as const

// Backwards-compat alias — existing code using `resourcesKeys` still compiles
/** @deprecated Use documentsKeys instead */
export const resourcesKeys = documentsKeys
