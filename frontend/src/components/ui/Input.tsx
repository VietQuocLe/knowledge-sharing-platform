type InputProps = {
  label: string
  type?: string
  placeholder?: string
}

export function Input({ label, type = 'text', placeholder }: InputProps) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      <span className="mb-1 block">{label}</span>
      <input
        type={type}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-slate-900"
      />
    </label>
  )
}
