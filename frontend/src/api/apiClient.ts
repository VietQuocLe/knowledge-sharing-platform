import axios, { AxiosHeaders, type AxiosRequestConfig } from 'axios'
import { getStoredToken, clearStoredToken } from '../features/auth/tokenStorage'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  timeout: 30000,
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  const headers = new AxiosHeaders(config.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  config.headers = headers
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredToken()
      window.location.assign('/login')
    }

    return Promise.reject(error)
  },
)

export function createJsonRequest<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  const headers = new AxiosHeaders(config.headers)
  headers.set('Content-Type', 'application/json')

  return apiClient.request<T>({
    ...config,
    headers,
  }).then((response) => response.data)
}

export function createFormRequest<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  const headers = new AxiosHeaders(config.headers)
  headers.set('Content-Type', 'application/x-www-form-urlencoded')

  return apiClient.request<T>({
    ...config,
    headers,
  }).then((response) => response.data)
}

export function createMultipartRequest<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  const headers = new AxiosHeaders(config.headers)
  headers.delete('Content-Type')

  return apiClient.request<T>({
    ...config,
    headers,
  }).then((response) => response.data)
}

export default apiClient
