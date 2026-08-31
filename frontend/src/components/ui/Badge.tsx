import type { ReactNode } from 'react'

type BadgeVariant = 'primary' | 'secondary' | 'success' | 'neutral' | 'warning' | 'danger'

interface BadgeProps {
    children: ReactNode
    variant?: BadgeVariant
    className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
    primary: 'bg-[#F0F7FF] text-slate-800 border-[#BAE6FD]',
    secondary: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-[#F0FDF4] text-[#16A34A] border-[#BBF7D0]',
    neutral: 'bg-[#F8F8F6] text-slate-600 border-slate-200/80',
    warning: 'bg-[#FEF9C3] text-amber-800 border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
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
