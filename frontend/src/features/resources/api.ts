import { createJsonRequest } from '../../api/apiClient'

// ─── Active Types (Document domain) ────────────────────────────────────────

export const ResourceType = {
  EXAM: 'EXAM',
  SLIDE: 'SLIDE',
  DOCUMENT: 'DOCUMENT',
  VIDEO: 'VIDEO',
  AUDIO: 'AUDIO',
  LINK: 'LINK',
  AI_ARTIFACT: 'AI_ARTIFACT',
} as const

export type ResourceType = (typeof ResourceType)[keyof typeof ResourceType]

export const DocumentStatus = {
  DRAFT: 'DRAFT',
  PUBLIC: 'PUBLIC',
  DELETED: 'DELETED',
} as const

export type DocumentStatus = (typeof DocumentStatus)[keyof typeof DocumentStatus]

export interface Asset {
  id: number
  document_id: number | null
  notebook_id: number | null
  file_name: string
  file_path: string
  file_type: string
  size: number
}

export interface Document {
  id: number
  title: string
  description: string | null
  subject_id: number
  resource_type: ResourceType
  status: DocumentStatus
  created_by: number
  created_at: string
  assets: Asset[]
}

export interface DocumentPageResponse {
  items: Document[]
  total: number
  page: number
  size: number
}

export interface AssetDownloadResponse {
  download_url: string
  file_name: string
  expires_in_seconds: number
}

export interface UploadConfig {
  max_file_size_mb: number
  max_assets_per_resource: number
  allowed_upload_file_types: string[]
}

// ─── Active API calls ───────────────────────────────────────────────────────

export const resourcesApi = {
  getDocumentList: async (params?: {
    subjectId?: number
    resourceType?: string
    page?: number
    size?: number
  }): Promise<DocumentPageResponse> => {
    const queryParams: Record<string, unknown> = {
      page: params?.page ?? 1,
      size: params?.size ?? 20,
    }
    if (params?.subjectId !== undefined) queryParams.subject_id = params.subjectId
    if (params?.resourceType !== undefined) queryParams.resource_type = params.resourceType

    return createJsonRequest({ method: 'GET', url: '/documents/', params: queryParams })
  },

  getDocumentDetail: async (id: number): Promise<Document> => {
    return createJsonRequest({ method: 'GET', url: `/documents/${id}` })
  },

  getAssetDownloadUrl: async (
    documentId: number,
    assetId: number,
  ): Promise<AssetDownloadResponse> => {
    return createJsonRequest({
      method: 'GET',
      url: `/documents/${documentId}/assets/${assetId}/download`,
    })
  },

  getUploadConfig: async (): Promise<UploadConfig> => {
    return createJsonRequest({ method: 'GET', url: '/config/upload' })
  },
}

// ─── [PAUSED - Admin branch] ─────────────────────────────────────────────────
// The following types and API calls belong to the Admin/contribution flow.
// They are kept here for when the Admin branch is re-activated.
//
// export const VisibilityEnum = { PRIVATE, PENDING_REVIEW, PUBLIC } as const
// export type VisibilityEnum = ...
// export const ResourceStatus = { PROCESSING, READY, FAILED, DELETED } as const
// export type ResourceStatus = ...
// export interface Resource { id, title, description, resource_type, owner_id,
//   subject_id, visibility, status, created_at, rejection_reason,
//   metadata_json, assets }
// export interface ResourceCreatePayload { title, description?, subject_id, resource_type }
//
// resourcesApi.getMyResources        → GET /resources/me
// resourcesApi.getMyResourceById     → GET /resources/me/:id
// resourcesApi.createResource        → POST /resources/
// resourcesApi.uploadResourceAsset   → POST /resources/:id/assets
// resourcesApi.submitResourceForReview → POST /resources/:id/submit-review
// resourcesApi.getAdminResources     → GET /resources/admin
// resourcesApi.approveResource       → POST /resources/:id/approve
// resourcesApi.rejectResource        → POST /resources/:id/reject
// resourcesApi.deleteResource        → DELETE /resources/:id
