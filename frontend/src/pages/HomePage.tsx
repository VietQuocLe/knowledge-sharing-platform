import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Building2, ArrowRight, GraduationCap, Layers } from 'lucide-react'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'

export function HomePage() {
  const { data: departments, isLoading, error } = useQuery({
    queryKey: taxonomyKeys.departmentsList(),
    queryFn: taxonomyApi.getDepartments,
  })

  const getDepartmentIcon = (deptId: number) => {
    switch (deptId) {
      case 1:
        return <GraduationCap className="h-5.5 w-5.5" />
      case 2:
        return <Building2 className="h-5.5 w-5.5" />
      default:
        return <Layers className="h-5.5 w-5.5" />
    }
  }

  const getDepartmentDescription = (deptId: number) => {
    switch (deptId) {
      case 1:
        return 'Kho lưu trữ tài liệu về Cấu trúc dữ liệu, Lập trình, Trí tuệ nhân tạo và các công nghệ mới.'
      case 2:
        return 'Tổng hợp giáo trình, đề cương bài giảng và tài liệu ôn tập khối ngành Kinh tế, Quản trị, Marketing.'
      default:
        return 'Tài nguyên tài liệu ôn tập và đề ý kiến bài giảng trực thuộc các chuyên ngành đào tạo.'
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-10 font-sans">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 px-8 py-10 shadow-lg text-white">
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl text-white leading-snug">
            Nền tảng chia sẻ học liệu trực tuyến
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed">
            Hệ thống tổ chức tài liệu thông minh theo Khoa → Ngành → Môn học giúp sinh viên dễ dàng tra cứu, tiếp cận những tài nguyên học tập chất lượng nhất từ giảng viên và bạn học.
          </p>
        </div>

        {/* Decorative subtle background shapes */}
        <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/2 -translate-x-12 translate-y-12 h-80 w-80 rounded-full bg-slate-500/10 blur-3xl pointer-events-none" />
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
          <div className="flex items-center justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : error ? (
          <ErrorMessage message="Không thể tải danh sách khoa. Vui lòng kiểm tra lại kết nối mạng hoặc thử lại sau." />
        ) : departments && departments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {departments.map((department) => (
              <Link key={department.id} to={`/departments/${department.id}`} className="group block">
                <Card
                  hoverable
                  className="h-full flex flex-col justify-between p-5 border-slate-200 bg-white hover:border-indigo-300 hover:shadow-md transition-all duration-300 rounded-2xl group cursor-pointer"
                >
                  <div className="space-y-4">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 shadow-3xs">
                      {getDepartmentIcon(department.id)}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors duration-200">
                        {department.name}
                      </h3>
                      <p className="text-xs text-slate-500 leading-relaxed mt-1.5 line-clamp-2">
                        {getDepartmentDescription(department.id)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-6 pt-3 border-t border-slate-50 flex items-center justify-between text-2xs font-bold text-slate-450 uppercase group-hover:text-indigo-600 transition-colors duration-200">
                    <span>Ngành trực thuộc &amp; Môn học</span>
                    <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1 text-slate-400 group-hover:text-indigo-600" />
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
