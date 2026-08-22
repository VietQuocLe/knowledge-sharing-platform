import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { Breadcrumb } from '../components/ui/Breadcrumb'
import { Card } from '../components/ui/Card'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { parseRouteId } from '../utils/parseRouteId'
import { Layers, ChevronRight } from 'lucide-react'

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
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Mã khoa không hợp lệ." />
      </div>
    )
  }

  if (isLoadingDept || isLoadingMajors) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (errorDept) {
    return (
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-10">
        <ErrorMessage message="Không thể tải thông tin khoa. Vui lòng kiểm tra lại kết nối." />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
      {/* Breadcrumb Navigation */}
      {department && (
        <Breadcrumb items={[{ label: department.name }]} />
      )}

      {department && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Cột trái: Thông tin tổng quan (lg:col-span-4) */}
          <div className="lg:col-span-4">
            <Card className="p-6 space-y-4">
              {/* Ảnh bìa / icon minh họa */}
              <div className="h-32 w-full bg-slate-50 border border-slate-200/60 rounded-xl flex items-center justify-center text-slate-400">
                <Layers className="h-12 w-12" />
              </div>
              <div className="space-y-2">
                <span className="inline-flex items-center rounded-md bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
                  Khoa #{department.id}
                </span>
                <h1 className="text-xl font-bold tracking-tight text-slate-900 leading-snug">
                  {department.name}
                </h1>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                Khoa chịu trách nhiệm quản lý giảng dạy chuyên môn và phát triển tài nguyên học tập cho các chuyên ngành học trực thuộc.
              </p>
            </Card>
          </div>

          {/* Cột phải: Danh sách chuyên ngành (lg:col-span-8) */}
          <div className="lg:col-span-8 space-y-6">
            <div className="border-b border-slate-150 pb-3">
              <h2 className="text-lg font-bold text-slate-900">Danh sách chuyên ngành</h2>
              <p className="text-sm text-slate-500 mt-1">
                Chọn một chuyên ngành bên dưới để xem chi tiết danh sách tài nguyên và môn học tương ứng.
              </p>
            </div>

            {errorMajors ? (
              <ErrorMessage message="Không thể tải danh sách ngành đào tạo trực thuộc khoa." />
            ) : majors && majors.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {majors.map((major) => (
                  <Link key={major.id} to={major.id ? `/majors/${major.id}` : '#'} className="group block">
                    <Card hoverable className="h-full flex flex-col justify-between p-5 border-slate-200/80 hover:border-slate-350">
                      <div className="space-y-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 border border-indigo-100/50 text-indigo-600">
                          <Layers className="h-5 w-5" />
                        </div>
                        <div>
                          <span className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-2xs font-semibold text-slate-600 mb-1.5">
                            Mã ngành: {major.code}
                          </span>
                          <h3 className="text-sm font-bold text-slate-900 leading-snug group-hover:text-indigo-650 transition line-clamp-2">
                            {major.name}
                          </h3>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-between text-2xs font-bold text-slate-450 uppercase group-hover:text-indigo-600 transition">
                        <span>Chi tiết môn học</span>
                        <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
                Hiện chưa có chuyên ngành nào được cấu hình trong khoa này.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

