import { useQuery } from '@tanstack/react-query'
import { createJsonRequest } from '../../api/apiClient'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AdminStats {
  users: { total: number; pro: number; free: number; active: number }
  documents: { total: number; public: number; draft: number }
  notebooks: { total: number }
  payments: { total_revenue: number; successful_orders: number }
}

export interface RecentTransaction {
  order_code: string
  user_email: string
  amount: number
  plan_type: string
  status: 'PENDING' | 'SUCCESS' | 'CANCELLED'
  created_at: string
  paid_at: string | null
}

export interface RecentUser {
  id: number
  email: string
  full_name: string
  tier: 'FREE' | 'PRO'
  role: 'USER' | 'PREMIUM_USER' | 'ADMIN'
  is_active: boolean
  created_at: string
}

export interface AdminActivities {
  recent_transactions: RecentTransaction[]
  recent_users: RecentUser[]
}

export interface TrendPoint {
  date: string
  count?: number
  amount?: number
}

export interface AdminTrends {
  user_registrations: TrendPoint[]
  daily_revenue: TrendPoint[]
}

// ── API functions ─────────────────────────────────────────────────────────────

const adminApi = {
  getStats: () =>
    createJsonRequest<AdminStats>({ method: 'GET', url: '/admin/stats' }),
  getActivities: () =>
    createJsonRequest<AdminActivities>({ method: 'GET', url: '/admin/activities' }),
  getTrends: () =>
    createJsonRequest<AdminTrends>({ method: 'GET', url: '/admin/trends' }),
}

// ── Query keys ────────────────────────────────────────────────────────────────

export const adminKeys = {
  all: ['admin'] as const,
  stats: () => [...adminKeys.all, 'stats'] as const,
  activities: () => [...adminKeys.all, 'activities'] as const,
  trends: () => [...adminKeys.all, 'trends'] as const,
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useAdminStats() {
  return useQuery({
    queryKey: adminKeys.stats(),
    queryFn: adminApi.getStats,
    staleTime: 60_000,
  })
}

export function useAdminActivities() {
  return useQuery({
    queryKey: adminKeys.activities(),
    queryFn: adminApi.getActivities,
    staleTime: 30_000,
  })
}

export function useAdminTrends() {
  return useQuery({
    queryKey: adminKeys.trends(),
    queryFn: adminApi.getTrends,
    staleTime: 5 * 60_000,
  })
}
