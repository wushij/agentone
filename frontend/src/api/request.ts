import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { handleUnauthorized } from '@/utils/session'

declare module 'axios' {
  export interface AxiosRequestConfig {
    skipAuth?: boolean
    skipErrorHandler?: boolean
    skipUnauthorizedRedirect?: boolean
  }
}

export const TOKEN_STORAGE_KEY = 'agentone_access_token'
export const USER_STORAGE_KEY = 'agentone_user'

export interface ExtendedRequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean
  skipErrorHandler?: boolean
  skipUnauthorizedRedirect?: boolean
}

export interface ApiResult<T = unknown> {
  code: number
  message: string
  data: T
}

export interface ApiRequestError extends Error {
  apiCode?: number
  httpStatus?: number
  canceled?: boolean
}

function logApiIssue(level: 'error' | 'warn', message: string, detail?: unknown) {
  const logger = level === 'error' ? console.error : console.warn
  if (detail !== undefined) {
    logger(`[API] ${message}`, detail)
    return
  }
  logger(`[API] ${message}`)
}

export function createApiError(message: string, apiCode?: number, httpStatus?: number) {
  const error = new Error(message) as ApiRequestError
  error.apiCode = apiCode
  error.httpStatus = httpStatus
  return error
}

export function createAbortError() {
  const error = createApiError('已取消请求')
  error.name = 'CanceledError'
  error.canceled = true
  return error
}

export function resolveErrorStatus(error: unknown): number | undefined {
  if (!error || typeof error !== 'object') return undefined
  const err = error as ApiRequestError & AxiosError<ApiResult>
  if (typeof err.apiCode === 'number') return err.apiCode
  if (typeof err.httpStatus === 'number') return err.httpStatus
  if (typeof err.response?.status === 'number') return err.response.status
  if (typeof err.response?.data?.code === 'number') return err.response.data.code
  return undefined
}

export function isNetworkFailure(error: unknown) {
  if (!error || typeof error !== 'object') return false
  const err = error as AxiosError
  if (!err.response) return true
  return err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK'
}

export function isAbortError(error: unknown) {
  if (!error || typeof error !== 'object') return false
  const err = error as ApiRequestError & { code?: string }
  if (err.canceled) return true
  return err.name === 'CanceledError' || err.name === 'AbortError' || err.code === 'ERR_CANCELED'
}

export function resolveErrorMessage(error: unknown, fallback = '操作失败') {
  if (isAbortError(error)) return fallback
  if (error && typeof error === 'object' && 'message' in error) {
    const message = String((error as Error).message || '').trim()
    if (message && message !== '已取消请求') return message
  }
  return fallback
}

export function normalizeRequestError(error: AxiosError<ApiResult>): ApiRequestError {
  const apiCode = error.response?.data?.code
  const httpStatus = error.response?.status

  let message = error.response?.data?.message

  if (!message) {
    if (error.message === 'Network Error') {
      message = '网络连接失败，请检查您的网络连接或后端服务是否已启动'
    } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      message = '请求超时，请稍后重试'
    } else if (httpStatus) {
      switch (httpStatus) {
        case 400:
          message = '请求参数错误 (400)'
          break
        case 401:
          message = '登录状态已失效，请重新登录 (401)'
          break
        case 403:
          message = '您暂无权限进行此操作 (403)'
          break
        case 404:
          message = '请求的资源或接口不存在 (404)'
          break
        case 405:
          message = '请求方法不允许 (405)'
          break
        case 500:
          message = '服务器内部错误，请联系管理员 (500)'
          break
        case 502:
        case 503:
        case 504:
          message = '网络网关异常或服务器正在维护，请稍后重试 (502/503/504)'
          break
        default:
          message = `服务器响应异常 (HTTP ${httpStatus})`
      }
    } else {
      message = error.message || '未知网络异常，请重试'
    }
  }

  return createApiError(message, apiCode, httpStatus)
}

function isUnauthorizedStatus(status?: number) {
  return status === 401
}

type RefreshQueueItem = {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

let isRefreshing = false
let requestsQueue: RefreshQueueItem[] = []

function subscribeTokenRefresh(resolve: (token: string) => void, reject: (error: unknown) => void) {
  requestsQueue.push({ resolve, reject })
}

function onRefreshed(token: string) {
  requestsQueue.forEach(({ resolve }) => resolve(token))
  requestsQueue = []
}

function onRefreshFailed(error: unknown) {
  requestsQueue.forEach(({ reject }) => reject(error))
  requestsQueue = []
  isRefreshing = false
}

function delay(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms)
  })
}

async function refreshAccessToken(): Promise<string> {
  const res = await request.post('/auth/refresh', {}, {
    skipAuth: false,
    skipErrorHandler: true,
    skipUnauthorizedRedirect: true
  })
  const data = res.data as { token?: string; accessToken?: string }
  const newToken = data?.token || data?.accessToken || ''
  if (!newToken) {
    throw createApiError('Token 刷新失败')
  }

  localStorage.setItem(TOKEN_STORAGE_KEY, newToken)
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()
  userStore.token = newToken
  userStore.scheduleTokenRefresh()
  return newToken
}

async function refreshAccessTokenWithRetry(maxAttempts = 3): Promise<string> {
  let lastError: unknown
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return await refreshAccessToken()
    } catch (error) {
      lastError = error
      if (isUnauthorizedStatus(resolveErrorStatus(error))) {
        throw error
      }
      if (isNetworkFailure(error) && attempt < maxAttempts) {
        await delay(1000)
        continue
      }
      throw error
    }
  }
  throw lastError
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000
})

request.interceptors.request.use((config) => {
  const nextConfig = config as ExtendedRequestConfig
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)

  if (token && !nextConfig.skipAuth) {
    config.headers = (config.headers ?? {}) as typeof config.headers
    ;(config.headers as Record<string, string>).Authorization = `Bearer ${token}`
  }

  return config
})

request.interceptors.response.use(
  (response) => {
    const cfg = response.config as ExtendedRequestConfig
    const body = response.data as ApiResult | unknown
    if (body && typeof body === 'object' && 'code' in body) {
      const result = body as ApiResult
      if (result.code !== 200) {
        if (isUnauthorizedStatus(result.code) && !cfg.skipUnauthorizedRedirect) {
          logApiIssue('warn', `未授权 (${result.code}): ${result.message}`)
        } else if (cfg.skipErrorHandler) {
          logApiIssue('warn', `请求失败 (${result.code}): ${result.message}`)
        } else {
          logApiIssue('error', `请求失败 (${result.code}): ${result.message}`)
        }
        return Promise.reject(createApiError(result.message || '请求失败', result.code, response.status))
      }
      if ('data' in result) {
        response.data = result.data
      }
    }
    if (typeof body === 'string' && body.trimStart().startsWith('<')) {
      return Promise.reject(createApiError('服务返回异常页面，请确认后端已启动', undefined, response.status))
    }
    return response
  },
  async (error: AxiosError<ApiResult>) => {
    const cfg = error.config as ExtendedRequestConfig | undefined

    if (isAbortError(error)) {
      return Promise.reject(createAbortError())
    }

    const normalized = normalizeRequestError(error)
    const status = resolveErrorStatus(normalized)

    if (isUnauthorizedStatus(status) && cfg && !cfg.skipUnauthorizedRedirect) {
      if (cfg.url === '/auth/refresh') {
        onRefreshFailed(normalized)
        logApiIssue('warn', '刷新 Token 接口返回 401，清理登录状态')
        void handleUnauthorized()
        return Promise.reject(normalized)
      }

      if (!isRefreshing) {
        isRefreshing = true
        void refreshAccessTokenWithRetry()
          .then((newToken) => {
            isRefreshing = false
            onRefreshed(newToken)
          })
          .catch((refreshError) => {
            onRefreshFailed(refreshError)
            if (isUnauthorizedStatus(resolveErrorStatus(refreshError))) {
              void handleUnauthorized()
            }
          })
      }

      return new Promise((resolve, reject) => {
        subscribeTokenRefresh(
          (token) => {
            if (cfg.headers) {
              cfg.headers.Authorization = `Bearer ${token}`
            }
            resolve(request(cfg))
          },
          (refreshError) => reject(refreshError)
        )
      })
    } else if (isNetworkFailure(error) && !cfg?.skipErrorHandler) {
      logApiIssue('warn', normalized.message, error)
    } else if (!cfg?.skipErrorHandler) {
      logApiIssue('error', normalized.message, error)
      ElMessage.error(normalized.message)
    } else {
      logApiIssue('warn', normalized.message, error)
    }

    return Promise.reject(normalized)
  }
)

export default request
