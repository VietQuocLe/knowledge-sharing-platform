import { useState } from 'react'
import toast from 'react-hot-toast'
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

const entityTypeLabel: Record<EntityType, string> = {
  department: 'khoa',
  major: 'ngành',
  subject: 'môn học',
}

const sectionTitle: Record<EntityType, string> = {
  department: 'Khoa',
  major: 'Ngành',
  subject: 'Môn học',
}

export function AdminTaxonomyPage() {
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

  const section = (title: string, type: EntityType, rows: Array<Department | Major | Subject>, columns: string[], render: (item: Department | Major | Subject) => string[]) => (
    <section className="rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between gap-3"><h2 className="text-lg font-semibold text-slate-900">{title}</h2><button onClick={() => openEditor(type)} className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">Thêm</button></div>
      <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b text-slate-600"><tr>{columns.map((column) => <th key={column} className="px-3 py-2 font-medium">{column}</th>)}<th className="px-3 py-2">Thao tác</th></tr></thead><tbody>{rows.map((item) => <tr key={item.id} className="border-b border-slate-100"><>{render(item).map((value, index) => <td key={index} className="px-3 py-3 text-slate-700">{value}</td>)}</><td className="whitespace-nowrap px-3 py-3"><button onClick={() => openEditor(type, item)} className="mr-3 text-slate-700 hover:underline">Sửa</button><button onClick={() => setDeleting({ type, entity: item })} className="text-red-600 hover:underline">Xóa</button></td></tr>)}</tbody></table></div>
      {rows.length === 0 ? <p className="mt-3 text-sm text-slate-500">Chưa có dữ liệu.</p> : null}
    </section>
  )

  if (departmentsQuery.isLoading || majorsQuery.isLoading || subjectsQuery.isLoading) return <div className="flex justify-center py-10"><Spinner /></div>
  if (departmentsQuery.error || majorsQuery.error || subjectsQuery.error) return <ErrorMessage message="Không thể tải phân loại học liệu." />

  return <div className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div><h1 className="text-2xl font-semibold text-slate-900">Phân loại học liệu</h1><p className="mt-2 text-sm text-slate-600">Quản lý khoa, ngành và môn học.</p></div>
    {section(sectionTitle.department, 'department', departmentsQuery.data ?? [], ['Tên'], (item) => [(item as Department).name])}
    {section(sectionTitle.major, 'major', majorsQuery.data ?? [], ['Mã', 'Tên', 'Khoa'], (item) => { const major = item as Major; return [major.code, major.name, major.department?.name ?? `#${major.department_id}`] })}
    {section(sectionTitle.subject, 'subject', subjectsQuery.data ?? [], ['Mã', 'Tên', 'Ngành'], (item) => { const subject = item as Subject; return [subject.code, subject.name, subject.majors.map((major) => major.name).join(', ') || '—'] })}

    <Modal isOpen={editing !== null} title={`${editing?.entity ? 'Sửa' : 'Thêm'} ${currentType ? entityTypeLabel[currentType] : ''}`}>
      <div className="space-y-4">
        {currentType !== 'department' ? <label className="block text-sm font-medium text-slate-700">Mã<input value={code} onChange={(event) => setCode(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label> : null}
        <label className="block text-sm font-medium text-slate-700">Tên<input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>

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
      <div className="mt-5 flex justify-end gap-2"><button onClick={() => setEditing(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => handleSave()} disabled={!isFormValid || isSaving} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-60">{isSaving ? <Spinner size="sm" className="border-slate-500 border-t-white" /> : null}Lưu</button></div>
    </Modal>
    <Modal isOpen={deleting !== null} title="Xác nhận xóa"><p className="text-sm text-slate-600">Xóa “{deleting?.entity?.name}”?</p><div className="mt-5 flex justify-end gap-2"><button onClick={() => setDeleting(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => handleDelete()} disabled={isDeleting} className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm text-white disabled:opacity-60">{isDeleting ? <Spinner size="sm" className="border-red-300 border-t-white" /> : null}Xóa</button></div></Modal>
  </div>
}
