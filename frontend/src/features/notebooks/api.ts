import { createJsonRequest } from '../../api/apiClient'

export interface Notebook {
    id: number
    title: string
    subject_id: number | null
    subject_name: string | null
    source_count: number
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

    createNotebook: async (data: NotebookCreateInput): Promise<Notebook> => {
        return createJsonRequest({
            method: 'POST',
            url: '/notebooks/',
            data,
        })
    },
}
