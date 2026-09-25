// Axios 实例：baseURL 由 VITE_API_BASE 控制，统一解包 {code, message, data}
import axios from 'axios'
import type { ApiResponse } from './types'

// API 基址解析：
// - 开发环境：默认 http://localhost:8000（可用 VITE_API_BASE 覆盖）
// - 生产构建：默认相对基址 ''（与页面同源 —— 前端由后端一并托管，避免跨域与写死域名）
// - 生产环境忽略 localhost 基址（对访客浏览器而言 localhost 指向其本机，必然请求失败）
const ENV_BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.trim() || ''
const isLocalhostBase = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i.test(ENV_BASE)
const useEnvBase = ENV_BASE !== '' && !(import.meta.env.PROD && isLocalhostBase)
const baseURL = useEnvBase ? ENV_BASE : import.meta.env.DEV ? 'http://localhost:8000' : ''

export const http = axios.create({
  baseURL,
  timeout: 20000,
})

// 响应拦截：直接返回 data 字段；code !== 0 或 HTTP 错误时抛异常
http.interceptors.response.use(
  (resp) => {
    const body = resp.data as ApiResponse
    if (body && typeof body.code === 'number' && body.code !== 0) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return resp
  },
  (error) => {
    // 422 参数校验失败：后端会透传 Pydantic 内部细节（含枚举值），此处收敛为友好文案
    if (error?.response?.status === 422) {
      return Promise.reject(new Error('输入参数有误，请检查后重试'))
    }
    const detail = error?.response?.data?.message
    return Promise.reject(new Error(detail || error?.message || '网络异常'))
  },
)

/** 获取解包后的 data（配合响应拦截器） */
export async function unwrap<T>(p: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const resp = await p
  return resp.data.data as T
}

export default http
