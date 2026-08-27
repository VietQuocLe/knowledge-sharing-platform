import { useEffect, useRef } from 'react'
import { FileText, ExternalLink, Download, X } from 'lucide-react'
import { Spinner } from '../../../components/ui/Spinner'

interface PdfPreviewModalProps {
    isOpen: boolean
    onClose: () => void
    fileUrl: string | null
    fileName: string
    isLoadingUrl: boolean
    pageNumber?: number
}

export function PdfPreviewModal({
    isOpen,
    onClose,
    fileUrl,
    fileName,
    isLoadingUrl,
    pageNumber,
}: PdfPreviewModalProps) {
    const modalRef = useRef<HTMLDivElement>(null)

    // Escape key handler
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose()
            }
        }
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [isOpen, onClose])

    if (!isOpen) return null

    const handleOverlayClick = (e: React.MouseEvent) => {
        if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
            onClose()
        }
    }

    return (
        <div
            onClick={handleOverlayClick}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 md:p-6"
        >
            <div
                ref={modalRef}
                className="w-full max-w-5xl h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
            >
                {/* Header */}
                <header className="flex items-center justify-between px-4 py-3 border-b border-slate-150 bg-slate-50">
                    <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className="h-5 w-5 shrink-0 text-rose-500" />
                        <h3 className="text-sm font-bold text-slate-800 truncate" title={fileName}>
                            {fileName}
                        </h3>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                        {fileUrl && (
                            <>
                                <a
                                    href={fileUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                                    title="Mở trong tab mới"
                                >
                                    <ExternalLink className="h-4 w-4" />
                                </a>
                                <a
                                    href={fileUrl}
                                    download={fileName}
                                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                                    title="Tải về"
                                >
                                    <Download className="h-4 w-4" />
                                </a>
                            </>
                        )}
                        <button
                            onClick={onClose}
                            className="p-2 text-slate-500 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition"
                            title="Đóng"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 bg-slate-100 flex items-center justify-center min-h-0 relative">
                    {isLoadingUrl ? (
                        <div className="flex flex-col items-center justify-center gap-3">
                            <Spinner size="lg" />
                            <p className="text-xs text-slate-500 font-medium">Đang chuẩn bị xem trước tài liệu...</p>
                        </div>
                    ) : fileUrl ? (
                        <iframe
                            src={pageNumber !== undefined ? `${fileUrl}#page=${pageNumber}` : fileUrl}
                            className="w-full h-full border-none bg-white"
                            title={fileName}
                        />
                    ) : (
                        <div className="text-center p-6 space-y-2">
                            <p className="text-sm text-slate-500 italic">Không thể tải hoặc hiển thị tập tin xem trước.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
