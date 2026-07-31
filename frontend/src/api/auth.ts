import request, { REFRESH_TOKEN_STORAGE_KEY, type ExtendedRequestConfig } from './request'
import type { CaptchaState, LoginPayload, LoginResponse, UserProfile } from '@/types'

const publicConfig: ExtendedRequestConfig = {
  skipAuth: true,
  skipErrorHandler: true
}

interface AuthPayload {
  token: string
  refreshToken?: string
  id: number
  username: string
  nickname?: string
  avatar?: string
  role: UserProfile['role']
  permissions?: string[]
  fullAccess?: boolean
}

function toUserProfile(data: AuthPayload): UserProfile {
  return {
    id: data.id,
    username: data.username,
    nickname: data.nickname,
    avatar: data.avatar,
    role: data.role,
    permissions: data.permissions ?? [],
    fullAccess: Boolean(data.fullAccess)
  }
}

function toLoginResponse(data: AuthPayload): LoginResponse {
  return {
    token: data.token,
    refreshToken: data.refreshToken,
    user: toUserProfile(data)
  }
}

export function login(payload: LoginPayload) {
  return request
    .post<AuthPayload>('/auth/login', payload, publicConfig)
    .then((res) => toLoginResponse(res.data))
}

export function getCaptchaRequired() {
  return request
    .get<{ required: boolean }>('/auth/captcha/required', publicConfig)
    .then((res) => res.data)
}

export function getCaptcha() {
  return request
    .get<CaptchaState>(`/auth/captcha?_=${Date.now()}`, publicConfig)
    .then((res) => res.data)
}

export function getCurrentUser() {
  return request
    .get<AuthPayload>('/auth/info', {
      timeout: 8000,
      skipErrorHandler: true,
      skipUnauthorizedRedirect: true
    } as ExtendedRequestConfig)
    .then((res) => toUserProfile(res.data))
}

export function logout() {
  return request.post<void>('/auth/logout').then((res) => res.data)
}

export function updateUserProfile(payload: { nickname: string; avatar?: string }) {
  return request.put<AuthPayload>('/auth/profile', payload).then((res) => toUserProfile(res.data))
}

export function changePassword(payload: { oldPassword: string; newPassword: string }) {
  return request.put<string>('/auth/password', payload).then((res) => res.data)
}

export function register(payload: {
  username: string
  password: string
  nickname?: string
  captchaId?: string
  captchaAnswer?: string
}) {
  return request
    .post<AuthPayload>('/auth/register', payload, publicConfig)
    .then((res) => toLoginResponse(res.data))
}

export function refreshToken() {
  // 双 token（§17.4）：优先用 refresh token 换发；无则回退拦截器带 access。
  const refreshTok = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY) || ''
  const cfg: ExtendedRequestConfig = refreshTok
    ? { skipAuth: true, headers: { Authorization: `Bearer ${refreshTok}` } }
    : {}
  return request.post<AuthPayload>('/auth/refresh', {}, cfg).then((res) => toLoginResponse(res.data))
}
