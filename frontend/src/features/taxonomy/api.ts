import { createJsonRequest } from '../../api/apiClient'

export interface Department {
  id: number
  name: string
}

export interface Major {
  id: number
  code: string
  name: string
  department_id: number
  department?: Department
}

export type SubjectCategory = 'GENERAL' | 'FOUNDATION' | 'SPECIALIZED' | 'ELECTIVE_CAPSTONE'

export interface Subject {
  id: number
  code: string
  name: string
  majors: Major[]
  category?: SubjectCategory
}

export type DepartmentPayload = { name: string }
export type MajorPayload = { code: string; name: string; department_id: number }
export type SubjectPayload = { code: string; name: string; department_id: number; major_ids: number[] }

export const taxonomyApi = {
  getDepartments: async (): Promise<Department[]> => {
    return createJsonRequest({
      method: 'GET',
      url: '/departments',
    })
  },

  getMajorsByDepartment: async (departmentId: number): Promise<Major[]> => {
    return createJsonRequest({
      method: 'GET',
      url: '/majors',
      params: { department_id: departmentId },
    })
  },

  getSubjectsByMajor: async (majorId: number): Promise<Subject[]> => {
    return createJsonRequest({
      method: 'GET',
      url: '/subjects',
      params: { major_id: majorId },
    })
  },

  getDepartmentById: async (id: number): Promise<Department> => {
    return createJsonRequest({
      method: 'GET',
      url: `/departments/${id}`,
    })
  },

  getMajorById: async (id: number): Promise<Major> => {
    return createJsonRequest({
      method: 'GET',
      url: `/majors/${id}`,
    })
  },

  getSubjectById: async (id: number): Promise<Subject> => {
    return createJsonRequest({
      method: 'GET',
      url: `/subjects/${id}`,
    })
  },

  createDepartment: async (data: DepartmentPayload): Promise<Department> =>
    createJsonRequest({ method: 'POST', url: '/departments/', data }),
  updateDepartment: async (id: number, data: DepartmentPayload): Promise<Department> =>
    createJsonRequest({ method: 'PUT', url: `/departments/${id}`, data }),
  deleteDepartment: async (id: number): Promise<void> =>
    createJsonRequest({ method: 'DELETE', url: `/departments/${id}` }),

  getMajors: async (): Promise<Major[]> => createJsonRequest({ method: 'GET', url: '/majors/' }),
  createMajor: async (data: MajorPayload): Promise<Major> =>
    createJsonRequest({ method: 'POST', url: '/majors/', data }),
  updateMajor: async (id: number, data: MajorPayload): Promise<Major> =>
    createJsonRequest({ method: 'PUT', url: `/majors/${id}`, data }),
  deleteMajor: async (id: number): Promise<void> =>
    createJsonRequest({ method: 'DELETE', url: `/majors/${id}` }),

  getSubjects: async (): Promise<Subject[]> => createJsonRequest({ method: 'GET', url: '/subjects/' }),
  searchSubjects: async (query: string, limit = 8): Promise<Subject[]> => {
    return createJsonRequest({
      method: 'GET',
      url: '/subjects/',
      params: { q: query, limit },
    })
  },
  createSubject: async (data: SubjectPayload): Promise<Subject> =>
    createJsonRequest({ method: 'POST', url: '/subjects/', data }),
  updateSubject: async (id: number, data: SubjectPayload): Promise<Subject> =>
    createJsonRequest({ method: 'PUT', url: `/subjects/${id}`, data }),
  deleteSubject: async (id: number): Promise<void> =>
    createJsonRequest({ method: 'DELETE', url: `/subjects/${id}` }),
}
