import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, XCircle, ArrowRight, Home, RefreshCw, Crown, Calendar, Hash } from 'lucide-react'
import { paymentsApi, type OrderStatusResponse, PricingModal } from '../features/payments'
import { useAuth } from '../features/auth/context/AuthContext'

export function PaymentReturnPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()

  const [isLoading, setIsLoading] = useState(true)
  const [orderStatus, setOrderStatus] = useState<OrderStatusResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isPricingModalOpen, setIsPricingModalOpen] = useState(false)

  useEffect(() => {
    const verifyPayment = async () => {
      setIsLoading(true)
      const params = Object.fromEntries(searchParams.entries())
      const orderCode = params['vnp_TxnRef']

      if (!orderCode) {
        setErrorMessage('Không tìm thấy thông tin đơn hàng trong liên kết trả về.')
        setIsLoading(false)
        return
      }

      try {
        // 1. Call confirmVnpayReturn API
        const result = await paymentsApi.confirmVnpayReturn(params)
        setOrderStatus(result)

        // 2. On success, immediately sync updated user tier to AuthContext
        if (result.status === 'SUCCESS') {
          await refreshUser()
        }
      } catch (err: any) {
        // Fallback: query order status from DB if return API verification fails
        try {
          const fallbackStatus = await paymentsApi.getOrderStatus(orderCode)
          setOrderStatus(fallbackStatus)
          if (fallbackStatus.status === 'SUCCESS') {
            await refreshUser()
          }
        } catch (fallbackErr: any) {
          const detail = err.response?.data?.detail || err.message || 'Không thể xác thực giao dịch thanh toán.'
          setErrorMessage(detail)
        }
      } finally {
        setIsLoading(false)
      }
    }

    void verifyPayment()
  }, [searchParams])

  const isSuccess = orderStatus?.status === 'SUCCESS'

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '30 ngày kể từ hôm nay'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4 md:p-6 font-sans">
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden text-center">
        {isLoading ? (
          <div className="py-16 px-6 space-y-4">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-teal-50 text-teal-600 animate-pulse">
              <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">Đang xác thực giao dịch VNPay...</h2>
            <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
              Vui lòng giữ nguyên màn hình trong giây lát để hệ thống hoàn tất kích hoạt gói Pro của bạn.
            </p>
          </div>
        ) : isSuccess ? (
          <div>
            {/* Header Success */}
            <div className="bg-gradient-to-b from-emerald-500 to-teal-600 p-8 text-white relative overflow-hidden">
              <div className="absolute -right-6 -top-6 w-28 h-28 bg-white/10 rounded-full blur-xl pointer-events-none" />
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-white/20 backdrop-blur-xs mb-3 shadow-inner">
                <CheckCircle2 className="h-10 w-10 text-white" />
              </div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 text-white text-xs font-bold uppercase tracking-wider mb-2">
                <Crown className="h-3.5 w-3.5 text-amber-300" />
                Hội Viên Pro
              </div>
              <h1 className="text-2xl font-black tracking-tight">Thanh Toán Thành Công!</h1>
              <p className="text-xs text-emerald-100 mt-1 max-w-sm mx-auto">
                Chúc mừng bạn đã nâng cấp gói Pro. Toàn bộ hạn mức 20 nguồn và 20 bài tập AI đã sẵn sàng!
              </p>
            </div>

            {/* Order Details Receipt */}
            <div className="p-6 md:p-8 space-y-4 text-left">
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/60 space-y-2.5 text-xs text-slate-600">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <span className="flex items-center gap-1.5 text-slate-500 font-medium">
                    <Hash className="h-3.5 w-3.5" />
                    Mã đơn hàng:
                  </span>
                  <span className="font-mono font-bold text-slate-800">{orderStatus.order_code}</span>
                </div>

                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Gói dịch vụ:</span>
                  <span className="font-bold text-teal-700">Pro Subscription (1 Tháng)</span>
                </div>

                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Số tiền thanh toán:</span>
                  <span className="font-bold text-slate-900">49.000đ</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-500 font-medium">
                    <Calendar className="h-3.5 w-3.5" />
                    Hạn sử dụng đến:
                  </span>
                  <span className="font-bold text-amber-700">{formatDate(orderStatus.pro_expires_at)}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  onClick={() => navigate('/me/workspace')}
                  className="flex-1 py-3 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 active:bg-black text-white font-bold text-xs shadow-md transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Khám phá Workspace</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
                <Link
                  to="/"
                  className="py-3 px-4 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs transition flex items-center justify-center gap-2"
                >
                  <Home className="h-4 w-4 text-slate-400" />
                  <span>Trang chủ</span>
                </Link>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {/* Header Failed / Cancelled */}
            <div className="bg-gradient-to-b from-rose-500 to-rose-600 p-8 text-white relative overflow-hidden">
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-white/20 backdrop-blur-xs mb-3 shadow-inner">
                <XCircle className="h-10 w-10 text-white" />
              </div>
              <h1 className="text-2xl font-black tracking-tight">Thanh Toán Chưa Hoàn Tất</h1>
              <p className="text-xs text-rose-100 mt-1 max-w-sm mx-auto">
                {errorMessage ||
                  'Giao dịch đã bị hủy theo yêu cầu hoặc gặp sự cố trên cổng VNPay. Tài khoản của bạn chưa bị trừ phí.'}
              </p>
            </div>

            {/* Error Content & Actions */}
            <div className="p-6 md:p-8 space-y-5">
              <div className="bg-amber-50 rounded-2xl p-4 border border-amber-200/80 text-left text-xs text-amber-800 leading-relaxed">
                <strong>Bạn muốn thử lại?</strong> Quá trình thanh toán trên VNPay Sandbox hoàn toàn miễn phí khi sử dụng thẻ NCB Test. Hạn mức của bạn hiện vẫn là gói Miễn phí.
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  onClick={() => setIsPricingModalOpen(true)}
                  className="flex-1 py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-md transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Crown className="h-4 w-4 text-amber-200" />
                  <span>Thử thanh toán lại</span>
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/me/workspace')}
                  className="py-3 px-4 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs transition"
                >
                  Về Workspace
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <PricingModal isOpen={isPricingModalOpen} onClose={() => setIsPricingModalOpen(false)} />
    </div>
  )
}
