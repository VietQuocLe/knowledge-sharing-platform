import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { GraduationCap, ArrowRight } from 'lucide-react'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { Card } from '../components/ui/Card'
import { DepartmentCardSkeleton } from '../components/ui/Skeleton'
import { ErrorMessage } from '../components/ui/ErrorMessage'

export function HomePage() {
  const { data: departments, isLoading, error } = useQuery({
    queryKey: taxonomyKeys.departmentsList(),
    queryFn: taxonomyApi.getDepartments,
  })


  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-10 font-sans">
      {/* Hero Section */}
      <div className="pt-2 pb-4">
        <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl text-slate-900 leading-snug">
          Nền tảng chia sẻ học liệu trực tuyến
        </h1>
      </div>

      {/* Main Browse Section */}
      <div>
        <div className="mb-6 flex flex-col gap-1.5">
          <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Danh sách Khoa đào tạo
          </h2>
          <p className="text-slate-550 text-xs sm:text-sm">
            Chọn khoa để bắt đầu quá trình khám phá tài liệu môn học.
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <DepartmentCardSkeleton key={i} />
            ))}
          </div>
        ) : error ? (
          <ErrorMessage message="Không thể tải danh sách khoa. Vui lòng kiểm tra lại kết nối mạng hoặc thử lại sau." />
        ) : departments && departments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {departments.map((department) => (
              <Link key={department.id} to={`/departments/${department.id}`} className="group block h-full">
                <Card
                  hoverable
                  className="h-full flex flex-col justify-between p-6 border-slate-200/80 bg-white hover:border-[#BAE6FD] hover:shadow-md transition-all duration-250 rounded-2xl cursor-pointer space-y-4"
                >
                  <div className="space-y-4">
                    {/* Ảnh bìa / icon minh họa */}
                    <div className="h-32 w-full bg-slate-50 border border-slate-200/60 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-[#0284C7] group-hover:bg-[#F0F7FF]/50 transition duration-200">
                      <GraduationCap className="h-12 w-12 group-hover:scale-105 transition duration-200" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-lg font-bold tracking-tight text-slate-900 group-hover:text-sky-800 transition-colors duration-200 leading-snug">
                        {department.name}
                      </h3>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-sky-600 group-hover:text-sky-700">
                    <span>Khám phá ngành &amp; môn học</span>
                    <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-1" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-350 p-8 text-center text-slate-500 text-sm">
            Hiện chưa có dữ liệu khoa nào trên hệ thống.
          </div>
        )}
      </div>
    </div>
  )
}
