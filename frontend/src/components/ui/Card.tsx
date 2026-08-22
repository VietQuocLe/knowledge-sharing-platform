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
        rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300
        ${hoverable ? 'hover:-translate-y-1 hover:border-slate-350 hover:shadow-md cursor-pointer' : ''}
        ${className}
      `.trim()}
            {...props}
        >
            {children}
        </div>
    )
}
