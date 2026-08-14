import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'

export function DepartmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const deptId = parseRouteId(id)

  const {
    data: department,
    isLoading: isLoadingDept,
    error: errorDept,
  } = useQuery({
    queryKey: taxonomyKeys.departmentDetail(deptId!),
    queryFn: () => taxonomyApi.getDepartmentById(deptId!),
    enabled: deptId !== null,
  })

  const {
    data: majors,
    isLoading: isLoadingMajors,
    error: errorMajors,
  } = useQuery({
    queryKey: taxonomyKeys.majorsList(deptId ?? undefined),
    queryFn: () => taxonomyApi.getMajorsByDepartment(deptId!),
    enabled: deptId !== null,
  })

  if (deptId === null) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Mã khoa không hợp lệ." />
      </div>
    )
  }

  if (isLoadingDept || isLoadingMajors) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </div>
    )
  }

  if (errorDept) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Không thể tải thông tin khoa" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        <Link to="/departments" className="text-sm text-slate-600 hover:text-slate-900">
          ← Quay lại danh sách khoa
        </Link>
      </div>

      {department && (
        <>
          <h1 className="text-3xl font-semibold text-slate-900">{department.name}</h1>
          <p className="mt-2 text-slate-600">Chọn ngành để xem các môn học</p>

          <div className="mt-8 space-y-4">
            {errorMajors ? (
              <ErrorMessage message="Không thể tải danh sách ngành" />
            ) : majors && majors.length > 0 ? (
              <div className="grid gap-4">
                {majors.map((major) => (
                  <Link
                    key={major.id}
                    to={`/majors/${major.id}`}
                    className="block rounded-lg border border-slate-200 p-4 transition hover:border-slate-900 hover:bg-slate-50"
                  >
                    <h3 className="font-medium text-slate-900">{major.name}</h3>
                    <p className="text-sm text-slate-600">{major.code}</p>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-slate-600">Không có ngành nào trong khoa này</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
