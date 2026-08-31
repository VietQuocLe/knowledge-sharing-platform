import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    children: ReactNode
    hoverable?: boolean
    className?: string
}

export function Card({ children, hoverable = false, className = '', ...props }: CardProps) {
    return (
        <div
            className={`
        rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all duration-250
        ${hoverable ? 'hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md cursor-pointer' : ''}
        ${className}
      `.trim()}
            {...props}
        >
            {children}
        </div>
    )
}
