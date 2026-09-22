import {
  BadgeDollarSign,
  BookOpen,
  FileText,
  RefreshCw,
  TrendingUp,
  Users,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { useAdminActivities, useAdminStats, useAdminTrends } from '../features/admin/api'
import { RecentTransactions } from '../features/admin/components/RecentTransactions'
import { RecentUsers } from '../features/admin/components/RecentUsers'
import { StatCard } from '../features/admin/components/StatCard'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatVND(amount: number): string {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M ₫`
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K ₫`
  return `${amount.toLocaleString('vi-VN')} ₫`
}

function shortDate(iso: string): string {
  if (!iso) return ''
  const clean = iso.split('T')[0]
  const parts = clean.split('-')
  if (parts.length >= 3) {
    return `${parts[2]}/${parts[1]}`
  }
  return iso
}

const PIE_COLORS = ['#94a3b8', '#f59e0b'] // slate-400 = FREE, amber-500 = PRO

// ── Component ─────────────────────────────────────────────────────────────────

export function AdminDashboardPage() {
  const statsQuery = useAdminStats()
  const activitiesQuery = useAdminActivities()
  const trendsQuery = useAdminTrends()

  const isLoading =
    statsQuery.isLoading || activitiesQuery.isLoading || trendsQuery.isLoading

  const isFetching =
    statsQuery.isFetching || activitiesQuery.isFetching || trendsQuery.isFetching

  const hasError =
    statsQuery.isError || activitiesQuery.isError || trendsQuery.isError

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <Spinner />
      </div>
    )
  }

  if (hasError || !statsQuery.data || !activitiesQuery.data || !trendsQuery.data) {
    return (
      <div className="py-12">
        <ErrorMessage message="Không thể tải dữ liệu dashboard. Vui lòng kiểm tra lại kết nối hoặc thử lại." />
      </div>
    )
  }

  const stats = statsQuery.data
  const activities = activitiesQuery.data
  const trends = trendsQuery.data

  const userChartData = (trends.user_registrations ?? []).map((p) => ({
    date: shortDate(p.date),
    'Người dùng mới': p.count ?? 0,
  }))

  const freeUsers = stats.users?.free ?? 0
  const proUsers = stats.users?.pro ?? 0
  const totalUsers = freeUsers + proUsers
  const proPercent = totalUsers > 0 ? Math.round((proUsers / totalUsers) * 100) : 0
  const hasUserDistribution = freeUsers > 0 || proUsers > 0

  const pieData = [
    { name: 'FREE', value: freeUsers },
    { name: 'PRO',  value: proUsers },
  ]

  const handleRefresh = () => {
    void statsQuery.refetch()
    void activitiesQuery.refetch()
    void trendsQuery.refetch()
  }

  return (
    <div className="space-y-6">
      {/* ── Page Header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
              Tổng quan
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live System
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isFetching}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 shadow-2xs hover:bg-slate-50 hover:text-slate-900 active:scale-95 disabled:opacity-60 transition cursor-pointer"
            title="Làm mới dữ liệu"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            <span>{isFetching ? 'Đang cập nhật...' : 'Làm mới'}</span>
          </button>
        </div>
      </div>

      {/* ── Row 1: Stat Cards (4 columns) ────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <StatCard
          title="Tổng người dùng"
          value={stats.users.total.toLocaleString('vi-VN')}
          badge={`${proUsers} PRO`}
          sub={`${freeUsers} tài khoản FREE`}
          icon={Users}
          color="sky"
        />
        <StatCard
          title="Tài liệu thư viện"
          value={stats.documents.total.toLocaleString('vi-VN')}
          badge={`${stats.documents.public} công khai`}
          sub={stats.documents.draft > 0 ? `${stats.documents.draft} bản nháp` : undefined}
          icon={FileText}
          color="violet"
        />
        <StatCard
          title="Sổ tay cá nhân"
          value={stats.notebooks.total.toLocaleString('vi-VN')}
          badge="Workspace"
          sub="Tổng số notebooks được tạo"
          icon={BookOpen}
          color="emerald"
        />
        <StatCard
          title="Doanh thu VNPay"
          value={formatVND(stats.payments.total_revenue)}
          badge={`${stats.payments.successful_orders} đơn`}
          sub="Giao dịch thanh toán thành công"
          icon={BadgeDollarSign}
          color="amber"
        />
      </div>

      {/* ── Row 2: Charts (Area Chart 2/3 + Donut Chart 1/3) ──────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Area chart — user growth */}
        <div className="min-w-0 lg:col-span-2 rounded-2xl border border-slate-200/85 bg-white p-6 shadow-xs">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
                <TrendingUp className="h-4.5 w-4.5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Tăng trưởng người dùng mới
                </h2>
                <p className="text-xs text-slate-500">Số lượt đăng ký tài khoản trong 30 ngày gần nhất</p>
              </div>
            </div>
            <span className="hidden sm:inline-flex rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
              30 ngày qua
            </span>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <AreaChart
              data={userChartData}
              margin={{ top: 10, right: 12, left: -24, bottom: 0 }}
            >
              <defs>
                <linearGradient id="userGrowthGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={{ stroke: '#f1f5f9' }}
                interval={3}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  fontSize: 12,
                  boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#0f172a', fontWeight: 700, marginBottom: 4 }}
              />
              <Area
                type="monotone"
                dataKey="Người dùng mới"
                stroke="#0284c7"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#userGrowthGradient)"
                activeDot={{ r: 5, fill: '#0284c7', stroke: '#ffffff', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Donut chart — FREE vs PRO */}
        <div className="min-w-0 rounded-2xl border border-slate-200/85 bg-white p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
                  <Users className="h-4.5 w-4.5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Phân bổ gói cước</h2>
                  <p className="text-xs text-slate-500">Tỷ lệ FREE so với PRO</p>
                </div>
              </div>
              {hasUserDistribution && (
                <span className="rounded-lg bg-amber-50 border border-amber-200/60 px-2 py-0.5 text-xs font-bold text-amber-700">
                  {proPercent}% PRO
                </span>
              )}
            </div>

            {hasUserDistribution ? (
              <ResponsiveContainer width="100%" height={210}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="48%"
                    innerRadius={54}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((_, index) => (
                      <Cell
                        key={index}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => (
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>
                        {value}
                      </span>
                    )}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: 12,
                      border: '1px solid #e2e8f0',
                      fontSize: 12,
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                    formatter={(value: number) => [
                      `${value.toLocaleString('vi-VN')} người dùng`,
                      '',
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[210px] items-center justify-center text-xs text-slate-400">
                Chưa có dữ liệu phân bổ người dùng
              </div>
            )}
          </div>

          <div className="mt-3 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-center">
            <div className="rounded-xl bg-slate-50 p-2.5">
              <p className="text-[11px] font-medium text-slate-500 uppercase">Gói FREE</p>
              <p className="mt-0.5 text-base font-bold text-slate-800">
                {freeUsers.toLocaleString('vi-VN')}
              </p>
            </div>
            <div className="rounded-xl bg-amber-50/70 p-2.5">
              <p className="text-[11px] font-bold text-amber-700 uppercase">Gói PRO</p>
              <p className="mt-0.5 text-base font-black text-amber-900">
                {proUsers.toLocaleString('vi-VN')}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Row 3: Activity Tables (2 columns) ────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <RecentTransactions transactions={activities.recent_transactions ?? []} />
        <RecentUsers users={activities.recent_users ?? []} />
      </div>
    </div>
  )
}
