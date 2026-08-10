import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'

export function AuthForm() {
  return (
    <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-slate-900">Đăng nhập</h2>
      <div className="space-y-4">
        <Input label="Email" placeholder="name@example.com" type="email" />
        <Input label="Mật khẩu" placeholder="••••••••" type="password" />
        <Button className="w-full">Đăng nhập</Button>
      </div>
    </div>
  )
}
