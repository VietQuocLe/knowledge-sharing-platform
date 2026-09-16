import { useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { getApiErrorMessage } from '../api/getApiErrorMessage'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Modal } from '../components/ui/Modal'
import { Spinner } from '../components/ui/Spinner'
import type { Department, Major, Subject } from '../features/taxonomy/api'
import { useDepartments } from '../features/taxonomy/hooks/useDepartments'
import { useMajors } from '../features/taxonomy/hooks/useMajors'
import { useSubjects } from '../features/taxonomy/hooks/useSubjects'
import { useCreateDepartment } from '../features/taxonomy/hooks/useCreateDepartment'
import { useUpdateDepartment } from '../features/taxonomy/hooks/useUpdateDepartment'
import { useDeleteDepartment } from '../features/taxonomy/hooks/useDeleteDepartment'
import { useCreateMajor } from '../features/taxonomy/hooks/useCreateMajor'
import { useUpdateMajor } from '../features/taxonomy/hooks/useUpdateMajor'
import { useDeleteMajor } from '../features/taxonomy/hooks/useDeleteMajor'
import { useCreateSubject } from '../features/taxonomy/hooks/useCreateSubject'
import { useUpdateSubject } from '../features/taxonomy/hooks/useUpdateSubject'
import { useDeleteSubject } from '../features/taxonomy/hooks/useDeleteSubject'
import { DepartmentMajorSubjectPicker } from '../features/taxonomy/components/DepartmentMajorSubjectPicker'

type EntityType = 'department' | 'major' | 'subject'
type EditingEntity = { type: EntityType; entity?: Department | Major | Subject } | null

interface TabConfig {
  key: EntityType
  label: string
  count: number
  description: string
  addLabel: string
  columns: string[]
  rows: Array<Department | Major | Subject>
  render: (item: Department | Major | Subject) => string[]
}

const entityTypeLabel: Record<EntityType, string> = {
  department: 'khoa',
  major: 'ngành',
  subject: 'môn học',
}

/**
 * Safely extracts entity count: supports both direct arrays and paginated responses ({ total } / { count }).
 */
function getSafeCount(data: unknown): number {
  if (!data) return 0
  if (Array.isArray(data)) return data.length
  if (typeof data === 'object' && data !== null) {
    if ('total' in data && typeof (data as { total: unknown }).total === 'number') {
      return (data as { total: number }).total
    }
    if ('count' in data && typeof (data as { count: unknown }).count === 'number') {
      return (data as { count: number }).count
    }
  }
  return 0
}

export function AdminTaxonomyPage() {
  const [activeTab, setActiveTab] = useState<EntityType>('department')
  const [editing, setEditing] = useState<EditingEntity>(null)
  const [deleting, setDeleting] = useState<EditingEntity>(null)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [departmentId, setDepartmentId] = useState<number | null>(null)
  const [majorId, setMajorId] = useState<number | null>(null)

  const departmentsQuery = useDepartments()
  const majorsQuery = useMajors()
  const subjectsQuery = useSubjects()

  const createDepartment = useCreateDepartment()
  const updateDepartment = useUpdateDepartment()
  const deleteDepartment = useDeleteDepartment()

  const createMajor = useCreateMajor()
  const updateMajor = useUpdateMajor()
  const deleteMajor = useDeleteMajor()

  const createSubject = useCreateSubject()
  const updateSubject = useUpdateSubject()
  const deleteSubject = useDeleteSubject()

  const handleSave = async () => {
    if (!editing) return
    const id = editing.entity?.id
    try {
      if (editing.type === 'department') {
        if (id) {
          await updateDepartment.mutateAsync({ id, data: { name } })
        } else {
          await createDepartment.mutateAsync({ name })
        }
      } else if (editing.type === 'major') {
        const payload = { name, code, department_id: departmentId! }
        if (id) {
          await updateMajor.mutateAsync({ id, data: payload })
        } else {
          await createMajor.mutateAsync(payload)
        }
      } else {
        const payload = { name, code, department_id: departmentId!, major_ids: majorId ? [majorId] : [] }
        if (id) {
          await updateSubject.mutateAsync({ id, data: payload })
        } else {
          await createSubject.mutateAsync(payload)
        }
      }
      setEditing(null)
      toast.success('Đã lưu phân loại.')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Không thể lưu. Hãy kiểm tra các trường bắt buộc.'))
    }
  }

  const handleDelete = async () => {
    if (!deleting?.entity) return
    const id = deleting.entity.id
    try {
      if (deleting.type === 'department') {
        await deleteDepartment.mutateAsync(id)
      } else if (deleting.type === 'major') {
        await deleteMajor.mutateAsync(id)
      } else {
        await deleteSubject.mutateAsync(id)
      }
      setDeleting(null)
      toast.success('Đã xóa phân loại.')
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Không thể xóa phân loại.'))
    }
  }

  const isSaving =
    createDepartment.isPending ||
    updateDepartment.isPending ||
    createMajor.isPending ||
    updateMajor.isPending ||
    createSubject.isPending ||
    updateSubject.isPending

  const isDeleting =
    deleteDepartment.isPending ||
    deleteMajor.isPending ||
    deleteSubject.isPending

  const openEditor = (type: EntityType, entity?: Department | Major | Subject) => {
    setEditing({ type, entity })
    setName(entity?.name ?? '')
    setCode(entity && type !== 'department' ? (entity as Major | Subject).code : '')
    if (entity && type === 'major') {
      setDepartmentId((entity as Major).department_id)
      setMajorId(null)
    } else if (entity && type === 'subject') {
      const subject = entity as Subject
      const firstMajor = subject.majors[0]
      setDepartmentId(firstMajor?.department_id ?? null)
      setMajorId(firstMajor?.id ?? null)
    } else {
      setDepartmentId(null)
      setMajorId(null)
    }
  }

  const currentType = editing?.type
  const isFormValid = Boolean(name.trim()) && (currentType === 'department' || (code.trim() && departmentId !== null && (currentType === 'major' || majorId !== null)))

  // Array-driven tab configuration for high scalability
  const tabs: TabConfig[] = [
    {
      key: 'department',
      label: 'Khoa',
      count: getSafeCount(departmentsQuery.data),
      description: 'Danh mục các Khoa trực thuộc trường',
      addLabel: 'Thêm Khoa',
      columns: ['Tên'],
      rows: departmentsQuery.data ?? [],
      render: (item) => [(item as Department).name],
    },
    {
      key: 'major',
      label: 'Ngành',
      count: getSafeCount(majorsQuery.data),
      description: 'Danh mục các Ngành đào tạo trực thuộc Khoa',
      addLabel: 'Thêm Ngành',
      columns: ['Mã', 'Tên', 'Khoa'],
      rows: majorsQuery.data ?? [],
      render: (item) => {
        const major = item as Major
        return [major.code, major.name, major.department?.name ?? `#${major.department_id}`]
      },
    },
    {
      key: 'subject',
      label: 'Môn học',
      count: getSafeCount(subjectsQuery.data),
      description: 'Danh mục các Môn học thuộc các Ngành',
      addLabel: 'Thêm Môn học',
      columns: ['Mã', 'Tên', 'Ngành'],
      rows: subjectsQuery.data ?? [],
      render: (item) => {
        const subject = item as Subject
        return [subject.code, subject.name, subject.majors.map((m) => m.name).join(', ') || '—']
      },
    },
  ]

  const currentTab = tabs.find((t) => t.key === activeTab) ?? tabs[0]

  if (departmentsQuery.isLoading || majorsQuery.isLoading || subjectsQuery.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    )
  }

  if (departmentsQuery.error || majorsQuery.error || subjectsQuery.error) {
    return <ErrorMessage message="Không thể tải phân loại học liệu." />
  }

  return (
    <div className="space-y-6 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Phân loại học liệu</h1>
          <p className="mt-1 text-sm text-slate-500">Quản lý phân cấp danh mục Khoa, Ngành và Môn học trong toàn hệ thống.</p>
        </div>
        <button
          type="button"
          onClick={() => openEditor(currentTab.key)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition cursor-pointer shrink-0"
        >
          <Plus className="h-4 w-4 pointer-events-none" />
          <span>{currentTab.addLabel}</span>
        </button>
      </div>

      {/* Array-driven Tabs Bar */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = tab.key === activeTab
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2.5 px-4 py-3 text-sm font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap -mb-px ${
                isActive
                  ? 'border-slate-900 text-slate-900 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                  isActive ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {tab.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Active Tab Table Content */}
      <div className="rounded-xl border border-slate-200/80 overflow-hidden bg-white shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-600 text-xs font-semibold uppercase tracking-wider">
              <tr>
                {currentTab.columns.map((column) => (
                  <th key={column} className="px-4 py-3.5 font-semibold">
                    {column}
                  </th>
                ))}
                <th className="px-4 py-3.5 text-right font-semibold">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {currentTab.rows.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                  {currentTab.render(item).map((value, index) => (
                    <td key={index} className="px-4 py-3.5 text-slate-700 font-medium">
                      {value}
                    </td>
                  ))}
                  <td className="whitespace-nowrap px-4 py-3.5 text-right">
                    <button
                      type="button"
                      onClick={() => openEditor(currentTab.key, item)}
                      className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 font-medium text-xs mr-3 px-2 py-1 rounded-md hover:bg-slate-100 transition cursor-pointer"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      Sửa
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleting({ type: currentTab.key, entity: item })}
                      className="inline-flex items-center gap-1 text-rose-600 hover:text-rose-700 font-medium text-xs px-2 py-1 rounded-md hover:bg-rose-50 transition cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Xóa
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {currentTab.rows.length === 0 && (
          <div className="py-12 text-center text-slate-400 text-sm">
            Chưa có dữ liệu cho {currentTab.label.toLowerCase()}.
          </div>
        )}
      </div>

      {/* Modal Thêm / Sửa */}
      <Modal isOpen={editing !== null} title={`${editing?.entity ? 'Sửa' : 'Thêm'} ${currentType ? entityTypeLabel[currentType] : ''}`}>
        <div className="space-y-4">
          {currentType !== 'department' && (
            <label className="block text-sm font-medium text-slate-700">
              Mã
              <input
                value={code}
                onChange={(event) => setCode(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
              />
            </label>
          )}
          <label className="block text-sm font-medium text-slate-700">
            Tên
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </label>

          {currentType === 'major' && (
            <DepartmentMajorSubjectPicker
              departmentId={departmentId}
              majorId={null}
              subjectId={null}
              showMajor={false}
              showSubject={false}
              onChange={(values) => {
                setDepartmentId(values.departmentId)
              }}
              departmentRequired
            />
          )}

          {currentType === 'subject' && (
            <DepartmentMajorSubjectPicker
              departmentId={departmentId}
              majorId={majorId}
              subjectId={null}
              showSubject={false}
              onChange={(values) => {
                setDepartmentId(values.departmentId)
                setMajorId(values.majorId)
              }}
              departmentRequired
              majorRequired
            />
          )}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setEditing(null)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition cursor-pointer"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={() => handleSave()}
            disabled={!isFormValid || isSaving}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 disabled:opacity-60 transition cursor-pointer"
          >
            {isSaving && <Spinner size="sm" className="border-slate-500 border-t-white" />}
            Lưu
          </button>
        </div>
      </Modal>

      {/* Modal Xác nhận xóa */}
      <Modal isOpen={deleting !== null} title="Xác nhận xóa">
        <p className="text-sm text-slate-600">
          Bạn có chắc chắn muốn xóa “{deleting?.entity?.name}”? Thao tác này không thể hoàn tác.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setDeleting(null)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition cursor-pointer"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={() => handleDelete()}
            disabled={isDeleting}
            className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-red-700 disabled:opacity-60 transition cursor-pointer"
          >
            {isDeleting && <Spinner size="sm" className="border-red-300 border-t-white" />}
            Xóa
          </button>
        </div>
      </Modal>
    </div>
  )
}
