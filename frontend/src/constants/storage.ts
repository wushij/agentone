/**
 * src/constants/storage.ts — 本地存储 Key 常量
 */

export const STORAGE_KEYS = {
  TOKEN: 'agentone_access_token',
  REFRESH_TOKEN: 'agentone_refresh_token',
  USER_INFO: 'agentone_user',
  THEME: 'agentone_theme',
  SIDEBAR_COLLAPSED: 'agentone_sidebar_collapsed',
} as const

export const TOKEN_STORAGE_KEY = STORAGE_KEYS.TOKEN
export const REFRESH_TOKEN_STORAGE_KEY = STORAGE_KEYS.REFRESH_TOKEN
export const USER_STORAGE_KEY = STORAGE_KEYS.USER_INFO
