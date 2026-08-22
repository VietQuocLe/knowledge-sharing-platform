import type { ReactNode } from 'react'

type BadgeVariant = 'primary' | 'secondary' | 'success' | 'neutral' | 'warning' | 'danger'

interface BadgeProps {
    children: ReactNode
    variant?: BadgeVariant
    className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
    primary: 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
    secondary: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    neutral: 'bg-slate-50 text-slate-600 border-slate-200/60',
    warning: 'bg-amber-50 text-amber-700 border-amber-200/60',
    danger: 'bg-rose-50 text-rose-700 border-rose-200/60',
}

export function Badge({ children, variant = 'neutral', className = '' }: BadgeProps) {
    return (
        <span
            className={`
        inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors duration-250
        ${variantStyles[variant]}
        ${className}
      `.trim()}
        >
            {children}
        </span>
    )
}
