/**
 * Query Key Factory for Resources
 * Convention: keys are organized hierarchically for better cache invalidation
 */

export const resourcesKeys = {
  all: ['resources'] as const,

  // Public resource list (searchable, paginated, filterable by subject/type)
  list: () => [...resourcesKeys.all, 'list'] as const,
  listPaginated: (params?: { subjectId?: number; page?: number; type?: string }) =>
    params
      ? [...resourcesKeys.list(), params]
      : [...resourcesKeys.list()],

  // Resource details
  detail: () => [...resourcesKeys.all, 'detail'] as const,
  detailById: (id: number) => [...resourcesKeys.detail(), id] as const,

  // Current user's resources (my resources)
  me: () => [...resourcesKeys.all, 'me'] as const,
  myList: () => [...resourcesKeys.me(), 'list'] as const,
  myListPaginated: (params?: { page?: number; type?: string }) =>
    params ? [...resourcesKeys.myList(), params] : [...resourcesKeys.myList()],
  myDetail: () => [...resourcesKeys.me(), 'detail'] as const,
  myDetailById: (id: number) => [...resourcesKeys.myDetail(), id] as const,

  // Admin moderation/management
  adminList: () => [...resourcesKeys.all, 'adminList'] as const,
  adminListFiltered: (params?: { visibility?: string }) =>
    params
      ? [...resourcesKeys.adminList(), params]
      : resourcesKeys.adminList(),
} as const
