import { Link } from 'react-router-dom'
import type { Document } from '../api'

type PublicDocumentCardProps = {
  document: Document
}

export function PublicResourceCard({ document }: PublicDocumentCardProps) {
  return (
    <Link
      to={`/documents/${document.id}`}
      className="block rounded-lg border border-slate-200 p-4 transition hover:border-slate-900 hover:bg-slate-50"
    >
      <div className="font-medium text-slate-900">{document.title}</div>
      {document.description ? (
        <div className="mt-1 line-clamp-2 text-sm text-slate-600">{document.description}</div>
      ) : null}
      <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
        <span className="rounded bg-slate-100 px-2 py-1">{document.resource_type}</span>
        <span>{new Date(document.created_at).toLocaleDateString('vi-VN')}</span>
      </div>
    </Link>
  )
}
