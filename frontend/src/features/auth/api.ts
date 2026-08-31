import { createFormRequest, createJsonRequest } from '../../api/apiClient'

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = {
  email: string
  full_name: string
  password: string
}

export type GoogleLoginPayload = {
  credential: string
}

export type AuthUser = {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

export const authApi = {
  login: async (payload: LoginPayload) => {
    const params = new URLSearchParams()
    params.append('username', payload.email)
    params.append('password', payload.password)

    return createFormRequest<AuthResponse>({
      method: 'POST',
      url: '/auth/login',
      data: params,
    })
  },
  register: async (payload: RegisterPayload) => {
    return createJsonRequest<AuthResponse>({
      method: 'POST',
      url: '/auth/register',
      data: payload,
    })
  },
  googleLogin: async (payload: GoogleLoginPayload) => {
    return createJsonRequest<AuthResponse>({
      method: 'POST',
      url: '/auth/google',
      data: payload,
    })
  },
  me: async () => {
    return createJsonRequest<AuthUser>({
      method: 'GET',
      url: '/auth/me',
    })
  },
}
