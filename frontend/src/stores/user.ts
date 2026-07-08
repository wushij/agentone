import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getCurrentUser, login as loginApi, logout as logoutApi } from '@/api/auth'
import { isNetworkFailure, resolveErrorStatus, TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '@/api/request'
import { clearAuthStorage } from '@/utils/session'
import { matchPermission } from '@/utils/permissions'
import type { LoginPayload, LoginResponse, UserProfile, UserRole } from '@/types'

const HYDRATE_MAX_ATTEMPTS = 3
const HYDRATE_RETRY_DELAY_MS = 1000

function delay(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms)
  })
}

function hasValidProfile(profile: UserProfile | null | undefined): profile is UserProfile {
  return Boolean(profile?.role)
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_STORAGE_KEY) || '')
  const profile = ref<UserProfile | null>(readStoredProfile())
  const initialized = ref(false)
  const backendUnavailable = ref(false)
  const permissions = ref<string[]>(readStoredProfile()?.permissions ?? [])
  const fullAccess = ref(Boolean(readStoredProfile()?.fullAccess))

  const isAuthenticated = computed(() => Boolean(token.value && hasValidProfile(profile.value)))
  const role = computed<UserRole | ''>(() => profile.value?.role ?? '')
  const isSuperAdmin = computed(() => role.value === 'super_admin' || fullAccess.value)
  const isAdmin = computed(() => isSuperAdmin.value || role.value === 'admin')
  const displayName = computed(
    () => profile.value?.nickname || profile.value?.username || '未登录'
  )

  function applyProfile(nextProfile: UserProfile) {
    profile.value = nextProfile
    permissions.value = nextProfile.permissions ?? []
    fullAccess.value = Boolean(nextProfile.fullAccess)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextProfile))
  }

  function persistSession(payload: LoginResponse) {
    token.value = payload.token
    localStorage.setItem(TOKEN_STORAGE_KEY, payload.token)
    applyProfile(payload.user)
    scheduleTokenRefresh()
  }

  function persistSessionFromResponse(payload: LoginResponse) {
    persistSession(payload)
    backendUnavailable.value = false
    initialized.value = true
  }

  let refreshTimer: ReturnType<typeof setInterval> | null = null

  function scheduleTokenRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(async () => {
      if (!token.value) return
      try {
        const { refreshToken: doRefresh } = await import('@/api/auth')
        const response = await doRefresh()
        token.value = response.token
        localStorage.setItem(TOKEN_STORAGE_KEY, response.token)
        applyProfile(response.user)
      } catch {
        /* ignore background refresh errors */
      }
    }, 30 * 60 * 1000)
  }

  function clearSession() {
    token.value = ''
    profile.value = null
    permissions.value = []
    fullAccess.value = false
    backendUnavailable.value = false
    clearAuthStorage()
    initialized.value = true
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  async function login(payload: LoginPayload) {
    const response = await loginApi(payload)
    persistSession(response)
    backendUnavailable.value = false
    initialized.value = true
    return response
  }

  async function hydrate() {
    if (initialized.value) return
    backendUnavailable.value = false

    if (!token.value) {
      profile.value = null
      initialized.value = true
      return
    }

    if (!hasValidProfile(profile.value)) {
      profile.value = readStoredProfile()
    }

    for (let attempt = 1; attempt <= HYDRATE_MAX_ATTEMPTS; attempt++) {
      try {
        const currentUser = await getCurrentUser()
        if (!hasValidProfile(currentUser)) {
          console.warn('[Auth] 用户信息不完整，将清除登录态')
          clearSession()
          return
        }
        applyProfile(currentUser)
        backendUnavailable.value = false
        initialized.value = true
        scheduleTokenRefresh()
        return
      } catch (error) {
        const status = resolveErrorStatus(error)

        if (status === 401) {
          console.warn('[Auth] 登录已失效，将跳转登录页', error)
          clearSession()
          return
        }

        const canRetry = isNetworkFailure(error) && attempt < HYDRATE_MAX_ATTEMPTS
        if (canRetry) {
          console.warn(`[Auth] 后端未就绪，${HYDRATE_RETRY_DELAY_MS}ms 后重试 (${attempt}/${HYDRATE_MAX_ATTEMPTS})`)
          await delay(HYDRATE_RETRY_DELAY_MS)
          continue
        }

        if (isNetworkFailure(error) && hasValidProfile(profile.value)) {
          console.error('[Auth] 无法校验登录状态，使用本地缓存并进入离线提示模式', error)
          permissions.value = profile.value.permissions ?? []
          fullAccess.value = Boolean(profile.value.fullAccess)
          backendUnavailable.value = true
          initialized.value = true
          return
        }

        console.warn('[Auth] 登录态无效，将清除并跳转登录页', error)
        clearSession()
        return
      }
    }
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
      /* ignore logout network errors */
    } finally {
      clearSession()
      initialized.value = true
    }
  }

  function canAccess(roles?: UserRole[]) {
    if (!roles?.length) return true
    if (!hasValidProfile(profile.value)) return false
    return roles.includes(profile.value.role)
  }

  function canAccessPermission(required?: string | string[]) {
    return matchPermission(permissions.value, required, fullAccess.value)
  }

  function updateProfile(newProfile: UserProfile) {
    applyProfile(newProfile)
  }

  return {
    token,
    profile,
    permissions,
    fullAccess,
    initialized,
    backendUnavailable,
    isAuthenticated,
    role,
    isSuperAdmin,
    isAdmin,
    displayName,
    login,
    hydrate,
    logout,
    persistSessionFromResponse,
    scheduleTokenRefresh,
    canAccess,
    canAccessPermission,
    clearSession,
    updateProfile,
    persistSession
  }
})

function readStoredProfile() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY)
    const parsed = raw ? (JSON.parse(raw) as UserProfile) : null
    return hasValidProfile(parsed) ? parsed : null
  } catch {
    return null
  }
}
