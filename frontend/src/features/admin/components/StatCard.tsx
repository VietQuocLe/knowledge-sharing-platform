import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  sub?: string
  badge?: string
  icon: LucideIcon
  color: 'sky' | 'violet' | 'emerald' | 'amber'
}

const colorMap: Record<
  StatCardProps['color'],
  { bg: string; icon: string; borderHover: string; badge: string }
> = {
  sky: {
    bg: 'bg-sky-50 text-sky-600',
    icon: 'text-sky-600',
    borderHover: 'hover:border-sky-300/80',
    badge: 'bg-sky-50 text-sky-700 border-sky-200/60',
  },
  violet: {
    bg: 'bg-violet-50 text-violet-600',
    icon: 'text-violet-600',
    borderHover: 'hover:border-violet-300/80',
    badge: 'bg-violet-50 text-violet-700 border-violet-200/60',
  },
  emerald: {
    bg: 'bg-emerald-50 text-emerald-600',
    icon: 'text-emerald-600',
    borderHover: 'hover:border-emerald-300/80',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
  },
  amber: {
    bg: 'bg-amber-50 text-amber-600',
    icon: 'text-amber-600',
    borderHover: 'hover:border-amber-300/80',
    badge: 'bg-amber-50 text-amber-700 border-amber-200/60',
  },
}

export function StatCard({ title, value, sub, badge, icon: Icon, color }: StatCardProps) {
  const c = colorMap[color]
  return (
    <div
      className={`group relative flex flex-col justify-between rounded-2xl border border-slate-200/85 bg-white p-5 shadow-xs transition-all duration-200 ${c.borderHover} hover:shadow-md`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${c.bg} shadow-2xs transition-transform duration-200 group-hover:scale-105`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-3">
        <p className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
          {value}
        </p>

        {(sub || badge) && (
          <div className="mt-2.5 flex items-center gap-2 flex-wrap">
            {badge && (
              <span
                className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-bold ${c.badge}`}
              >
                {badge}
              </span>
            )}
            {sub && (
              <span className="text-xs font-medium text-slate-500">
                {sub}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
