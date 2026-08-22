/**
 * Query Key Factory for Taxonomy (Departments, Majors, Subjects)
 * Convention: keys are organized hierarchically for better cache invalidation
 */

export const taxonomyKeys = {
  all: ['taxonomy'] as const,

  // Departments
  departments: () => [...taxonomyKeys.all, 'departments'] as const,
  departmentsList: () => [...taxonomyKeys.departments(), 'list'] as const,
  departmentDetail: (id: number) => [...taxonomyKeys.departments(), id] as const,

  // Majors
  majors: () => [...taxonomyKeys.all, 'majors'] as const,
  majorsList: (departmentId?: number) =>
    departmentId
      ? [...taxonomyKeys.majors(), 'list', departmentId]
      : [...taxonomyKeys.majors(), 'list'],
  majorDetail: (id: number) => [...taxonomyKeys.majors(), id] as const,

  // Subjects
  subjects: () => [...taxonomyKeys.all, 'subjects'] as const,
  subjectsList: (majorId?: number) =>
    majorId
      ? [...taxonomyKeys.subjects(), 'list', majorId]
      : [...taxonomyKeys.subjects(), 'list'],
  subjectsSearch: (query: string) => [...taxonomyKeys.subjects(), 'search', query] as const,
  subjectDetail: (id: number) => [...taxonomyKeys.subjects(), id] as const,
} as const
