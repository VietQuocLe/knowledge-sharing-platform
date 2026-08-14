import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { getApiErrorMessage } from '../api/getApiErrorMessage'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Modal } from '../components/ui/Modal'
import { Spinner } from '../components/ui/Spinner'
import { taxonomyApi, type Department, type Major, type Subject } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'

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
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<EditingEntity>(null)
  const [deleting, setDeleting] = useState<EditingEntity>(null)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [majorIds, setMajorIds] = useState<number[]>([])

  const departmentsQuery = useQuery({ queryKey: taxonomyKeys.departmentsList(), queryFn: taxonomyApi.getDepartments })
  const majorsQuery = useQuery({ queryKey: taxonomyKeys.majorsList(), queryFn: taxonomyApi.getMajors })
  const subjectsQuery = useQuery({ queryKey: taxonomyKeys.subjectsList(), queryFn: taxonomyApi.getSubjects })
  const editorDepartmentId =
    editing?.type === 'subject' && departmentId ? Number(departmentId) : null
  const editorMajorsQuery = useQuery({
    queryKey: taxonomyKeys.majorsList(editorDepartmentId ?? undefined),
    queryFn: () => taxonomyApi.getMajorsByDepartment(editorDepartmentId!),
    enabled: editorDepartmentId !== null && editorDepartmentId > 0,
  })
  const invalidateTaxonomy = () => queryClient.invalidateQueries({ queryKey: taxonomyKeys.all })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!editing) throw new Error('No entity selected')
      const id = editing.entity?.id
      if (editing.type === 'department') return id ? taxonomyApi.updateDepartment(id, { name }) : taxonomyApi.createDepartment({ name })
      if (editing.type === 'major') {
        const payload = { name, code, department_id: Number(departmentId) }
        return id ? taxonomyApi.updateMajor(id, payload) : taxonomyApi.createMajor(payload)
      }
      const payload = { name, code, department_id: Number(departmentId), major_ids: majorIds }
      return id ? taxonomyApi.updateSubject(id, payload) : taxonomyApi.createSubject(payload)
    },
    onSuccess: () => { setEditing(null); void invalidateTaxonomy(); toast.success('Đã lưu phân loại.') },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể lưu. Hãy kiểm tra các trường bắt buộc.')),
  })
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!deleting?.entity) throw new Error('No entity selected')
      if (deleting.type === 'department') return taxonomyApi.deleteDepartment(deleting.entity.id)
      if (deleting.type === 'major') return taxonomyApi.deleteMajor(deleting.entity.id)
      return taxonomyApi.deleteSubject(deleting.entity.id)
    },
    onSuccess: () => { setDeleting(null); void invalidateTaxonomy(); toast.success('Đã xóa phân loại.') },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể xóa phân loại.')),
  })

  const openEditor = (type: EntityType, entity?: Department | Major | Subject) => {
    setEditing({ type, entity })
    setName(entity?.name ?? '')
    setCode(entity && type !== 'department' ? (entity as Major | Subject).code : '')
    if (entity && type === 'major') setDepartmentId(String((entity as Major).department_id))
    else if (entity && type === 'subject') {
      const subject = entity as Subject
      setDepartmentId(String(subject.majors[0]?.department_id ?? ''))
      setMajorIds(subject.majors.map((major) => major.id))
    } else {
      setDepartmentId('')
      setMajorIds([])
    }
  }
  const currentType = editing?.type
  const editorMajors = editorMajorsQuery.data ?? []
  const isFormValid = Boolean(name.trim()) && (currentType === 'department' || (code.trim() && departmentId && (currentType === 'major' || majorIds.length > 0)))

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
        {currentType !== 'department' ? <label className="block text-sm font-medium text-slate-700">Khoa<select value={departmentId} onChange={(event) => { setDepartmentId(event.target.value); setMajorIds([]) }} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"><option value="">Chọn khoa</option>{departmentsQuery.data?.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label> : null}
        {currentType === 'subject' ? <label className="block text-sm font-medium text-slate-700">Ngành (chọn ít nhất một)<select multiple value={majorIds.map(String)} onChange={(event) => setMajorIds(Array.from(event.target.selectedOptions, (option) => Number(option.value)))} className="mt-1 h-28 w-full rounded-lg border border-slate-300 px-3 py-2" disabled={!departmentId || editorMajorsQuery.isLoading}>{editorMajors.map((major) => <option key={major.id} value={major.id}>{major.code} — {major.name}</option>)}</select></label> : null}
      </div>
      <div className="mt-5 flex justify-end gap-2"><button onClick={() => setEditing(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => saveMutation.mutate()} disabled={!isFormValid || saveMutation.isPending} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-60">{saveMutation.isPending ? <Spinner size="sm" className="border-slate-500 border-t-white" /> : null}Lưu</button></div>
    </Modal>
    <Modal isOpen={deleting !== null} title="Xác nhận xóa"><p className="text-sm text-slate-600">Xóa “{deleting?.entity?.name}”?</p><div className="mt-5 flex justify-end gap-2"><button onClick={() => setDeleting(null)} className="rounded-lg border px-3 py-2 text-sm">Hủy</button><button onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending} className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm text-white disabled:opacity-60">{deleteMutation.isPending ? <Spinner size="sm" className="border-red-300 border-t-white" /> : null}Xóa</button></div></Modal>
  </div>
}
