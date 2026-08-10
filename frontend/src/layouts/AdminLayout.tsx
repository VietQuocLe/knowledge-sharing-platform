import type { ReactNode } from 'react'

export function AdminLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-slate-100">{children}</div>
}
