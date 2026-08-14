/**
 * Spinner Component
 * Compact loading indicator for both full-container and inline usage
 */

type SpinnerSize = 'sm' | 'md' | 'lg'

interface SpinnerProps {
  size?: SpinnerSize
  className?: string
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-8 w-8 border-3',
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div
      className={`
        animate-spin rounded-full border-slate-200
        border-t-slate-900
        ${sizeStyles[size]}
        ${className}
      `.trim()}
      aria-label="Đang tải"
    />
  )
}
