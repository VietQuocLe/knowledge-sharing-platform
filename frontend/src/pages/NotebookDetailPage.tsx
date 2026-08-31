import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { BookOpen, Clock, FileText, MessageSquare, File, Plus, MoreVertical, Trash2, Download, ExternalLink, Eye, GraduationCap } from 'lucide-react'
import { useNotebookDetail, AddDocumentModal, useUnsaveDocument, useDeleteNotebookAsset, notebooksApi, NotebookChatPanel, NotebookCreationsHub, QuizRunner, GenerateArtifactModal } from '../features/notebooks'
import { documentsApi, PdfPreviewModal } from '../features/documents'
import { useClickOutside } from '../hooks/useClickOutside'
import { Spinner } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Badge } from '../components/ui/Badge'
import { formatFileSize, formatRelativeTime } from '../utils/formatters'
import { toast } from 'react-hot-toast'

interface SourceCardProps {
    source: any
    notebookId: number
    onPreview: (previewState: any) => void
    onActionSuccess: () => void
}

function SourceCard({ source, notebookId, onPreview, onActionSuccess }: SourceCardProps) {
    const navigate = useNavigate()
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const [isConfirmOpen, setIsConfirmOpen] = useState(false)

    const menuRef = useClickOutside<HTMLDivElement>(() => setIsMenuOpen(false))

    const { mutate: unsaveDoc, isPending: isUnsaving } = useUnsaveDocument(notebookId)
    const { mutate: deleteAsset, isPending: isDeleting } = useDeleteNotebookAsset(notebookId)

    const handlePreview = async () => {
        setIsMenuOpen(false)
        onPreview({
            isOpen: true,
            fileUrl: null,
            fileName: source.title,
            isLoadingUrl: true
        })
        try {
            let url = ''
            if (source.type === 'local') {
                const res = await notebooksApi.downloadAsset(notebookId, source.id)
                url = res.download_url
            } else {
                const docDetail = await documentsApi.getDocumentDetail(source.id)
                const asset = docDetail.assets?.[0]
                if (!asset) {
                    throw new Error('Tài liệu thư viện không chứa tệp tin.')
                }
                const res = await documentsApi.getAssetDownloadUrl(docDetail.id, asset.id)
                url = res.download_url
            }
            onPreview({
                isOpen: true,
                fileUrl: url,
                fileName: source.title,
                isLoadingUrl: false
            })
        } catch (err: any) {
            const msg = err.response?.data?.detail || err.message || 'Không thể tải đường dẫn xem trước.'
            toast.error(msg)
            onPreview({
                isOpen: false,
                fileUrl: null,
                fileName: '',
                isLoadingUrl: false
            })
        }
    }

    const handleDownload = async () => {
        setIsMenuOpen(false)
        try {
            const res = await notebooksApi.downloadAsset(notebookId, source.id)
            const link = document.createElement('a')
            link.href = res.download_url
            link.download = res.file_name || source.title
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            toast.success('Đang bắt đầu tải tệp...')
        } catch (err) {
            toast.error('Không thể tải tệp tin. Vui lòng thử lại!')
        }
    }

    const handleConfirmAction = () => {
        setIsConfirmOpen(false)
        if (source.type === 'local') {
            deleteAsset(source.id, {
                onSuccess: () => {
                    toast.success(`Đã xóa tệp "${source.title}" thành công.`)
                    onActionSuccess()
                },
                onError: (err: any) => {
                    const msg = err.response?.data?.detail || 'Không thể xóa tệp.'
                    toast.error(msg)
                }
            })
        } else {
            unsaveDoc(source.id, {
                onSuccess: () => {
                    toast.success(`Đã bỏ lưu tài liệu "${source.title}".`)
                    onActionSuccess()
                },
                onError: (err: any) => {
                    const msg = err.response?.data?.detail || 'Không thể bỏ lưu tài liệu.'
                    toast.error(msg)
                }
            })
        }
    }

    const getFileIcon = (fileName: string, fileType: string) => {
        const nameLower = fileName.toLowerCase()
        if (nameLower.endsWith('.pdf') || fileType.toLowerCase().includes('pdf')) {
            return <FileText className="h-5 w-5 text-rose-500" />
        }
        if (
            nameLower.endsWith('.docx') ||
            fileType.toLowerCase().includes('wordprocessingml') ||
            fileType.toLowerCase().includes('docx')
        ) {
            return <FileText className="h-5 w-5 text-blue-500" />
        }
        return <File className="h-5 w-5 text-slate-500" />
    }

    const docxTypes = ['docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const isDocx = docxTypes.some(t =>
        source.title.toLowerCase().endsWith('.docx') ||
        (source.file_type || '').toLowerCase().includes(t)
    );
    const isPdf = source.title.toLowerCase().endsWith('.pdf') || (source.file_type || '').toLowerCase().includes('pdf');

    const isConverting = source.type === 'local' && isDocx && source.conversion_status === 'PENDING';
    const isFailed = source.type === 'local' && isDocx && source.conversion_status === 'FAILED';
    const isCompleted = source.type === 'local' && isDocx && source.conversion_status === 'COMPLETED';

    const canPreview = source.type === 'saved'
        ? isPdf
        : (isPdf || isCompleted);

    const handleTitleClick = () => {
        if (isConverting) {
            toast.loading('Tài liệu đang được chuyển đổi sang PDF. Vui lòng đợi trong giây lát!', { id: 'converting', duration: 2000 })
            return
        }
        if (isFailed) {
            toast.error('Chuyển đổi sang PDF thất bại. Vui lòng tải tệp gốc về để xem.')
            return
        }
        if (canPreview) {
            handlePreview()
        } else {
            toast.error('Định dạng Word (.docx) không hỗ trợ xem trực tuyến. Vui lòng tải về máy để xem.')
        }
    }

    const isPending = isUnsaving || isDeleting

    return (
        <div className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-slate-350 hover:shadow-2xs transition duration-150 flex flex-col justify-between gap-3 relative group">
            {/* Card Content Row */}
            <div className="flex items-start gap-4 min-w-0 pr-6">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 border border-slate-150 shadow-3xs group-hover:scale-105 transition">
                    {getFileIcon(source.title, source.file_type)}
                </div>
                <div className="min-w-0 flex-1">
                    <h4
                        onClick={handleTitleClick}
                        className={`text-xs font-bold text-slate-800 break-words leading-snug line-clamp-2 hover:text-sky-600 transition ${canPreview
                            ? 'hover:underline cursor-pointer'
                            : isConverting
                                ? 'cursor-wait opacity-80'
                                : 'cursor-default'
                            }`}
                        title={source.title}
                    >
                        {source.title}
                    </h4>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                        {source.type === 'local' ? (
                            <Badge variant="warning" className="text-[9px] px-1.5 py-0 border-amber-200 bg-amber-50 text-amber-700 font-bold">
                                Tải lên
                            </Badge>
                        ) : (
                            <Badge variant="primary" className="text-[9px] px-1.5 py-0 font-bold">
                                Thư viện
                            </Badge>
                        )}
                        {isConverting && (
                            <Badge variant="primary" className="text-[9px] px-1.5 py-0 border-sky-200 bg-sky-50 text-sky-700 font-bold animate-pulse">
                                Đang xử lý...
                            </Badge>
                        )}
                        {isFailed && (
                            <Badge variant="danger" className="text-[9px] px-1.5 py-0 border-rose-200 bg-rose-50 text-rose-700 font-bold">
                                Lỗi xử lý PDF
                            </Badge>
                        )}
                        <span className="text-[10px] text-slate-455 font-medium">
                            {source.type === 'local' ? formatFileSize(source.size) : source.file_type}
                        </span>
                    </div>
                </div>
            </div>

            {/* Bottom timestamp */}
            <div className="flex items-center gap-1.5 text-[10px] text-slate-450 pt-2 border-t border-slate-50">
                <Clock className="h-3 w-3 shrink-0" />
                <span>Thêm vào {formatRelativeTime(source.created_at)}</span>
            </div>

            {/* Kebab action menu anchor */}
            <div className="absolute top-3.5 right-3.5" ref={menuRef}>
                <button
                    type="button"
                    disabled={isPending}
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-655 transition cursor-pointer"
                    title="Thao tác"
                >
                    <MoreVertical className="h-4 w-4" />
                </button>

                {isMenuOpen && (
                    <div className="absolute right-0 mt-1 w-40 bg-white border border-slate-150 rounded-xl shadow-lg py-1 z-30 font-sans">
                        {isConverting && (
                            <button
                                type="button"
                                disabled
                                className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-400 bg-slate-50 flex items-center gap-2 cursor-not-allowed opacity-60"
                            >
                                <Eye className="h-3.5 w-3.5 text-slate-400" />
                                Đang xử lý...
                            </button>
                        )}
                        {canPreview && !isConverting && (
                            <button
                                type="button"
                                onClick={handlePreview}
                                className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-sky-50 hover:text-sky-600 flex items-center gap-2 transition cursor-pointer"
                            >
                                <Eye className="h-3.5 w-3.5 text-slate-455" />
                                Xem trước
                            </button>
                        )}

                        {source.type === 'local' ? (
                            <>
                                <button
                                    type="button"
                                    onClick={handleDownload}
                                    className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-sky-50 hover:text-sky-600 flex items-center gap-2 transition cursor-pointer"
                                >
                                    <Download className="h-3.5 w-3.5 text-slate-450" />
                                    Tải về máy
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsMenuOpen(false)
                                        setIsConfirmOpen(true)
                                    }}
                                    className="w-full px-3 py-2 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50 flex items-center gap-2 transition border-t border-slate-100 cursor-pointer"
                                >
                                    <Trash2 className="h-3.5 w-3.5 text-rose-450" />
                                    Xóa tệp
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsMenuOpen(false)
                                        navigate(`/documents/${source.id}`)
                                    }}
                                    className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-sky-50 hover:text-sky-600 flex items-center gap-2 transition cursor-pointer"
                                >
                                    <ExternalLink className="h-3.5 w-3.5 text-slate-455" />
                                    Xem ở thư viện
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsMenuOpen(false)
                                        setIsConfirmOpen(true)
                                    }}
                                    className="w-full px-3 py-2 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50 flex items-center gap-2 transition border-t border-slate-100 cursor-pointer"
                                >
                                    <Trash2 className="h-3.5 w-3.5 text-rose-450" />
                                    Bỏ lưu
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Confirmation Modal */}
            {isConfirmOpen && (
                <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-3xs z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-xl font-sans text-left">
                        <h3 className="text-sm font-bold text-slate-800">
                            {source.type === 'local' ? 'Xóa tệp tin' : 'Bỏ lưu tài liệu'}
                        </h3>
                        <p className="text-xs text-slate-505 text-slate-500 leading-relaxed">
                            {source.type === 'local'
                                ? `Bạn có chắc chắn muốn xóa tệp "${source.title}"? Thao tác này sẽ xóa vĩnh viễn tệp học tập của bạn.`
                                : `Bạn có chắc chắn muốn bỏ lưu tài liệu "${source.title}" khỏi sổ ghi chú này?`}
                        </p>
                        <div className="flex justify-end gap-2 text-xs font-bold pt-1">
                            <button
                                type="button"
                                onClick={() => setIsConfirmOpen(false)}
                                className="px-4 py-2 text-slate-500 hover:bg-slate-100 rounded-xl transition cursor-pointer"
                            >
                                Hủy
                            </button>
                            <button
                                type="button"
                                onClick={handleConfirmAction}
                                className="px-4 py-2 bg-rose-650 bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 rounded-xl shadow-sm transition cursor-pointer"
                            >
                                Đồng ý
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export function NotebookDetailPage() {
    const { notebookId } = useParams<{ notebookId: string }>()
    const parsedId = notebookId ? parseInt(notebookId, 10) : NaN
    const navigate = useNavigate()

    const [isAiPanelOpen, setIsAiPanelOpen] = useState(true)
    const [isAddDocOpen, setIsAddDocOpen] = useState(false)
    const [searchParams, setSearchParams] = useSearchParams()

    const activeArtifactId = (() => {
        const param = searchParams.get('artifact')
        return param ? Number(param) : null
    })()

    const handleSelectArtifact = (id: number | null) => {
        setSearchParams((prev) => {
            const next = new URLSearchParams(prev)
            if (id === null) {
                next.delete('artifact')
            } else {
                next.set('artifact', String(id))
            }
            return next
        })
    }

    const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false)
    const [previewState, setPreviewState] = useState<{
        isOpen: boolean
        fileUrl: string | null
        fileName: string
        isLoadingUrl: boolean
    }>({
        isOpen: false,
        fileUrl: null,
        fileName: '',
        isLoadingUrl: false
    })

    const { data: notebook, isLoading, error } = useNotebookDetail(parsedId)




    useEffect(() => {
        if (error) {
            const err = error as any
            const status = err.response?.status
            const detail = err.response?.data?.detail || 'Không thể tải sổ ghi chú.'

            if (status === 403 || status === 404) {
                toast.error(detail)
                navigate('/me/workspace')
            } else {
                toast.error('Có lỗi xảy ra khi tải dữ liệu sổ ghi chú.')
            }
        }
    }, [error, navigate])

    if (isNaN(parsedId) || parsedId <= 0) {
        return (
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
                <ErrorMessage message="Mã sổ ghi chú không hợp lệ." />
            </div>
        )
    }

    if (isLoading) {
        return (
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
                <div className="flex justify-center py-16">
                    <Spinner size="lg" />
                </div>
            </div>
        )
    }

    if (error || !notebook) {
        return (
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10">
                <ErrorMessage message="Không thể tải hoặc hiển thị sổ ghi chú học tập." />
            </div>
        )
    }

    return (
        <div className="flex-1 flex flex-col min-h-0 h-full w-full overflow-hidden bg-[#FAF9F6] relative font-sans">
            {/* Main view wrapper */}
            <div className="flex flex-1 min-h-0 h-full w-full overflow-hidden">
                {/* Left Pane: Documents Area */}
                <div className="flex-1 flex flex-col min-w-0 h-full p-6 bg-white overflow-y-auto gap-6 border-r border-slate-200/80">
                    {/* Header bar */}
                    {activeArtifactId === null && (
                        <div className="flex flex-col gap-2 pb-4 border-b border-slate-100 flex-shrink-0">
                            <div className="flex flex-wrap items-center gap-3">
                                <h1 className="text-xl font-extrabold text-slate-900 md:text-2xl tracking-tight leading-snug">
                                    {notebook.title}
                                </h1>
                                {notebook.subject_name && (
                                    <Badge variant="primary" className="flex items-center gap-1 font-bold">
                                        <BookOpen className="h-3.5 w-3.5" />
                                        {notebook.subject_name}
                                    </Badge>
                                )}
                            </div>
                        </div>
                    )}

                    {activeArtifactId !== null ? (
                        <QuizRunner
                            notebookId={notebook.id}
                            artifactId={activeArtifactId}
                            onBack={() => handleSelectArtifact(null)}
                        />
                    ) : (
                        <>
                            {/* Quick Actions Block (StudyFetch style) */}
                            <div className="bg-[#F8F8F6] border border-slate-200/80 rounded-2xl p-5 space-y-4 flex-shrink-0">
                                <div>
                                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                                        Bắt đầu học tập
                                    </h3>
                                    <p className="text-[11px] text-slate-500 mt-1">
                                        Tải tài liệu nguồn lên hoặc tạo bài luyện tập, Flashcard ôn tập ngay lập tức.
                                    </p>
                                </div>

                                <div className="flex flex-wrap gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setIsAddDocOpen(true)}
                                        className="px-4 py-2.5 text-xs font-bold text-white bg-black hover:bg-slate-800 active:bg-slate-900 rounded-xl shadow-xs transition flex items-center gap-2 cursor-pointer"
                                    >
                                        <Plus className="h-4 w-4" />
                                        Thêm tài liệu nguồn
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setIsGenerateModalOpen(true)}
                                        className="px-4 py-2.5 text-xs font-bold text-slate-800 border border-slate-200 bg-white hover:bg-slate-50 active:bg-slate-100 rounded-xl shadow-xs transition flex items-center gap-2 cursor-pointer"
                                    >
                                        <GraduationCap className="h-4 w-4 text-[#0D9488]" />
                                        <span>Tạo bài tập / Quiz</span>
                                    </button>
                                </div>
                            </div>

                            {/* Creations Hub */}
                            <div className="pt-2">
                                <NotebookCreationsHub
                                    notebookId={notebook.id}
                                    onSelectArtifact={handleSelectArtifact}
                                    onOpenGenerateModal={() => setIsGenerateModalOpen(true)}
                                />
                            </div>

                            {/* Sources section */}
                            <div className="space-y-4 flex flex-col pt-6 border-t border-slate-100">
                                <div className="flex items-center justify-between flex-shrink-0">
                                    <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                                        Tài liệu nguồn
                                    </h2>

                                    {/* Compact Quota Indicator */}
                                    <div className="flex items-center gap-3">
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FEF9C3] text-amber-800 border border-amber-200 text-xs font-semibold whitespace-nowrap">
                                            <span className="font-bold">{notebook.sources_count}</span>
                                            <span className="text-[10px]"> / {notebook.max_sources} nguồn</span>
                                        </span>
                                    </div>
                                </div>

                                {notebook.sources.length > 0 ? (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {notebook.sources.map((source) => (
                                            <SourceCard
                                                key={`${source.type}-${source.id}`}
                                                source={source}
                                                notebookId={notebook.id}
                                                onPreview={setPreviewState}
                                                onActionSuccess={() => { }}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="py-12 px-4 border-2 border-dashed border-slate-200 rounded-3xl text-center bg-[#F8F8F6]/60">
                                        <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                                        <h3 className="text-sm font-semibold text-slate-800 mb-1">Chưa có nguồn tài liệu nào</h3>
                                        <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                                            Sổ ghi chú này hiện chưa được liên kết nguồn nào. Tính năng lưu tài liệu công cộng và upload tệp tin cá nhân đã sẵn sàng để sử dụng.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>

                {/* Right Pane: AI Assistant Widget */}
                {isAiPanelOpen ? (
                    <NotebookChatPanel notebookId={parsedId} onClose={() => setIsAiPanelOpen(false)} />
                ) : (
                    /* Floating status badge when collapsed (Bottom-Right Studocu-style) */
                    <button
                        onClick={() => setIsAiPanelOpen(true)}
                        className="fixed bottom-6 right-6 z-40 flex items-center justify-center h-14 w-14 rounded-full bg-black text-white shadow-xl hover:bg-slate-800 hover:scale-105 active:scale-95 transition cursor-pointer"
                        title="Mở Trợ lý AI"
                    >
                        <MessageSquare className="h-6 w-6" />
                    </button>
                )}
            </div>

            <AddDocumentModal
                isOpen={isAddDocOpen}
                onClose={() => setIsAddDocOpen(false)}
                notebook={notebook}
            />

            {isGenerateModalOpen && (
                <GenerateArtifactModal
                    isOpen={isGenerateModalOpen}
                    notebookId={notebook.id}
                    sources={notebook.sources}
                    onClose={() => setIsGenerateModalOpen(false)}
                    onSuccess={(newArtifactId) => {
                        handleSelectArtifact(newArtifactId)
                        setIsGenerateModalOpen(false)
                    }}
                />
            )}

            <PdfPreviewModal
                isOpen={previewState.isOpen}
                onClose={() => setPreviewState({ ...previewState, isOpen: false })}
                fileUrl={previewState.fileUrl}
                fileName={previewState.fileName}
                isLoadingUrl={previewState.isLoadingUrl}
            />
        </div>
    )
}
