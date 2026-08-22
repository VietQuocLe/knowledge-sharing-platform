import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { Breadcrumb } from '../components/ui/Breadcrumb'
import { Card } from '../components/ui/Card'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { SUBJECT_CATEGORY_LABELS } from '../features/taxonomy/constants'
import { parseRouteId } from '../utils/parseRouteId'
import { BookOpen, ChevronRight, ChevronDown } from 'lucide-react'
import type { SubjectCategory } from '../features/taxonomy/api'

export function MajorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const majorId = parseRouteId(id)

  const {
    data: major,
    isLoading: isLoadingMajor,
    error: errorMajor,
  } = useQuery({
    queryKey: taxonomyKeys.majorDetail(majorId!),
    queryFn: () => taxonomyApi.getMajorById(majorId!),
    enabled: majorId !== null,
  })

  const {
    data: subjects,
    isLoading: isLoadingSubjects,
    error: errorSubjects,
  } = useQuery({
    queryKey: taxonomyKeys.subjectsList(majorId ?? undefined),
    queryFn: () => taxonomyApi.getSubjectsByMajor(majorId!),
    enabled: majorId !== null,
  })

  // State to track manual open/close toggles of groups
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})

  // Dynamic Grouping & Sorting
  const groupedSubjects = useMemo(() => {
    const groups: Record<SubjectCategory, typeof subjects> = {
      GENERAL: [],
      FOUNDATION: [],
      SPECIALIZED: [],
      ELECTIVE_CAPSTONE: [],
    }

    if (subjects) {
      subjects.forEach((subject) => {
        const cat = subject.category || 'GENERAL'
        if (groups[cat]) {
          groups[cat].push(subject)
        } else {
          groups.GENERAL.push(subject)
        }
      })
    }

    // Sort subjects in each group by code alphabetically
    Object.keys(groups).forEach((key) => {
      groups[key as SubjectCategory]?.sort((a, b) => a.code.localeCompare(b.code))
    })

    return groups
  }, [subjects])

  const isGroupOpen = (category: SubjectCategory) => {
    if (openGroups[category] !== undefined) {
      return openGroups[category]
    }
    // Default open if group has subjects
    return (groupedSubjects[category]?.length || 0) > 0
  }

  const toggleGroup = (category: SubjectCategory) => {
    setOpenGroups((prev) => ({
      ...prev,
      [category]: !isGroupOpen(category),
    }))
  }

  if (majorId === null) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Mã ngành không hợp lệ." />
      </div>
    )
  }

  if (isLoadingMajor || isLoadingSubjects) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (errorMajor) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Không thể tải thông tin ngành đào tạo." />
      </div>
    )
  }

  const breadcrumbItems = major
    ? [
      {
        label: major.department?.name || 'Khoa',
        href: `/departments/${major.department_id}`,
      },
      { label: major.name },
    ]
    : []

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
      {/* Breadcrumb Navigation */}
      {major && <Breadcrumb items={breadcrumbItems} />}

      {major && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Cột trái: Thông tin tổng quan (lg:col-span-4) */}
          <div className="lg:col-span-4">
            <Card className="p-6 space-y-4">
              {/* Ảnh bìa / icon minh họa */}
              <div className="h-32 w-full bg-slate-50 border border-slate-200/60 rounded-xl flex items-center justify-center text-slate-400">
                <BookOpen className="h-12 w-12" />
              </div>
              <div className="space-y-2">
                <span className="inline-flex items-center rounded-md bg-indigo-50 border border-indigo-200/50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                  Mã ngành: {major.code}
                </span>
                <h1 className="text-xl font-bold tracking-tight text-slate-900 leading-snug">
                  {major.name}
                </h1>
              </div>
              <p className="text-sm text-slate-550 leading-relaxed">
                Chuyên ngành đào tạo chính quy thuộc khoa {major.department?.name || 'trực thuộc'}. Dưới đây là các môn học có tài liệu chia sẻ trong lộ trình học tập.
              </p>
            </Card>
          </div>

          {/* Cột phải: Danh sách môn học dạng Accordion (lg:col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="border-b border-slate-150 pb-3">
              <h2 className="text-lg font-bold text-slate-900 font-sans">Tài liệu các môn</h2>
              <p className="text-sm text-slate-500 mt-1">
                Mỗi kì thì bạn sẽ học tầm 4-5 môn, chi tiết bạn xem ở chương trình đào tạo.
              </p>
            </div>

            {errorSubjects ? (
              <ErrorMessage message="Không thể tải danh sách môn học của ngành đào tạo này." />
            ) : subjects && subjects.length > 0 ? (
              <div className="space-y-4">
                {(Object.keys(SUBJECT_CATEGORY_LABELS) as SubjectCategory[]).map((categoryKey) => {
                  const groupSubjects = groupedSubjects[categoryKey] || []
                  const isOpen = isGroupOpen(categoryKey)
                  const label = SUBJECT_CATEGORY_LABELS[categoryKey]

                  return (
                    <div key={categoryKey} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-3xs">
                      {/* Accordion Header */}
                      <button
                        type="button"
                        onClick={() => toggleGroup(categoryKey)}
                        className="flex items-center justify-between w-full p-4 bg-slate-50 hover:bg-slate-100/70 border-b border-slate-200/40 transition cursor-pointer text-left focus:outline-hidden"
                      >
                        <div className="flex items-center gap-2">
                          {isOpen ? (
                            <ChevronDown className="h-4.5 w-4.5 text-slate-500 transition-transform duration-200" />
                          ) : (
                            <ChevronRight className="h-4.5 w-4.5 text-slate-500 transition-transform duration-200" />
                          )}
                          <span className="font-bold text-slate-800 text-sm sm:text-base">{label}</span>
                        </div>
                        <span className="text-xs font-semibold text-slate-500 bg-white border border-slate-200 px-2 py-0.5 rounded-full select-none">
                          {groupSubjects.length} môn
                        </span>
                      </button>

                      {/* Accordion Content */}
                      {isOpen && (
                        <div className="p-3 bg-white divide-y divide-slate-100">
                          {groupSubjects.length > 0 ? (
                            groupSubjects.map((sub) => (
                              <Link
                                key={sub.id}
                                to={`/subjects/${sub.id}`}
                                className="group flex items-center justify-between p-3.5 hover:bg-slate-50/70 rounded-xl transition"
                              >
                                <div className="flex items-center gap-3 min-w-0">
                                  <BookOpen className="h-4.5 w-4.5 text-slate-400 shrink-0" />
                                  <span className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-2xs font-bold text-slate-650 shrink-0">
                                    {sub.code}
                                  </span>
                                  <span className="text-sm font-bold text-slate-800 truncate group-hover:text-indigo-650 transition">
                                    {sub.name}
                                  </span>
                                </div>
                                <ChevronRight className="h-4 w-4 text-slate-350 transition-transform group-hover:translate-x-0.5" />
                              </Link>
                            ))
                          ) : (
                            <div className="text-center py-6 text-slate-450 italic text-sm">
                              Hiện chưa có môn học nào thuộc nhóm kiến thức này.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                Hiện chưa có môn học nào được đăng ký cho chuyên ngành này.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

