import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DepartmentMajorSubjectPicker } from './DepartmentMajorSubjectPicker'

export function TaxonomyView() {
  const navigate = useNavigate()
  const [departmentId, setDepartmentId] = useState<number | null>(null)
  const [majorId, setMajorId] = useState<number | null>(null)
  const [subjectId, setSubjectId] = useState<number | null>(null)

  const handleChange = (values: {
    departmentId: number | null
    majorId: number | null
    subjectId: number | null
  }) => {
    setDepartmentId(values.departmentId)
    setMajorId(values.majorId)
    setSubjectId(values.subjectId)

    if (values.subjectId) {
      navigate(`/subjects/${values.subjectId}`)
    }
  }

  return (
    <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Duyệt theo phân loại</h2>
      <DepartmentMajorSubjectPicker
        departmentId={departmentId}
        majorId={majorId}
        subjectId={subjectId}
        onChange={handleChange}
      />
    </div>
  )
}
