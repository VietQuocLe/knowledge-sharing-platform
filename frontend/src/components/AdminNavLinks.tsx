import { Link } from 'react-router-dom'

export function AdminNavLinks() {
  return (
    <>
      {/* [PAUSED - Admin branch] Moderation page temporarily hidden
      <Link to="/admin/moderation" className="text-sm text-slate-600 hover:text-slate-900">
        Kiểm duyệt
      </Link>
      */}
      <Link to="/admin/taxonomy" className="text-sm text-slate-600 hover:text-slate-900">
        Phân loại
      </Link>
    </>
  )
}
