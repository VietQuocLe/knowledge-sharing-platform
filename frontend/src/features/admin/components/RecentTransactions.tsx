import { CreditCard } from 'lucide-react'
import type { RecentTransaction } from '../api'

interface Props {
  transactions: RecentTransaction[]
}

const statusConfig = {
  SUCCESS: {
    label: 'Thành công',
    className: 'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
    dot: 'bg-emerald-500',
  },
  PENDING: {
    label: 'Chờ xử lý',
    className: 'bg-amber-50 text-amber-700 border border-amber-200/80',
    dot: 'bg-amber-500',
  },
  CANCELLED: {
    label: 'Đã hủy',
    className: 'bg-rose-50 text-rose-700 border border-rose-200/80',
    dot: 'bg-rose-500',
  },
}

const planLabel: Record<string, string> = {
  '1_MONTH': '1 tháng',
  '3_MONTH': '3 tháng',
  '6_MONTH': '6 tháng',
  '1_YEAR': '1 năm',
}

function formatVND(amount: number): string {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function RecentTransactions({ transactions }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/85 bg-white shadow-xs overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
            <CreditCard className="h-4.5 w-4.5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Giao dịch VNPay gần nhất</h2>
            <p className="text-xs text-slate-500">10 giao dịch mới nhất trên hệ thống</p>
          </div>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
          {transactions.length} giao dịch
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50/70 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px]">
            <tr>
              <th className="px-5 py-3.5 font-semibold">Mã đơn</th>
              <th className="px-5 py-3.5 font-semibold">Khách hàng</th>
              <th className="px-5 py-3.5 font-semibold">Gói</th>
              <th className="px-5 py-3.5 font-semibold">Số tiền</th>
              <th className="px-5 py-3.5 font-semibold">Trạng thái</th>
              <th className="px-5 py-3.5 font-semibold">Thời gian</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-slate-400">
                  Chưa có giao dịch nào được ghi nhận.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const s = statusConfig[tx.status] ?? statusConfig.PENDING
                const initial = (tx.user_email?.[0] || 'U').toUpperCase()
                return (
                  <tr key={tx.order_code} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-mono font-medium text-slate-800 whitespace-nowrap">
                      {tx.order_code}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5 max-w-[200px]" title={tx.user_email}>
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-700 font-bold text-[11px]">
                          {initial}
                        </div>
                        <span className="truncate text-slate-700 font-medium">{tx.user_email}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-slate-600 font-medium">
                      {planLabel[tx.plan_type] ?? tx.plan_type}
                    </td>
                    <td className="px-5 py-3.5 font-bold text-slate-900 whitespace-nowrap">
                      {formatVND(tx.amount)}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${s.className}`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
                        {s.label}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 whitespace-nowrap">
                      {formatDate(tx.created_at)}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
