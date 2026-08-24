import { useState } from 'react'
import { X, Search, FileText, Loader2, UploadCloud, Paperclip } from 'lucide-react'
import { Modal } from '../../../components/ui/Modal'
import { useDocuments } from '../../documents/hooks/useDocuments'
import { useSaveDocumentToNotebook } from '../hooks/useSaveDocumentToNotebook'
import { useUploadNotebookAsset } from '../hooks/useUploadNotebookAsset'
import type { NotebookDetail } from '../api'
import { toast } from 'react-hot-toast'

interface AddDocumentModalProps {
    isOpen: boolean
    onClose: () => void
    notebook: NotebookDetail
}

export function AddDocumentModal({ isOpen, onClose, notebook }: AddDocumentModalProps) {
    const [activeTab, setActiveTab] = useState<'library' | 'upload'>('library')
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedFiles, setSelectedFiles] = useState<File[]>([])
    const [isUploading, setIsUploading] = useState(false)

    // TanStack queries/mutations
    const { data: documentsData, isLoading: isDocsLoading } = useDocuments({
        subjectId: notebook.subject_id || undefined,
        size: 50
    })

    const { mutate: saveDocument, isPending: isSavingDoc } = useSaveDocumentToNotebook(notebook.id)
    const { mutateAsync: uploadAsset } = useUploadNotebookAsset(notebook.id)

    const isQuotaFull = notebook.sources_count >= notebook.max_sources

    const handleLibrarySave = (documentId: number, docTitle: string) => {
        if (isQuotaFull) {
            toast.error('Không thể lưu tài liệu. Sổ ghi chú đã đạt giới hạn tối đa!')
            return
        }

        saveDocument(documentId, {
            onSuccess: () => {
                toast.success(`Đã lưu tài liệu "${docTitle}" thành công!`)
            },
            onError: (err: any) => {
                const errMsg = err.response?.data?.detail || 'Không thể lưu tài liệu. Vui lòng thử lại!'
                toast.error(errMsg)
            }
        })
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const filesArray = Array.from(e.target.files)
            const validFiles: File[] = []

            for (const file of filesArray) {
                // Validate file extension
                const nameLower = file.name.toLowerCase()
                const isAllowedExt = nameLower.endsWith('.pdf') || nameLower.endsWith('.docx')

                if (!isAllowedExt) {
                    toast.error(`Tệp "${file.name}" không đúng định dạng PDF hoặc DOCX.`)
                    continue
                }

                // Validate file size (30MB limit)
                const sizeMb = file.size / (1024 * 1024)
                if (sizeMb > 30) {
                    toast.error(`Tệp "${file.name}" vượt quá giới hạn tối đa 30MB.`)
                    continue
                }

                // Check for duplicates
                if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                    continue
                }

                validFiles.push(file)
            }

            if (validFiles.length > 0) {
                setSelectedFiles(prev => [...prev, ...validFiles])
            }
        }
    }

    const handleFileUpload = async () => {
        if (selectedFiles.length === 0) return
        if (isQuotaFull) {
            toast.error('Không thể tải tệp lên. Sổ ghi chú đã đạt giới hạn tối đa!')
            return
        }

        setIsUploading(true)
        let successCount = 0

        const uploadPromises = selectedFiles.map(async (file) => {
            try {
                await uploadAsset(file)
                successCount++
            } catch (err: any) {
                const errMsg = err.response?.data?.detail || `Không thể tải tệp "${file.name}" lên.`
                toast.error(errMsg)
            }
        })

        await Promise.all(uploadPromises)
        setIsUploading(false)

        if (successCount > 0) {
            toast.success(`Đã tải lên thành công ${successCount} tệp!`)
            setSelectedFiles([])
            onClose()
        }
    }

    // Filter documents based on search term (client side search)
    const documents = documentsData?.items || []
    const filteredDocuments = documents.filter(doc =>
        doc.title.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const isActionPending = isSavingDoc || isUploading

    return (
        <Modal isOpen={isOpen}>
            <div className="flex flex-col gap-4 font-sans max-h-[80vh] w-full">
                {/* Modal Header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Thêm tài liệu</h3>
                        <p className="text-3xs text-slate-450 mt-0.5">
                            {notebook.subject_name ? `Ưu tiên lọc theo môn: ${notebook.subject_name}` : 'Tìm kiếm hoặc tải lên tài liệu học tập'}
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="p-1 rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-655 transition cursor-pointer"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                {/* Quota limit warning */}
                {isQuotaFull && (
                    <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-800 text-xs font-semibold leading-relaxed flex items-start gap-2">
                        <span>⚠️ Sổ ghi chú đã đạt tối đa {notebook.max_sources} tài liệu. Hãy xóa bớt nguồn trước khi thêm mới.</span>
                    </div>
                )}

                {/* Tabs selection */}
                <div className="flex border-b border-slate-100">
                    <button
                        type="button"
                        onClick={() => setActiveTab('library')}
                        className={`flex-1 pb-2.5 text-xs font-bold text-center border-b-2 transition cursor-pointer ${activeTab === 'library'
                            ? 'border-indigo-600 text-indigo-600'
                            : 'border-transparent text-slate-450 hover:text-slate-655'
                            }`}
                    >
                        Thêm từ thư viện
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('upload')}
                        className={`flex-1 pb-2.5 text-xs font-bold text-center border-b-2 transition cursor-pointer ${activeTab === 'upload'
                            ? 'border-indigo-600 text-indigo-600'
                            : 'border-transparent text-slate-450 hover:text-slate-655'
                            }`}
                    >
                        Tải tệp lên (PDF/DOCX)
                    </button>
                </div>

                {/* Content views */}
                {activeTab === 'library' ? (
                    <>
                        {/* Search Bar */}
                        <div className="relative">
                            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Tìm tài liệu từ danh sách..."
                                className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                            />
                        </div>

                        {/* List Container */}
                        <div className="flex-1 overflow-y-auto max-h-[40vh] pr-1 space-y-2">
                            {isDocsLoading ? (
                                <div className="flex justify-center py-10">
                                    <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
                                </div>
                            ) : filteredDocuments.length > 0 ? (
                                filteredDocuments.map((doc) => {
                                    const isSaved = notebook.sources.some(
                                        (s) => s.type === 'saved' && s.id === doc.id
                                    )

                                    return (
                                        <div
                                            key={doc.id}
                                            className="p-3 rounded-xl border border-slate-150 hover:border-slate-350 transition flex items-center justify-between gap-3 text-left"
                                        >
                                            <div className="min-w-0 flex-1 flex items-start gap-2.5">
                                                <FileText className="h-4.5 w-4.5 text-indigo-500 shrink-0 mt-0.5" />
                                                <div className="min-w-0">
                                                    <h4 className="text-xs font-bold text-slate-800 truncate" title={doc.title}>
                                                        {doc.title}
                                                    </h4>
                                                    <span className="text-[10px] text-slate-450 mt-1 block">
                                                        ID: {doc.id} {doc.description && `• ${doc.description.slice(0, 45)}...`}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Action button */}
                                            <button
                                                type="button"
                                                disabled={isSaved || isActionPending || isQuotaFull}
                                                onClick={() => handleLibrarySave(doc.id, doc.title)}
                                                className={`px-3 py-1.5 rounded-lg text-3xs font-extrabold transition cursor-pointer select-none shrink-0 ${isSaved
                                                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                                    : isQuotaFull
                                                        ? 'bg-rose-50/55 text-rose-400 cursor-not-allowed border border-rose-100/30'
                                                        : 'bg-indigo-600 hover:bg-indigo-700 text-white active:bg-indigo-808 shadow-sm'
                                                    }`}
                                            >
                                                {isSaved ? 'Đã lưu' : 'Lưu'}
                                            </button>
                                        </div>
                                    )
                                })
                            ) : (
                                <div className="text-center py-10 text-slate-400 text-xs italic">
                                    Chưa tìm thấy hoặc không tìm được tài liệu công cộng phù hợp.
                                </div>
                            )}
                        </div>
                        {/* Tab Footer button */}
                        <div className="flex justify-end pt-3 border-t border-slate-100 mt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 text-xs font-bold text-slate-655 hover:bg-slate-100 rounded-xl transition cursor-pointer"
                            >
                                Đóng
                            </button>
                        </div>
                    </>
                ) : (
                    // Upload Tab Content
                    <div className="space-y-4">
                        <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-200 hover:border-indigo-500 rounded-2xl p-6 bg-slate-50/30 group transition cursor-pointer relative">
                            <input
                                type="file"
                                multiple
                                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                onChange={handleFileChange}
                                disabled={isUploading || isQuotaFull}
                                className="absolute inset-0 opacity-0 cursor-pointer disabled:cursor-not-allowed"
                            />

                            <UploadCloud className="h-10 w-10 text-slate-400 group-hover:text-indigo-500 shrink-0 mb-2 transition" />
                            <p className="text-xs font-bold text-slate-800 text-center">
                                Nhấp hoặc thả tập tin vào đây để tải lên.
                            </p>
                            <p className="text-[10px] text-slate-450 mt-1.5 text-center">
                                PDF hoặc DOCX (Hỗ trợ chọn nhiều tệp, Tối đa 30MB mỗi tệp)
                            </p>
                        </div>

                        {selectedFiles.length > 0 && (
                            <div className="space-y-2 max-h-[20vh] overflow-y-auto pr-1">
                                {selectedFiles.map((file, idx) => (
                                    <div key={`${file.name}-${idx}`} className="flex items-center justify-between p-3 rounded-xl border border-slate-150 bg-slate-50/50">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <Paperclip className="h-4 w-4 text-indigo-500 shrink-0" />
                                            <div className="min-w-0">
                                                <p className="text-xs font-bold text-slate-800 truncate" title={file.name}>
                                                    {file.name}
                                                </p>
                                                <p className="text-3xs text-slate-450 mt-0.5">
                                                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            disabled={isUploading}
                                            onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== idx))}
                                            className="p-1 rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-655 transition cursor-pointer"
                                        >
                                            <X className="h-3.5 w-3.5" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-100 mt-2">
                            <button
                                type="button"
                                disabled={isUploading}
                                onClick={onClose}
                                className="px-4 py-2 text-xs font-bold text-slate-655 hover:bg-slate-100 rounded-xl transition cursor-pointer"
                            >
                                Đóng
                            </button>
                            <button
                                type="button"
                                disabled={selectedFiles.length === 0 || isUploading || isQuotaFull}
                                onClick={handleFileUpload}
                                className={`px-4 py-2 text-xs font-bold text-white rounded-xl shadow-sm transition flex items-center gap-1.5 ${selectedFiles.length === 0 || isUploading || isQuotaFull
                                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                                    : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-805 active:bg-indigo-800 cursor-pointer'
                                    }`}
                            >
                                {isUploading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                                {isUploading ? 'Đang tải lên...' : 'Tải lên'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </Modal>
    )
}
