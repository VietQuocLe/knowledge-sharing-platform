import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'

export function DepartmentsPage() {
  const { data: departments, isLoading, error } = useQuery({
    queryKey: taxonomyKeys.departmentsList(),
    queryFn: taxonomyApi.getDepartments,
  })

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-12">
        <ErrorMessage message="Không thể tải danh sách khoa" />
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

      <h1 className="text-3xl font-semibold text-slate-900">Danh sách khoa</h1>
      <p className="mt-2 text-slate-600">Chọn khoa để xem các ngành và môn học.</p>

      {departments && departments.length > 0 ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {departments.map((department) => (
            <Link
              key={department.id}
              to={`/departments/${department.id}`}
              className="rounded-lg border border-slate-200 p-4 transition hover:border-slate-900 hover:bg-slate-50"
            >
              <h2 className="font-medium text-slate-900">{department.name}</h2>
            </Link>
          ))}
        </div>
      ) : (
        <p className="mt-8 text-slate-600">Chưa có khoa nào.</p>
      )}
    </div>
  )
}
