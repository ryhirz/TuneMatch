// Axios 实例：baseURL 由 VITE_API_BASE 控制，统一解包 {code, message, data}
import axios from 'axios'
import type { ApiResponse } from './types'

const baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

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
