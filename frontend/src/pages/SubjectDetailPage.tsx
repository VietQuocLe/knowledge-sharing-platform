import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PaginationBar } from '../components/ui/PaginationBar'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { PublicResourceCard } from '../features/resources/components/PublicResourceCard'
import { resourcesApi } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'

export function SubjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const subjectId = parseRouteId(id)
  const [page, setPage] = useState(1)
  const pageSize = 20

  const {
    data: subject,
    isLoading: isLoadingSubject,
    error: errorSubject,
  } = useQuery({
    queryKey: taxonomyKeys.subjectDetail(subjectId!),
    queryFn: () => taxonomyApi.getSubjectById(subjectId!),
    enabled: subjectId !== null,
  })

  const {
    data: resourcesPage,
    isLoading: isLoadingResources,
    error: errorResources,
  } = useQuery({
    queryKey: resourcesKeys.listPaginated({ subjectId: subjectId ?? undefined, page }),
    queryFn: () =>
      resourcesApi.getResourceList({
        subjectId: subjectId!,
        page,
        size: pageSize,
      }),
    enabled: subjectId !== null,
  })

  const resources = resourcesPage?.items ?? []
  const total = resourcesPage?.total ?? 0

  if (subjectId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Mã môn học không hợp lệ." />
      </div>
    )
  }

  if (isLoadingSubject) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </div>
    )
  }

  if (errorSubject) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Không thể tải thông tin môn học" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        <Link to="/" className="text-sm text-slate-600 hover:text-slate-900">
          ← Quay lại
        </Link>
      </div>

      {subject && (
        <>
          <h1 className="text-3xl font-semibold text-slate-900">{subject.name}</h1>
          <p className="mt-2 text-slate-600">Mã môn: {subject.code}</p>

          <div className="mt-2 flex flex-wrap gap-2">
            {subject.majors.map((major) => (
              <span key={major.id} className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
                {major.name}
              </span>
            ))}
          </div>

          <h2 className="mt-8 text-xl font-semibold text-slate-900">Tài nguyên liên quan</h2>

          {isLoadingResources ? (
            <div className="mt-6 flex justify-center py-8">
              <Spinner />
            </div>
          ) : errorResources ? (
            <div className="mt-6">
              <ErrorMessage message="Không thể tải danh sách tài nguyên" />
            </div>
          ) : resources.length > 0 ? (
            <div className="mt-6 space-y-3">
              {resources.map((resource) => (
                <PublicResourceCard key={resource.id} resource={resource} />
              ))}
              <PaginationBar page={page} total={total} pageSize={pageSize} onPageChange={setPage} />
            </div>
          ) : (
            <p className="mt-6 text-slate-600">Không có tài nguyên nào cho môn học này</p>
          )}
        </>
      )}
    </div>
  )
}
