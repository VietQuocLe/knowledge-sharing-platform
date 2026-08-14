import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'

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

  if (majorId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Mã ngành không hợp lệ." />
      </div>
    )
  }

  if (isLoadingMajor || isLoadingSubjects) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </div>
    )
  }

  if (errorMajor) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Không thể tải thông tin ngành" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        {major ? (
          <Link
            to={`/departments/${major.department_id}`}
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            ← Quay lại khoa
          </Link>
        ) : (
          <Link to="/departments" className="text-sm text-slate-600 hover:text-slate-900">
            ← Quay lại
          </Link>
        )}
      </div>

      {major && (
        <>
          <h1 className="text-3xl font-semibold text-slate-900">{major.name}</h1>
          <p className="mt-2 text-slate-600">Mã ngành: {major.code}</p>

          <h2 className="mt-8 text-xl font-semibold text-slate-900">Danh sách môn học</h2>

          {errorSubjects ? (
            <div className="mt-6">
              <ErrorMessage message="Không thể tải danh sách môn học" />
            </div>
          ) : subjects && subjects.length > 0 ? (
            <div className="mt-6 space-y-3">
              {subjects.map((subject) => (
                <Link
                  key={subject.id}
                  to={`/subjects/${subject.id}`}
                  className="block rounded-lg border border-slate-200 p-4 transition hover:border-slate-900 hover:bg-slate-50"
                >
                  <div className="font-medium text-slate-900">{subject.name}</div>
                  <div className="text-sm text-slate-600">{subject.code}</div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="mt-6 text-slate-600">Không có môn học nào trong ngành này</p>
          )}
        </>
      )}
    </div>
  )
}
