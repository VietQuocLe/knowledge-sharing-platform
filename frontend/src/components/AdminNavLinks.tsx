import { NavLink } from 'react-router-dom'

export function AdminNavLinks() {
  return (
    <div className="flex items-center gap-4">
      <NavLink
        to="/admin"
        end
        className={({ isActive }) =>
          `text-sm font-medium transition ${
            isActive ? 'text-slate-900 font-bold' : 'text-slate-600 hover:text-slate-900'
          }`
        }
      >
        Tổng quan
      </NavLink>
      <NavLink
        to="/admin/taxonomy"
        className={({ isActive }) =>
          `text-sm font-medium transition ${
            isActive ? 'text-slate-900 font-bold' : 'text-slate-600 hover:text-slate-900'
          }`
        }
      >
        Phân loại
      </NavLink>
    </div>
  )
}
