import { AuthForm } from '../features/auth/components/AuthForm'

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <AuthForm mode="login" />
    </div>
  )
}
