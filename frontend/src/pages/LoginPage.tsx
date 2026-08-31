import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { GraduationCap, Eye, EyeOff, Loader2 } from "lucide-react"
import { GoogleLogin } from "@react-oauth/google"
import toast from "react-hot-toast"
import { useAuth } from "../features/auth/context/AuthContext"

export function LoginPage() {
  const navigate = useNavigate()
  const { login, loginWithGoogle } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await login(email, password)
      navigate("/", { replace: true })
    } catch {
      toast.error("Email hoặc mật khẩu không chính xác.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
    if (!credentialResponse.credential) return
    setIsLoading(true)
    try {
      await loginWithGoogle(credentialResponse.credential)
      navigate("/", { replace: true })
    } catch {
      toast.error("Đăng nhập Google thất bại. Vui lòng thử lại.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "linear-gradient(135deg, #f0f7ff 0%, #faf9f6 50%, #f0fdf4 100%)" }}>
      {/* Header */}
      <header className="px-8 py-5 flex items-center justify-between">
        <Link to="/" className="inline-flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-sky-600 text-white shadow-md shadow-sky-200">
            <GraduationCap className="h-5 w-5" />
          </div>
          <span className="text-base font-bold tracking-tight text-slate-900">HCMC-VAULT</span>
        </Link>
      </header>

      {/* Content */}
      <div className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-sm">

          {/* Title */}
          <div className="text-center mb-7">
            <h1 className="text-2xl font-bold text-slate-900">Chào mừng trở lại</h1>
            <p className="text-sm text-slate-500 mt-1.5">Đăng nhập để tiếp tục khám phá tài liệu</p>
          </div>

          {/* Card */}
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl shadow-slate-200/60 border border-white/60 p-7">
            {/* Google Login */}
            <div className="flex justify-center mb-5">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => toast.error("Đăng nhập Google thất bại.")}
                text="signin_with"
                shape="pill"
                theme="outline"
                size="large"
                width="320"
              />
            </div>

            {/* Divider */}
            <div className="relative mb-5">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-100" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-3 text-[11px] text-slate-400 font-medium uppercase tracking-wider">hoặc đăng nhập bằng email</span>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="johndoe@email.com"
                  required
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:border-transparent transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">Mật khẩu</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 pr-11 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:border-transparent transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Remember me + Forgot */}
              <div className="flex items-center justify-between pt-0.5">
                <label className="flex items-center gap-2 text-sm text-slate-500 cursor-pointer select-none">
                  <input type="checkbox" className="rounded-md border-slate-300 text-sky-600 focus:ring-sky-400 cursor-pointer" />
                  Ghi nhớ đăng nhập
                </label>
                {/* <span className="text-xs text-slate-400 cursor-not-allowed select-none">Quên mật khẩu?</span> */}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-2xl bg-black py-3 text-sm font-semibold text-white hover:bg-slate-800 active:scale-[0.98] disabled:opacity-60 transition-all duration-150 shadow-md shadow-slate-200 cursor-pointer mt-1 flex items-center justify-center gap-2"
              >
                {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                {isLoading ? "Đang đăng nhập..." : "Đăng nhập"}
              </button>
            </form>
          </div>

          {/* Footer */}
          <p className="mt-5 text-center text-sm text-slate-500">
            Chưa có tài khoản?{" "}
            <Link to="/register" className="font-semibold text-sky-600 hover:text-sky-700 transition">
              Tạo tài khoản
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
