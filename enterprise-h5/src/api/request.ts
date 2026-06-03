import axios, { type AxiosRequestConfig } from 'axios'
import { showToast } from 'vant'
import { getToken, clearAuth } from '@/utils/token'
import router from '@/router'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  traceId: string
}

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

const request = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

function redirectToLogin() {
  if (router.currentRoute.value.path === '/login') return
  router.push('/login')
}

request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  const fullUrl = `${config.baseURL ?? ''}${config.url ?? ''}`
  if (import.meta.env.DEV) {
    console.debug(`[H5] ${config.method?.toUpperCase()} ${fullUrl}`, config.data ?? config.params ?? '')
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    if (import.meta.env.DEV) console.debug('[H5] ←', response.config.url, body)
    if (body.code === 0) return body as unknown as typeof response
    if (body.code === 40101) {
      clearAuth()
      redirectToLogin()
      showToast('登录已过期，请重新登录')
      return Promise.reject(new Error(body.message))
    }
    showToast(body.message || '请求失败')
    return Promise.reject(new Error(body.message))
  },
  (error) => {
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      showToast('后端服务不可用或接口地址错误')
    } else if (error.response?.status === 401) {
      clearAuth()
      redirectToLogin()
      showToast('登录已过期')
    } else {
      showToast(error.response?.data?.message || error.message || '网络异常')
    }
    return Promise.reject(error)
  }
)

export function get<T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig): Promise<T> {
  return request.get(url, { params, ...config }).then(r => (r as unknown as ApiResponse<T>).data)
}
export function post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.post(url, data, config).then(r => (r as unknown as ApiResponse<T>).data)
}
export default request
