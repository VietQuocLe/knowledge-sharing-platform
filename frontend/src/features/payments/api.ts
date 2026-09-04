import { createJsonRequest } from '../../api/apiClient'

export type CheckoutCreateResponse = {
  order_code: string
  payment_url: string
  amount: number
}

export type OrderStatusResponse = {
  order_code: string
  status: 'PENDING' | 'SUCCESS' | 'CANCELLED'
  amount: number
  plan_type: string
  paid_at: string | null
  tier: 'FREE' | 'PRO' | null
  pro_expires_at: string | null
}

export const paymentsApi = {
  createCheckout: async (): Promise<CheckoutCreateResponse> => {
    return createJsonRequest<CheckoutCreateResponse>({
      method: 'POST',
      url: '/payments/create-checkout',
    })
  },

  confirmVnpayReturn: async (params: Record<string, string>): Promise<OrderStatusResponse> => {
    return createJsonRequest<OrderStatusResponse>({
      method: 'GET',
      url: '/payments/vnpay-return',
      params,
    })
  },

  getOrderStatus: async (orderCode: string): Promise<OrderStatusResponse> => {
    return createJsonRequest<OrderStatusResponse>({
      method: 'GET',
      url: `/payments/orders/${orderCode}/status`,
    })
  },
}

