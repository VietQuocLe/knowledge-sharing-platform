import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorMessage } from '../../../components/ui/ErrorMessage'
import { Spinner } from '../../../components/ui/Spinner'
import { taxonomyApi } from '../api'
import { taxonomyKeys } from '../queryKeys'

export function TaxonomyView() {
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | null>(null)
  const [selectedMajorId, setSelectedMajorId] = useState<number | null>(null)

  const {
    data: departments,
    isLoading: isLoadingDepts,
    error: errorDepts,
  } = useQuery({
    queryKey: taxonomyKeys.departmentsList(),
    queryFn: () => taxonomyApi.getDepartments(),
  })

  const {
    data: majors,
    isLoading: isLoadingMajors,
    error: errorMajors,
  } = useQuery({
    queryKey: taxonomyKeys.majorsList(selectedDepartmentId ?? undefined),
    queryFn: () => taxonomyApi.getMajorsByDepartment(selectedDepartmentId!),
    enabled: selectedDepartmentId !== null,
  })

  const {
    data: subjects,
    isLoading: isLoadingSubjects,
    error: errorSubjects,
  } = useQuery({
    queryKey: taxonomyKeys.subjectsList(selectedMajorId ?? undefined),
    queryFn: () => taxonomyApi.getSubjectsByMajor(selectedMajorId!),
    enabled: selectedMajorId !== null,
  })

  return (
    <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Duyệt theo phân loại</h2>

      {/* Departments */}
      <div>
        <h3 className="mb-3 text-sm font-medium text-slate-700">Chọn Khoa</h3>
        {isLoadingDepts ? (
          <div className="flex justify-center py-4">
            <Spinner size="sm" />
          </div>
        ) : errorDepts ? (
          <ErrorMessage message="Không thể tải danh sách khoa" />
        ) : (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {departments?.map((dept) => (
              <button
                key={dept.id}
                onClick={() => {
                  setSelectedDepartmentId(dept.id)
                  setSelectedMajorId(null)
                }}
                className={`rounded-lg border px-3 py-2 text-sm transition ${
                  selectedDepartmentId === dept.id
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-300 bg-white text-slate-900 hover:border-slate-500'
                }`.trim()}
              >
                {dept.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Majors */}
      {selectedDepartmentId && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-slate-700">Chọn Ngành</h3>
          {isLoadingMajors ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : errorMajors ? (
            <ErrorMessage message="Không thể tải danh sách ngành" />
          ) : majors && majors.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {majors.map((major) => (
                <button
                  key={major.id}
                  onClick={() => setSelectedMajorId(major.id)}
                  className={`rounded-lg border px-3 py-2 text-sm transition ${
                    selectedMajorId === major.id
                      ? 'border-slate-900 bg-slate-900 text-white'
                      : 'border-slate-300 bg-white text-slate-900 hover:border-slate-500'
                  }`.trim()}
                >
                  {major.name}
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Không có ngành nào</p>
          )}
        </div>
      )}

      {/* Subjects */}
      {selectedMajorId && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-slate-700">Danh sách Môn học</h3>
          {isLoadingSubjects ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : errorSubjects ? (
            <ErrorMessage message="Không thể tải danh sách môn học" />
          ) : subjects && subjects.length > 0 ? (
            <div className="space-y-2">
              {subjects.map((subject) => (
                <Link
                  key={subject.id}
                  to={`/subjects/${subject.id}`}
                  className="block rounded-lg border border-slate-200 p-3 transition hover:border-slate-900 hover:bg-slate-50"
                >
                  <div className="text-sm font-medium text-slate-900">{subject.name}</div>
                  <div className="text-xs text-slate-500">{subject.code}</div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Không có môn học nào</p>
          )}
        </div>
      )}
    </div>
  )
}
