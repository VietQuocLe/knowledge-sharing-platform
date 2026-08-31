import type { ResourceType } from '../features/documents/api'

/**
 * Maps raw resource type to user-friendly Vietnamese label
 */
export function formatResourceType(type: ResourceType | string): string {
    switch (type) {
        case 'SLIDE':
        case 'LECTURE':
            return 'Bài giảng / Slide'
        case 'EXAM':
            return 'Bài tập / Lab'
        case 'DOCUMENT':
        case 'REFERENCE':
            return 'Tài liệu tham khảo'
        case 'SYLLABUS':
            return 'Đề cương chi tiết'
        case 'VIDEO':
            return 'Video bài giảng'
        case 'AUDIO':
            return 'Audio'
        case 'LINK':
            return 'Liên kết ngoài'
        case 'AI_ARTIFACT':
            return 'Tài nguyên AI'
        default:
            return type || 'Tài liệu'
    }
}

/**
 * Format file size from bytes to human-readable string
 */
export function formatFileSize(bytes: number | undefined | null): string {
    if (bytes === undefined || bytes === null || isNaN(bytes)) return '0 B'
    if (bytes === 0) return '0 B'

    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * Format date string to relative time (Vietnamese) or absolute date if older than 7 days
 */
export function formatRelativeTime(dateStr: string | Date | undefined | null): string {
    if (!dateStr) return ''

    const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
    if (isNaN(date.getTime())) return ''

    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffSecs < 60) {
        return 'Vừa xong'
    }
    if (diffMins < 60) {
        return `${diffMins} phút trước`
    }
    if (diffHours < 24) {
        return `${diffHours} giờ trước`
    }
    if (diffDays < 7) {
        return `${diffDays} ngày trước`
    }

    // Fallback to absolute standard Vietnamese date format: dd/MM/yyyy HH:mm
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')

    return `${day}/${month}/${year} ${hours}:${minutes}`
}
