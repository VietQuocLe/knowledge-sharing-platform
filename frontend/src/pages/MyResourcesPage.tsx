import { ErrorMessage } from '../components/ui/ErrorMessage'

export function MyResourcesPage() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Tài liệu của tôi</h1>
      <p className="mt-2 text-sm text-slate-600">Theo dõi trạng thái và tiếp tục hoàn thiện các tài liệu của bạn.</p>
      <div className="mt-6">
        <ErrorMessage message="Trang này tạm thời ngừng hoạt động trong quá trình nâng cấp hệ thống." />
      </div>
    </div>
  )
}
