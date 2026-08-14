import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { getApiErrorMessage } from '../api/getApiErrorMessage'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Spinner } from '../components/ui/Spinner'
import { ResourceType, resourcesApi, type ResourceType as ResourceTypeValue } from '../features/resources/api'
import { resourcesKeys } from '../features/resources/queryKeys'
import { taxonomyApi } from '../features/taxonomy/api'
import { taxonomyKeys } from '../features/taxonomy/queryKeys'

type ResourceCreateFormValues = {
  title: string
  description: string
  subjectId: string
  resourceType: ResourceTypeValue
}

export function ResourceCreatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [departmentId, setDepartmentId] = useState<number | null>(null)
  const [majorId, setMajorId] = useState<number | null>(null)
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ResourceCreateFormValues>({
    defaultValues: { resourceType: ResourceType.DOCUMENT },
  })

  const departmentsQuery = useQuery({
    queryKey: taxonomyKeys.departmentsList(),
    queryFn: taxonomyApi.getDepartments,
  })
  const majorsQuery = useQuery({
    queryKey: taxonomyKeys.majorsList(departmentId ?? undefined),
    queryFn: () => taxonomyApi.getMajorsByDepartment(departmentId!),
    enabled: departmentId !== null,
  })
  const subjectsQuery = useQuery({
    queryKey: taxonomyKeys.subjectsList(majorId ?? undefined),
    queryFn: () => taxonomyApi.getSubjectsByMajor(majorId!),
    enabled: majorId !== null,
  })

  const createMutation = useMutation({
    mutationFn: resourcesApi.createResource,
    onSuccess: async (resource) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: resourcesKeys.me() }),
        queryClient.invalidateQueries({ queryKey: resourcesKeys.myDetailById(resource.id) }),
      ])
      toast.success('Đã tạo tài nguyên. Hãy đính kèm tài liệu để gửi duyệt.')
      navigate(`/resources/${resource.id}/upload`)
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Không thể tạo tài nguyên. Vui lòng thử lại.')),
  })

  const onSubmit = (values: ResourceCreateFormValues) => {
    createMutation.mutate({
      title: values.title.trim(),
      description: values.description.trim() || undefined,
      subject_id: Number(values.subjectId),
      resource_type: values.resourceType,
    })
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Tạo tài nguyên mới</h1>
      <p className="mt-2 text-sm text-slate-600">Bước 1/2: nhập thông tin và chọn môn học cho tài liệu.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 max-w-2xl space-y-5">
        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Tiêu đề</span>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
            placeholder="Ví dụ: Bài giảng lập trình Python"
            {...register('title', { required: 'Vui lòng nhập tiêu đề' })}
          />
          {errors.title ? <span className="mt-1 block text-xs text-red-600">{errors.title.message}</span> : null}
        </label>

        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Mô tả</span>
          <textarea
            className="min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
            placeholder="Mô tả ngắn về tài liệu (không bắt buộc)"
            {...register('description')}
          />
        </label>

        {departmentsQuery.isLoading ? (
          <Spinner size="sm" />
        ) : departmentsQuery.error ? (
          <ErrorMessage message="Không thể tải danh sách khoa" />
        ) : (
          <label className="block text-sm font-medium text-slate-700">
            <span className="mb-1 block">Khoa</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              defaultValue=""
              onChange={(event) => {
                const value = event.target.value
                setDepartmentId(value ? Number(value) : null)
                setMajorId(null)
                setValue('subjectId', '')
              }}
            >
              <option value="">Chọn khoa</option>
              {departmentsQuery.data?.map((department) => (
                <option key={department.id} value={department.id}>{department.name}</option>
              ))}
            </select>
          </label>
        )}

        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Ngành</span>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
            disabled={departmentId === null || majorsQuery.isLoading}
            defaultValue=""
            onChange={(event) => {
              const value = event.target.value
              setMajorId(value ? Number(value) : null)
              setValue('subjectId', '')
            }}
          >
            <option value="">{majorsQuery.isLoading ? 'Đang tải ngành...' : 'Chọn ngành'}</option>
            {majorsQuery.data?.map((major) => (
              <option key={major.id} value={major.id}>{major.name}</option>
            ))}
          </select>
          {majorsQuery.error ? <span className="mt-1 block text-xs text-red-600">Không thể tải danh sách ngành</span> : null}
        </label>

        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Môn học</span>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 disabled:bg-slate-100"
            disabled={majorId === null || subjectsQuery.isLoading}
            defaultValue=""
            {...register('subjectId', { required: 'Vui lòng chọn môn học' })}
          >
            <option value="">{subjectsQuery.isLoading ? 'Đang tải môn học...' : 'Chọn môn học'}</option>
            {subjectsQuery.data?.map((subject) => (
              <option key={subject.id} value={subject.id}>{subject.code} — {subject.name}</option>
            ))}
          </select>
          {errors.subjectId ? <span className="mt-1 block text-xs text-red-600">{errors.subjectId.message}</span> : null}
          {subjectsQuery.error ? <span className="mt-1 block text-xs text-red-600">Không thể tải danh sách môn học</span> : null}
        </label>

        <label className="block text-sm font-medium text-slate-700">
          <span className="mb-1 block">Loại tài nguyên</span>
          <select className="w-full rounded-lg border border-slate-300 px-3 py-2" {...register('resourceType')}>
            {Object.values(ResourceType).map((resourceType) => (
              <option key={resourceType} value={resourceType}>{resourceType}</option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={createMutation.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {createMutation.isPending ? <Spinner size="sm" className="border-slate-500 border-t-white" /> : null}
          {createMutation.isPending ? 'Đang tạo...' : 'Tạo và tiếp tục'}
        </button>
      </form>
    </div>
  )
}
