import { Users, Crown, Shield } from 'lucide-react'
import type { RecentUser } from '../api'

interface Props {
  users: RecentUser[]
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

export function RecentUsers({ users }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200/85 bg-white shadow-xs overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
            <Users className="h-4.5 w-4.5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Người dùng mới đăng ký</h2>
            <p className="text-xs text-slate-500">10 tài khoản được tạo gần nhất</p>
          </div>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
          {users.length} người dùng
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50/70 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px]">
            <tr>
              <th className="px-5 py-3.5 font-semibold">Thành viên</th>
              <th className="px-5 py-3.5 font-semibold">Vai trò</th>
              <th className="px-5 py-3.5 font-semibold">Gói cước</th>
              <th className="px-5 py-3.5 font-semibold">Ngày đăng ký</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-slate-400">
                  Chưa có người dùng nào.
                </td>
              </tr>
            ) : (
              users.map((u) => {
                const initial = (u.full_name?.[0] || u.email?.[0] || 'U').toUpperCase()
                const isPro = u.tier === 'PRO'
                const isAdmin = u.role === 'ADMIN'
                return (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500 text-white font-bold text-xs shadow-2xs">
                          {initial}
                        </div>
                        <div className="min-w-0 max-w-[190px]">
                          <p className="truncate font-semibold text-slate-900" title={u.full_name}>
                            {u.full_name}
                          </p>
                          <p className="truncate text-slate-400 text-[11px]" title={u.email}>
                            {u.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      {isAdmin ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-purple-50 border border-purple-200/80 px-2 py-0.5 text-[11px] font-bold text-purple-700">
                          <Shield className="h-3 w-3" />
                          ADMIN
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                          USER
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      {isPro ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-amber-500/15 to-yellow-500/15 border border-amber-400/50 px-2.5 py-0.5 text-[11px] font-black text-amber-700 uppercase tracking-wider">
                          <Crown className="h-3 w-3 text-amber-500" />
                          PRO
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
                          FREE
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 whitespace-nowrap">
                      {formatDate(u.created_at)}
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
