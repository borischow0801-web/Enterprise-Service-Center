import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, clearAuth } from '@/utils/token'
import router from '@/router'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  traceId: string
}

// 留空时使用相对路径，Vite proxy 在服务端转发，外部 PC 也能正常访问
const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

const request = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor ───────────────────────────────────────────────────────
request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    if (import.meta.env.DEV) {
      console.debug(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data ?? config.params ?? '')
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor ──────────────────────────────────────────────────────
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const body = response.data
    if (import.meta.env.DEV) {
      console.debug(`[API] ← ${response.config.url}`, body)
    }
    if (body.code === 0) {
      // 把整个 ApiResponse 往下传，typed helpers 再取 .data
      return body as unknown as AxiosResponse
    }
    if (body.code === 40101) {
      clearAuth()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
      return Promise.reject(new Error(body.message))
    }
    ElMessage.error(body.message || '请求失败')
    return Promise.reject(new Error(body.message))
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error('[API] error', error)
    }
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      ElMessage.error('无法连接后端服务，请检查服务是否启动')
      return Promise.reject(error)
    }
    const status = error.response?.status
    if (status === 401) {
      clearAuth()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.error('权限不足')
    } else if (status === 404) {
      ElMessage.error(`接口不存在: ${error.config?.url}`)
    } else if (status === 422) {
      const detail = error.response?.data?.message || '请求参数错误'
      ElMessage.error(detail)
    } else if (status >= 500) {
      ElMessage.error('后端服务异常，请联系管理员')
    } else {
      ElMessage.error(error.response?.data?.message || error.message || '网络异常')
    }
    return Promise.reject(error)
  },
)

// ── Typed helpers ─────────────────────────────────────────────────────────────
export function get<T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig): Promise<T> {
  return request.get(url, { params, ...config }).then((r) => (r as unknown as ApiResponse<T>).data)
}

export function post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.post(url, data, config).then((r) => (r as unknown as ApiResponse<T>).data)
}

export function put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.put(url, data, config).then((r) => (r as unknown as ApiResponse<T>).data)
}

export function del<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.delete(url, config).then((r) => (r as unknown as ApiResponse<T>).data)
}

export function patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  return request.patch(url, data, config).then((r) => (r as unknown as ApiResponse<T>).data)
}

export default request
