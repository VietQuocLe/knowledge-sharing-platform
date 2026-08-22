import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, ChevronRight, BookOpen, Layers, Presentation, FileBadge, Video, Music, ExternalLink, Cpu, File, AlertCircle } from 'lucide-react'
import { PaginationBar } from '../components/ui/PaginationBar'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { Breadcrumb } from '../components/ui/Breadcrumb'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { formatResourceType, formatRelativeTime } from '../utils/formatters'
import { documentsApi, documentsKeys } from '../features/documents'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'
import { SUBJECT_CATEGORY_LABELS } from '../features/taxonomy/constants'

const filterOptions = [
  { value: null, label: 'Tất cả' },
  { value: 'LECTURE', label: 'Slide / Bài giảng' },
  { value: 'EXAM', label: 'Đề thi & Đáp án' },
  { value: 'REFERENCE', label: 'Tài liệu tham khảo' },
  { value: 'SYLLABUS', label: 'Đề cương môn học' },
]

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'SLIDE':
    case 'LECTURE':
      return <Presentation className="h-5 w-5 text-indigo-500" />
    case 'EXAM':
      return <FileBadge className="h-5 w-5 text-amber-500" />
    case 'DOCUMENT':
    case 'REFERENCE':
      return <FileText className="h-5 w-5 text-emerald-500" />
    case 'SYLLABUS':
      return <FileText className="h-5 w-5 text-teal-500" />
    case 'VIDEO':
      return <Video className="h-5 w-5 text-rose-500" />
    case 'AUDIO':
      return <Music className="h-5 w-5 text-violet-500" />
    case 'LINK':
      return <ExternalLink className="h-5 w-5 text-sky-500" />
    case 'AI_ARTIFACT':
      return <Cpu className="h-5 w-5 text-fuchsia-500" />
    default:
      return <File className="h-5 w-5 text-slate-500" />
  }
}

export function SubjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const subjectId = parseRouteId(id)
  const [page, setPage] = useState(1)
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const pageSize = 20

  // 1. Fetch Subject Detail
  const {
    data: subject,
    isLoading: isLoadingSubject,
    error: errorSubject,
  } = useQuery({
    queryKey: taxonomyKeys.subjectDetail(subjectId!),
    queryFn: () => taxonomyApi.getSubjectById(subjectId!),
    enabled: subjectId !== null,
  })

  // 2. Fetch Department Detail (using primary major's department_id from subject)
  const primaryMajor = subject?.majors?.[0]
  const deptId = primaryMajor?.department_id

  const { data: department, isLoading: isLoadingDept } = useQuery({
    queryKey: taxonomyKeys.departmentDetail(deptId!),
    queryFn: () => taxonomyApi.getDepartmentById(deptId!),
    enabled: !!deptId,
  })

  // 3. Fetch Documents (filtered by Subject and Resource Type)
  const {
    data: documentsPage,
    isLoading: isLoadingDocuments,
    error: errorDocuments,
  } = useQuery({
    queryKey: documentsKeys.listPaginated({
      subjectId: subjectId ?? undefined,
      page,
      type: selectedType ?? undefined,
    }),
    queryFn: () =>
      documentsApi.getDocumentList({
        subjectId: subjectId!,
        resourceType: selectedType ?? undefined,
        page,
        size: pageSize,
      }),
    enabled: subjectId !== null,
  })

  const documents = documentsPage?.items ?? []
  const total = documentsPage?.total ?? 0

  if (subjectId === null) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Mã môn học không hợp lệ." />
      </div>
    )
  }

  if (isLoadingSubject || isLoadingDept) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (errorSubject) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Không thể tải thông tin môn học." />
      </div>
    )
  }

  // Construct Breadcrumb segments: Trang chủ > [Department] > [Major] > [Subject]
  const breadcrumbItems = []
  if (department && primaryMajor && subject) {
    breadcrumbItems.push(
      { label: department.name, href: `/departments/${department.id}` },
      { label: primaryMajor.name, href: primaryMajor.id ? `/majors/${primaryMajor.id}` : '#' },
      { label: subject.name },
    )
  }

  // On pill click: Reset page, set new resource type filter
  const handleTypeSelect = (type: string | null) => {
    setSelectedType(type)
    setPage(1)
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
      {/* Breadcrumb Navigation */}
      {breadcrumbItems.length > 0 && <Breadcrumb items={breadcrumbItems} />}

      {subject && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Cột trái: Thông tin tổng quan (lg:col-span-4) */}
          <div className="lg:col-span-4">
            <Card className="p-6 space-y-4">
              {/* Ảnh bìa / icon minh họa */}
              <div className="h-32 w-full bg-slate-50 border border-slate-200/60 rounded-xl flex items-center justify-center text-slate-400">
                <BookOpen className="h-12 w-12" />
              </div>
              <div className="space-y-2">
                <Badge variant="primary">
                  Mã môn: {subject.code}
                </Badge>
                <h1 className="text-xl font-bold tracking-tight text-slate-900 leading-snug">
                  {subject.name}
                </h1>
              </div>

              {subject.category && (
                <div className="pt-3 border-t border-slate-100 space-y-1">
                  <span className="text-xs font-bold text-slate-450 uppercase tracking-wider block">Khối kiến thức:</span>
                  <span className="text-sm font-semibold text-slate-700">
                    {SUBJECT_CATEGORY_LABELS[subject.category] || subject.category}
                  </span>
                </div>
              )}

              {subject.majors && subject.majors.length > 0 && (
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <span className="text-xs font-bold text-slate-450 uppercase tracking-wider block font-sans">Ngành trực thuộc:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {subject.majors.map((m) => (
                      <Link
                        key={m.id}
                        to={m.id ? `/majors/${m.id}` : '#'}
                        className="inline-flex items-center gap-1 rounded-md bg-slate-50 border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100 hover:text-slate-800 transition"
                      >
                        <Layers className="h-3 w-3 text-slate-400" />
                        {m.name}
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-slate-100 space-y-1">
                <span className="text-xs font-bold text-slate-450 uppercase tracking-wider block">Mô tả tóm tắt:</span>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Kho dữ liệu tài liệu ôn tập, đề cương bài giảng và hướng dẫn tự học dành cho môn {subject.name} ({subject.code}). Đóng góp bởi cộng đồng sinh viên.
                </p>
              </div>
            </Card>
          </div>

          {/* Cột phải: Danh sách tài liệu & bộ lọc (lg:col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Filter Tabs / Pills */}
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                Lọc theo loại học liệu
              </h2>
              <div className="flex flex-wrap gap-2 pb-3 border-b border-slate-150">
                {filterOptions.map((opt) => {
                  const isActive = selectedType === opt.value
                  return (
                    <button
                      key={opt.value ?? 'all'}
                      type="button"
                      onClick={() => handleTypeSelect(opt.value)}
                      className={`
                        rounded-full px-4 py-1.5 text-xs font-semibold transition border shadow-sm cursor-pointer
                        ${isActive
                          ? 'bg-slate-900 border-slate-900 text-white hover:bg-slate-800'
                          : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-350'
                        }
                      `.trim()}
                    >
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Documents List */}
            <div>
              <h2 className="text-lg font-bold text-slate-900 mb-4">Danh sách tài liệu môn học</h2>

              {isLoadingDocuments ? (
                <div className="flex justify-center py-16">
                  <Spinner size="lg" />
                </div>
              ) : errorDocuments ? (
                <ErrorMessage message="Không thể tải danh sách tài liệu môn học." />
              ) : documents.length > 0 ? (
                <div className="space-y-6">
                  <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs divide-y divide-slate-100">
                    {documents.map((document) => {
                      const assetCount = document.assets?.length || 0
                      const hasAssets = assetCount > 0

                      const rowContent = (
                        <div className="flex items-center justify-between gap-4 p-4 transition-colors">
                          <div className="flex items-center gap-3.5 min-w-0">
                            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${hasAssets
                                ? 'bg-slate-50 border-slate-100 shadow-3xs'
                                : 'bg-slate-100/50 border-slate-100/80 opacity-60'
                              }`}>
                              {getResourceIcon(document.resource_type)}
                            </div>

                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="text-xs font-bold text-slate-800 leading-snug line-clamp-1">
                                  {document.title}
                                </span>
                                <span className="shrink-0">
                                  <Badge variant="neutral" className="text-[10px] px-1.5 py-0">
                                    {formatResourceType(document.resource_type)}
                                  </Badge>
                                </span>
                                {!hasAssets && (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-650 bg-amber-50 px-1.5 py-0.5 rounded-sm shrink-0">
                                    <AlertCircle className="h-3 w-3" />
                                    Chưa có tệp đính kèm
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400">
                                <span>Đăng {formatRelativeTime(document.created_at)}</span>
                                {hasAssets && (
                                  <>
                                    <span>•</span>
                                    <span className="font-medium text-slate-450 truncate max-w-md">
                                      {assetCount} tệp đính kèm {assetCount === 1 ? `(${document.assets[0].file_name})` : ''}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>

                          {hasAssets && (
                            <div className="text-slate-350 group-hover:text-indigo-650 transition-colors shrink-0">
                              <ChevronRight className="h-4 w-4 transform group-hover:translate-x-0.5 transition-transform" />
                            </div>
                          )}
                        </div>
                      )

                      if (hasAssets) {
                        return (
                          <Link
                            key={document.id}
                            to={`/documents/${document.id}`}
                            className="group block hover:bg-slate-50/70 transition-all"
                          >
                            {rowContent}
                          </Link>
                        )
                      } else {
                        return (
                          <div
                            key={document.id}
                            className="opacity-70 cursor-not-allowed select-none bg-slate-50/30"
                            title="Tài liệu chưa có tệp đính kèm"
                          >
                            {rowContent}
                          </div>
                        )
                      }
                    })}
                  </div>

                  {/* Pagination Controls */}
                  {total > pageSize && (
                    <PaginationBar
                      page={page}
                      total={total}
                      pageSize={pageSize}
                      onPageChange={setPage}
                    />
                  )}
                </div>
              ) : (
                <EmptyState
                  title="Không tìm thấy tài liệu phù hợp"
                  description="Môn học này hiện chưa có tài liệu tương thích với bộ lọc được chọn. Bạn muốn đóng góp tài liệu đầu tiên?"
                  action={
                    import.meta.env.VITE_CONTRIBUTE_FORM_URL
                      ? {
                        label: 'Đóng góp tài liệu',
                        onClick: () => window.open(import.meta.env.VITE_CONTRIBUTE_FORM_URL, '_blank', 'noreferrer'),
                      }
                      : undefined
                  }
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
