import { forwardRef } from 'react'

type InputProps = {
  label: string
  type?: string
  placeholder?: string
  error?: string
} & React.InputHTMLAttributes<HTMLInputElement>

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, type = 'text', placeholder, error, ...props },
  ref,
) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      <span className="mb-1 block">{label}</span>
      <input
        ref={ref}
        type={type}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-slate-900"
        {...props}
      />
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
    </label>
  )
})
