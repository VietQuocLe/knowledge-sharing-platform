import { useState } from 'react'
import { Check, Crown, Loader2, Sparkles, X, Zap } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { paymentsApi } from '../api'

interface PricingModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
}

export function PricingModal({
  isOpen,
  onClose,
  title = 'Nâng cấp Không giới hạn với Gói Pro',
  description = 'Mở khóa toàn bộ sức mạnh AI Workspace, tối ưu việc ôn thi và quản lý tri thức học tập.',
}: PricingModalProps) {
  const [isLoading, setIsLoading] = useState(false)

  if (!isOpen) return null

  const handleCheckout = async () => {
    setIsLoading(true)
    try {
      const response = await paymentsApi.createCheckout()
      if (response.payment_url) {
        toast.loading('Đang chuyển hướng sang cổng thanh toán VNPay Sandbox...', { duration: 2500 })
        window.location.href = response.payment_url
      } else {
        throw new Error('Không nhận được đường dẫn thanh toán từ máy chủ.')
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Không thể tạo đơn thanh toán. Vui lòng thử lại!'
      toast.error(msg)
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs font-sans animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200/80 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header Banner */}
        <div className="relative px-6 pt-7 pb-6 bg-gradient-to-br from-slate-900 via-slate-850 to-slate-900 text-white overflow-hidden">
          <div className="absolute -right-10 -top-10 w-40 h-40 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />
          <div className="absolute -left-10 -bottom-10 w-40 h-40 bg-teal-500/10 rounded-full blur-2xl pointer-events-none" />

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-400/15 border border-amber-400/30 text-amber-300 text-xs font-bold tracking-wide uppercase">
              <Crown className="h-3.5 w-3.5 text-amber-400" />
              Gói Hội Viên Pro
            </span>
          </div>
          <h2 className="text-xl md:text-2xl font-black text-white tracking-tight">{title}</h2>
          <p className="text-xs md:text-sm text-slate-300 mt-1.5 max-w-lg leading-relaxed">{description}</p>
        </div>

        {/* Pricing Cards Comparison */}
        <div className="p-6 md:p-8 space-y-6 overflow-y-auto max-h-[70vh]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Free Plan */}
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-800">Gói Miễn Phí</h3>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-200/80 text-slate-700">
                    Hiện tại
                  </span>
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-2xl font-extrabold text-slate-900">0đ</span>
                  <span className="text-xs text-slate-500 font-medium">/vĩnh viễn</span>
                </div>
                <ul className="mt-5 space-y-2.5 text-xs text-slate-600">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-slate-400 shrink-0" />
                    <span>Tối đa <strong>8 tài liệu nguồn</strong> / Notebook</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-slate-400 shrink-0" />
                    <span>Tối đa <strong>10 bài tập AI</strong> / Notebook</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-slate-400 shrink-0" />
                    <span>Tra cứu và chat AI cơ bản</span>
                  </li>
                </ul>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-200/60 text-center">
                <span className="text-xs font-semibold text-slate-400">Gói mặc định của hệ thống</span>
              </div>
            </div>

            {/* Pro Plan (Highlighted) */}
            <div className="rounded-2xl border-2 border-amber-400/80 bg-gradient-to-b from-amber-50/40 via-white to-white p-5 flex flex-col justify-between shadow-lg relative">
              <div className="absolute -top-3 right-4 px-3 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-black uppercase tracking-wider shadow-xs">
                Khuyên Dùng
              </div>
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-black text-slate-900 flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-amber-500" />
                    Gói Chuyên Nghiệp (Pro)
                  </h3>
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-black text-slate-900">49.000đ</span>
                  <span className="text-xs text-slate-500 font-semibold">/tháng</span>
                </div>
                <ul className="mt-5 space-y-2.5 text-xs text-slate-700 font-medium">
                  <li className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full bg-teal-100 flex items-center justify-center shrink-0">
                      <Check className="h-3 w-3 text-teal-700 stroke-[3]" />
                    </div>
                    <span>Tối đa <strong>20 tài liệu nguồn</strong> / Notebook (gấp 2.5 lần)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full bg-teal-100 flex items-center justify-center shrink-0">
                      <Check className="h-3 w-3 text-teal-700 stroke-[3]" />
                    </div>
                    <span>Tối đa <strong>20 bài tập AI</strong> / Notebook (gấp đôi)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                      <Crown className="h-3 w-3 text-amber-700 stroke-[3]" />
                    </div>
                    <span>Huy hiệu <strong>PRO Ánh Kim</strong> độc quyền cạnh hồ sơ</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                      <Zap className="h-3 w-3 text-amber-700 stroke-[3]" />
                    </div>
                    <span>Ưu tiên băng thông sinh bài tập AI tức thì</span>
                  </li>
                </ul>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleCheckout}
                  disabled={isLoading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 active:from-amber-700 active:to-amber-800 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Đang khởi tạo thanh toán...</span>
                    </>
                  ) : (
                    <>
                      <span>Nâng cấp ngay với VNPay (49K)</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Guarantee Note */}
          <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200/60 flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-teal-600/10 flex items-center justify-center shrink-0 text-teal-700 font-bold text-xs">
              NCB
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Kiểm thử an toàn qua <strong>Cổng VNPay Sandbox</strong> (Hỗ trợ thẻ ATM NCB Test miễn phí 100%, OTP: <code>123456</code>). Giao dịch được kích hoạt tự động tức thì.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

