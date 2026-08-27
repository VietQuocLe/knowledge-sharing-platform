import { createJsonRequest, createMultipartRequest } from '../../api/apiClient'

export interface Notebook {
    id: number
    title: string
    subject_id: number | null
    subject_name: string | null
    source_count: number
    created_at: string
    updated_at: string
}

export interface NotebookSource {
    id: number
    type: 'local' | 'saved'
    title: string
    file_type: string
    size: number | null
    created_at: string
}

export interface NotebookDetail {
    id: number
    title: string
    subject_id: number | null
    subject_name: string | null
    sources_count: number
    max_sources: number
    sources: NotebookSource[]
    created_at: string
    updated_at: string
}

export interface NotebookCreateInput {
    title: string
    subject_id?: number | null
}

export const notebooksApi = {
    getMyNotebooks: async (): Promise<Notebook[]> => {
        return createJsonRequest({ method: 'GET', url: '/notebooks/me' })
    },

    getNotebookDetail: async (id: number): Promise<NotebookDetail> => {
        return createJsonRequest({ method: 'GET', url: `/notebooks/${id}` })
    },

    createNotebook: async (data: NotebookCreateInput): Promise<Notebook> => {
        return createJsonRequest({
            method: 'POST',
            url: '/notebooks/',
            data,
        })
    },

    renameNotebook: async (id: number, title: string): Promise<Notebook> => {
        return createJsonRequest({
            method: 'PATCH',
            url: `/notebooks/${id}`,
            data: { title },
        })
    },

    deleteNotebook: async (id: number): Promise<void> => {
        return createJsonRequest({
            method: 'DELETE',
            url: `/notebooks/${id}`,
        })
    },

    saveDocument: async (notebookId: number, documentId: number): Promise<any> => {
        return createJsonRequest({
            method: 'POST',
            url: `/notebooks/${notebookId}/saved-documents`,
            data: { document_id: documentId },
        })
    },

    unsaveDocument: async (notebookId: number, documentId: number): Promise<void> => {
        return createJsonRequest({
            method: 'DELETE',
            url: `/notebooks/${notebookId}/saved-documents/${documentId}`,
        })
    },

    uploadAsset: async (notebookId: number, file: File): Promise<any> => {
        const formData = new FormData()
        formData.append('file', file)
        return createMultipartRequest({
            method: 'POST',
            url: `/notebooks/${notebookId}/assets`,
            data: formData,
        })
    },

    deleteAsset: async (notebookId: number, assetId: number): Promise<void> => {
        return createJsonRequest({
            method: 'DELETE',
            url: `/notebooks/${notebookId}/assets/${assetId}`,
        })
    },

    downloadAsset: async (notebookId: number, assetId: number): Promise<{ download_url: string; file_name: string }> => {
        return createJsonRequest({
            method: 'GET',
            url: `/notebooks/${notebookId}/assets/${assetId}/download`,
        })
    },

    createSession: async (notebookId: number, title?: string): Promise<{ id: number; title: string }> => {
        return createJsonRequest({
            method: 'POST',
            url: `/notebooks/${notebookId}/sessions`,
            data: { title },
        })
    },

    listSessions: async (notebookId: number): Promise<Array<{ id: number; title: string }>> => {
        return createJsonRequest({
            method: 'GET',
            url: `/notebooks/${notebookId}/sessions`,
        })
    },

    getSessionMessages: async (notebookId: number, sessionId: number): Promise<Array<{ id: number; session_id: number; role: 'user' | 'assistant'; content: string; citations?: any; created_at: string }>> => {
        return createJsonRequest({
            method: 'GET',
            url: `/notebooks/${notebookId}/sessions/${sessionId}/messages`,
        })
    },

    renameSession: async (notebookId: number, sessionId: number, title: string): Promise<{ id: number; title: string }> => {
        return createJsonRequest({
            method: 'PATCH',
            url: `/notebooks/${notebookId}/sessions/${sessionId}`,
            data: { title },
        })
    },

    deleteSession: async (notebookId: number, sessionId: number): Promise<void> => {
        return createJsonRequest({
            method: 'DELETE',
            url: `/notebooks/${notebookId}/sessions/${sessionId}`,
        })
    },
}
