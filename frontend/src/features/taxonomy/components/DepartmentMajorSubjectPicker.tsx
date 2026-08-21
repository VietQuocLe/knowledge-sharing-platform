import { Spinner } from '../../../components/ui/Spinner'
import { ErrorMessage } from '../../../components/ui/ErrorMessage'
import { useDepartments } from '../hooks/useDepartments'
import { useMajors } from '../hooks/useMajors'
import { useSubjects } from '../hooks/useSubjects'

interface DepartmentMajorSubjectPickerProps {
    departmentId: number | null
    majorId: number | null
    subjectId: number | null
    onChange: (values: {
        departmentId: number | null
        majorId: number | null
        subjectId: number | null
    }) => void
    showMajor?: boolean
    showSubject?: boolean
    departmentRequired?: boolean
    majorRequired?: boolean
    subjectRequired?: boolean
}

export function DepartmentMajorSubjectPicker({
    departmentId,
    majorId,
    subjectId,
    onChange,
    showMajor = true,
    showSubject = true,
    departmentRequired = false,
    majorRequired = false,
    subjectRequired = false,
}: DepartmentMajorSubjectPickerProps) {
    const departmentsQuery = useDepartments()
    const majorsQuery = useMajors(departmentId)
    const subjectsQuery = useSubjects(majorId)

    const handleDepartmentChange = (id: number | null) => {
        onChange({
            departmentId: id,
            majorId: null,
            subjectId: null,
        })
    }

    const handleMajorChange = (id: number | null) => {
        onChange({
            departmentId,
            majorId: id,
            subjectId: null,
        })
    }

    const handleSubjectChange = (id: number | null) => {
        onChange({
            departmentId,
            majorId,
            subjectId: id,
        })
    }

    return (
        <div className="space-y-4">
            {/* Department Select */}
            <div>
                <label className="block text-sm font-medium text-slate-700">
                    <span className="mb-1 block">Khoa {departmentRequired && <span className="text-red-500">*</span>}</span>
                    {departmentsQuery.isLoading ? (
                        <Spinner size="sm" />
                    ) : departmentsQuery.error ? (
                        <ErrorMessage message="Không thể tải danh sách khoa" />
                    ) : (
                        <select
                            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
                            value={departmentId ?? ''}
                            onChange={(e) => {
                                const val = e.target.value
                                handleDepartmentChange(val ? Number(val) : null)
                            }}
                        >
                            <option value="">Chọn khoa</option>
                            {departmentsQuery.data?.map((dept) => (
                                <option key={dept.id} value={dept.id}>
                                    {dept.name}
                                </option>
                            ))}
                        </select>
                    )}
                </label>
            </div>

            {/* Major Select */}
            {showMajor && (
                <div>
                    <label className="block text-sm font-medium text-slate-700">
                        <span className="mb-1 block">Ngành {majorRequired && <span className="text-red-500">*</span>}</span>
                        <select
                            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-900 disabled:bg-slate-100"
                            disabled={departmentId === null || majorsQuery.isLoading}
                            value={majorId ?? ''}
                            onChange={(e) => {
                                const val = e.target.value
                                handleMajorChange(val ? Number(val) : null)
                            }}
                        >
                            <option value="">
                                {majorsQuery.isLoading ? 'Đang tải ngành...' : 'Chọn ngành'}
                            </option>
                            {majorsQuery.data?.map((major) => (
                                <option key={major.id} value={major.id}>
                                    {major.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    {majorsQuery.error ? (
                        <span className="mt-1 block text-xs text-red-600">Không thể tải danh sách ngành</span>
                    ) : null}
                </div>
            )}

            {/* Subject Select */}
            {showMajor && showSubject && (
                <div>
                    <label className="block text-sm font-medium text-slate-700">
                        <span className="mb-1 block">Môn học {subjectRequired && <span className="text-red-500">*</span>}</span>
                        <select
                            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-900 disabled:bg-slate-100"
                            disabled={majorId === null || subjectsQuery.isLoading}
                            value={subjectId ?? ''}
                            onChange={(e) => {
                                const val = e.target.value
                                handleSubjectChange(val ? Number(val) : null)
                            }}
                        >
                            <option value="">
                                {subjectsQuery.isLoading ? 'Đang tải môn học...' : 'Chọn môn học'}
                            </option>
                            {subjectsQuery.data?.map((subj) => (
                                <option key={subj.id} value={subj.id}>
                                    {subj.code} — {subj.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    {subjectsQuery.error ? (
                        <span className="mt-1 block text-xs text-red-600">Không thể tải danh sách môn học</span>
                    ) : null}
                </div>
            )}
        </div>
    )
}
