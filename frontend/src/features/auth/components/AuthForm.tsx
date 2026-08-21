import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useLocation, useNavigate } from 'react-router-dom'
import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
import { useAuth } from '../context/AuthContext'
import { getApiErrorMessage } from '../../../api/getApiErrorMessage'

type AuthFormValues = {
  email: string
  password: string
  full_name?: string
}

type AuthFormProps = {
  mode?: 'login' | 'register'
}

export function AuthForm({ mode = 'login' }: AuthFormProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, register: registerUser } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<AuthFormValues>({
    mode: 'onBlur',
  })

  const onSubmit = async (values: AuthFormValues) => {
    setIsSubmitting(true)
    setError(null)

    try {
      if (mode === 'register') {
        await registerUser(values.email, values.full_name ?? '', values.password)
      } else {
        await login(values.email, values.password)
      }

      const redirectTo = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(redirectTo && redirectTo !== '/login' ? redirectTo : '/')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Có lỗi xảy ra. Vui lòng thử lại.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h2 className="mb-4 text-xl font-semibold text-slate-900">
        {mode === 'register' ? 'Đăng ký' : 'Đăng nhập'}
      </h2>

      {error ? <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div> : null}

      <div className="space-y-4">
        {mode === 'register' ? (
          <Input
            label="Họ và tên"
            placeholder="Nguyễn Văn A"
            {...register('full_name', { required: 'Vui lòng nhập họ tên' })}
            error={errors.full_name?.message}
          />
        ) : null}

        <Input
          label="Email"
          placeholder="name@example.com"
          type="email"
          {...register('email', {
            required: 'Vui lòng nhập email',
            pattern: {
              value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
              message: 'Email không hợp lệ',
            },
          })}
          error={errors.email?.message}
        />

        <Input
          label="Mật khẩu"
          placeholder="••••••••"
          type="password"
          {...register('password', {
            required: 'Vui lòng nhập mật khẩu',
            minLength: {
              value: 8,
              message: 'Mật khẩu tối thiểu 8 ký tự',
            },
          })}
          error={errors.password?.message}
        />

        <Button className="w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Đang xử lý...' : mode === 'register' ? 'Đăng ký' : 'Đăng nhập'}
        </Button>
      </div>
    </form>
  )
}
