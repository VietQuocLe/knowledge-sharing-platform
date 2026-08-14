import { createJsonRequest, createMultipartRequest } from '../../api/apiClient'

/** Allow up to 30 MB uploads on slower connections without hitting the default 10s timeout. */
const UPLOAD_REQUEST_TIMEOUT_MS = 120_000

export const ResourceType = {
  DOCUMENT: 'DOCUMENT',
  VIDEO: 'VIDEO',
  AUDIO: 'AUDIO',
  LINK: 'LINK',
  AI_ARTIFACT: 'AI_ARTIFACT',
} as const

export type ResourceType = (typeof ResourceType)[keyof typeof ResourceType]

export const VisibilityEnum = {
  PRIVATE: 'PRIVATE',
  PENDING_REVIEW: 'PENDING_REVIEW',
  PUBLIC: 'PUBLIC',
} as const

export type VisibilityEnum = (typeof VisibilityEnum)[keyof typeof VisibilityEnum]

export const ResourceStatus = {
  PROCESSING: 'PROCESSING',
  READY: 'READY',
  FAILED: 'FAILED',
  DELETED: 'DELETED',
} as const

export type ResourceStatus = (typeof ResourceStatus)[keyof typeof ResourceStatus]

export interface Asset {
  id: number
  resource_id: number
  file_name: string
  file_path: string
  file_type: string
  size: number
}

export interface Resource {
  id: number
  title: string
  description: string | null
  resource_type: ResourceType
  owner_id: number
  subject_id: number | null
  visibility: VisibilityEnum
  status: ResourceStatus
  created_at: string
  rejection_reason: string | null
  metadata_json: Record<string, unknown>
  assets: Asset[]
}

export interface ResourcePageResponse {
  items: Resource[]
  total: number
  page: number
  size: number
}

export interface ResourceCreatePayload {
  title: string
  description?: string
  subject_id: number
  resource_type: ResourceType
}

export const resourcesApi = {
  getResourceList: async (params?: {
    subjectId?: number
    resourceType?: string
    page?: number
    size?: number
  }): Promise<ResourcePageResponse> => {
    const queryParams: Record<string, unknown> = {
      page: params?.page ?? 1,
      size: params?.size ?? 20,
    }

    if (params?.subjectId !== undefined) {
      queryParams.subject_id = params.subjectId
    }
    if (params?.resourceType !== undefined) {
      queryParams.resource_type = params.resourceType
    }

    return createJsonRequest({
      method: 'GET',
      url: '/resources',
      params: queryParams,
    })
  },

  getResourceDetail: async (id: number): Promise<Resource> => {
    return createJsonRequest({
      method: 'GET',
      url: `/resources/${id}`,
    })
  },

  getMyResources: async (params?: {
    subjectId?: number
    resourceType?: string
    page?: number
    size?: number
  }): Promise<ResourcePageResponse> => {
    const queryParams: Record<string, unknown> = {
      page: params?.page ?? 1,
      size: params?.size ?? 20,
    }

    if (params?.subjectId !== undefined) {
      queryParams.subject_id = params.subjectId
    }
    if (params?.resourceType !== undefined) {
      queryParams.resource_type = params.resourceType
    }

    return createJsonRequest({
      method: 'GET',
      url: '/resources/me',
      params: queryParams,
    })
  },

  getMyResourceById: async (id: number): Promise<Resource> => {
    return createJsonRequest({
      method: 'GET',
      url: `/resources/me/${id}`,
    })
  },

  createResource: async (payload: ResourceCreatePayload): Promise<Resource> => {
    return createJsonRequest({
      method: 'POST',
      url: '/resources/',
      data: payload,
    })
  },

  uploadResourceAsset: async (resourceId: number, file: File): Promise<Resource> => {
    const formData = new FormData()
    formData.append('file', file)

    return createMultipartRequest({
      method: 'POST',
      url: `/resources/${resourceId}/assets`,
      data: formData,
      timeout: UPLOAD_REQUEST_TIMEOUT_MS,
    })
  },

  submitResourceForReview: async (resourceId: number): Promise<Resource> => {
    return createJsonRequest({
      method: 'POST',
      url: `/resources/${resourceId}/submit-review`,
    })
  },

  getAdminResources: async (params?: { visibility?: VisibilityEnum }): Promise<ResourcePageResponse> => {
    return createJsonRequest({
      method: 'GET',
      url: '/resources/admin',
      params: { visibility: params?.visibility, page: 1, size: 100 },
    })
  },

  approveResource: async (resourceId: number): Promise<Resource> => {
    return createJsonRequest({ method: 'POST', url: `/resources/${resourceId}/approve` })
  },

  rejectResource: async (resourceId: number, reason: string): Promise<Resource> => {
    return createJsonRequest({ method: 'POST', url: `/resources/${resourceId}/reject`, data: { reason } })
  },

  deleteResource: async (resourceId: number): Promise<void> => {
    return createJsonRequest({ method: 'DELETE', url: `/resources/${resourceId}` })
  },
}
