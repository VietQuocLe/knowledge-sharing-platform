/**
 * ErrorMessage Component
 * Display error state instead of content, with optional custom message
 */

interface ErrorMessageProps {
  message?: string
  onRetry?: () => void
  className?: string
}

export function ErrorMessage({
  message = 'Đã xảy ra lỗi. Vui lòng thử lại.',
  onRetry,
  className = '',
}: ErrorMessageProps) {
  return (
    <div
      className={`
        flex flex-col items-center justify-center rounded-lg 
        border border-red-200 bg-red-50 p-6 text-center
        ${className}
      `.trim()}
    >
      <svg
        className="mb-3 h-6 w-6 text-red-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p className="mb-3 text-sm text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm font-medium text-red-600 transition hover:text-red-800"
        >
          Thử lại
        </button>
      )}
    </div>
  )
}
