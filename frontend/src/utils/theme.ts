export type ThemePresetId =
  | 'slate'
  | 'indigo'
  | 'teal'
  | 'emerald'
  | 'amber'
  | 'blush'
  | 'rose'
  | 'violet'

export type ThemeSelection = ThemePresetId | 'custom'

export interface ThemePreset {
  id: ThemePresetId
  label: string
  primary: string
  primaryHover: string
  primaryActive: string
  bg: string
  sidebarBg: string
}

export const THEME_PRESETS: ThemePreset[] = [
  {
    id: 'slate',
    label: '石墨',
    primary: '#010710',
    primaryHover: '#0f1a2e',
    primaryActive: '#000000',
    bg: '#f3f5f8',
    sidebarBg: '#ffffff'
  },
  {
    id: 'indigo',
    label: '靛蓝',
    primary: '#4f46e5',
    primaryHover: '#4338ca',
    primaryActive: '#3730a3',
    bg: '#f5f3ff',
    sidebarBg: '#ffffff'
  },
  {
    id: 'teal',
    label: '青绿',
    primary: '#0d9488',
    primaryHover: '#0f766e',
    primaryActive: '#115e59',
    bg: '#f0fdfa',
    sidebarBg: '#ffffff'
  },
  {
    id: 'emerald',
    label: '翠绿',
    primary: '#059669',
    primaryHover: '#047857',
    primaryActive: '#065f46',
    bg: '#ecfdf5',
    sidebarBg: '#ffffff'
  },
  {
    id: 'amber',
    label: '琥珀',
    primary: '#d97706',
    primaryHover: '#b45309',
    primaryActive: '#92400e',
    bg: '#fffbeb',
    sidebarBg: '#ffffff'
  },
  {
    id: 'blush',
    label: '淡粉',
    primary: '#e89696',
    primaryHover: '#dc8585',
    primaryActive: '#cf7575',
    bg: '#fffbfb',
    sidebarBg: '#ffffff'
  },
  {
    id: 'rose',
    label: '玫红',
    primary: '#e11d48',
    primaryHover: '#be123c',
    primaryActive: '#9f1239',
    bg: '#fff1f2',
    sidebarBg: '#ffffff'
  },
  {
    id: 'violet',
    label: '紫韵',
    primary: '#7c3aed',
    primaryHover: '#6d28d9',
    primaryActive: '#5b21b6',
    bg: '#f5f3ff',
    sidebarBg: '#ffffff'
  }
]

export const DEFAULT_THEME_ID: ThemePresetId = 'slate'

const THEME_MAP = Object.fromEntries(THEME_PRESETS.map((preset) => [preset.id, preset])) as Record<
  ThemePresetId,
  ThemePreset
>

const THEME_STORAGE_KEY = 'ao_theme'
const MODE_STORAGE_KEY = 'ao_color_mode'

function hexToRgb(hex: string) {
  const raw = hex.replace('#', '')
  const full = raw.length === 3 ? raw.split('').map((char) => char + char).join('') : raw
  const num = parseInt(full, 16)
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  }
}

function clampChannel(value: number) {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function rgbToHex(r: number, g: number, b: number) {
  return `#${[r, g, b].map((item) => clampChannel(item).toString(16).padStart(2, '0')).join('')}`
}

export function normalizeHex(input: string, fallback = '#010710') {
  let hex = input.trim()
  if (!hex.startsWith('#')) hex = `#${hex}`
  if (/^#[0-9a-fA-F]{3}$/.test(hex)) {
    hex = `#${hex
      .slice(1)
      .split('')
      .map((char) => char + char)
      .join('')}`
  }
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) return fallback
  return hex.toLowerCase()
}

function rgba(hex: string, alpha: number) {
  const { r, g, b } = hexToRgb(hex)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function darken(hex: string, ratio: number) {
  const { r, g, b } = hexToRgb(hex)
  const factor = 1 - ratio
  return rgbToHex(r * factor, g * factor, b * factor)
}

function tintBg(hex: string) {
  const { r, g, b } = hexToRgb(hex)
  const ratio = 0.93
  return rgbToHex(r + (255 - r) * ratio, g + (255 - g) * ratio, b + (255 - b) * ratio)
}

interface ThemeVars {
  id: string
  primary: string
  primaryHover: string
  primaryActive: string
  bg: string
  sidebarBg: string
}

let activeTheme: ThemeVars | null = null

const SURFACE_VAR_KEYS = [
  '--theme-bg',
  '--theme-sidebar-bg',
  '--theme-text-base',
  '--theme-text-secondary',
  '--theme-border'
] as const

function clearSurfaceVars() {
  const root = document.documentElement
  for (const key of SURFACE_VAR_KEYS) {
    root.style.removeProperty(key)
  }
}

function applyLightSurfaceVars(theme: ThemeVars) {
  const root = document.documentElement
  root.style.setProperty('--theme-bg', theme.bg)
  root.style.setProperty('--theme-sidebar-bg', theme.sidebarBg)
  root.style.setProperty('--theme-text-base', '#1e293b')
  root.style.setProperty('--theme-text-secondary', '#64748b')
  root.style.setProperty('--theme-border', '#e2e8f0')
}

function applySurfaceVars(theme: ThemeVars, dark: boolean) {
  if (dark) {
    clearSurfaceVars()
  } else {
    applyLightSurfaceVars(theme)
  }
}

function applyBrandVars(theme: ThemeVars) {
  const root = document.documentElement

  root.dataset.theme = theme.id
  root.style.setProperty('--theme-primary', theme.primary)
  root.style.setProperty('--theme-primary-hover', theme.primaryHover)
  root.style.setProperty('--theme-primary-active', theme.primaryActive)
  root.style.setProperty('--theme-primary-muted', rgba(theme.primary, 0.08))
  root.style.setProperty('--theme-primary-muted-strong', rgba(theme.primary, 0.14))
  root.style.setProperty(
    '--theme-primary-gradient',
    `linear-gradient(135deg, ${theme.primary} 0%, ${theme.primaryHover} 100%)`
  )
  root.style.setProperty('--theme-logo-end', theme.primaryActive)
  root.style.setProperty('--el-color-primary', theme.primary)
}

function applyThemeVars(theme: ThemeVars) {
  activeTheme = theme
  applyBrandVars(theme)
  applySurfaceVars(theme, resolveDark(loadColorMode()))
}

export function applyThemePreset(id: ThemePresetId) {
  const preset = THEME_MAP[id] ?? THEME_MAP[DEFAULT_THEME_ID]
  applyThemeVars(preset)
}

export function applyCustomTheme(primary: string) {
  const color = normalizeHex(primary)
  applyThemeVars({
    id: 'custom',
    primary: color,
    primaryHover: darken(color, 0.14),
    primaryActive: darken(color, 0.24),
    bg: tintBg(color),
    sidebarBg: '#ffffff'
  })
  return color
}

export const themePresetList = THEME_PRESETS

export function findPresetIdByPrimary(color: string): ThemePresetId | undefined {
  const normalized = normalizeHex(color)
  return THEME_PRESETS.find((preset) => preset.primary === normalized)?.id
}

export function getThemePreset(id: ThemePresetId) {
  return THEME_MAP[id] ?? THEME_MAP[DEFAULT_THEME_ID]
}

export function loadStoredTheme(): ThemeSelection {
  try {
    const raw = localStorage.getItem(THEME_STORAGE_KEY)
    if (!raw) return DEFAULT_THEME_ID
    if (!raw.startsWith('{')) {
      const legacy = raw as ThemePresetId
      if (THEME_MAP[legacy]) return legacy
      return DEFAULT_THEME_ID
    }
    const parsed = JSON.parse(raw) as { id?: ThemeSelection; customColor?: string }
    if (parsed.id === 'custom' && parsed.customColor) return 'custom'
    if (parsed.id && THEME_MAP[parsed.id as ThemePresetId]) return parsed.id as ThemePresetId
  } catch {
    /* ignore */
  }
  return DEFAULT_THEME_ID
}

export function loadStoredCustomColor() {
  try {
    const raw = localStorage.getItem(THEME_STORAGE_KEY)
    if (!raw?.startsWith('{')) return null
    const parsed = JSON.parse(raw) as { customColor?: string }
    return parsed.customColor ? normalizeHex(parsed.customColor) : null
  } catch {
    return null
  }
}

export function saveThemeSelection(selection: ThemeSelection, customColor?: string) {
  localStorage.setItem(
    THEME_STORAGE_KEY,
    JSON.stringify({ id: selection, customColor: customColor ?? null })
  )
}

export function initThemeFromStorage() {
  const stored = loadStoredTheme()
  if (stored === 'custom') {
    const color = loadStoredCustomColor()
    if (color) {
      applyCustomTheme(color)
      return color
    }
  }
  const presetId = stored === 'custom' ? DEFAULT_THEME_ID : stored
  applyThemePreset(presetId)
  return getThemePreset(presetId).primary
}

export type ColorMode = 'light' | 'dark' | 'system'

export function loadColorMode(): ColorMode {
  const v = localStorage.getItem(MODE_STORAGE_KEY)
  if (v === 'dark' || v === 'system') return v
  return 'light'
}

export function saveColorMode(mode: ColorMode) {
  localStorage.setItem(MODE_STORAGE_KEY, mode)
}

export function resolveDark(mode: ColorMode): boolean {
  if (mode === 'dark') return true
  if (mode === 'system') return window.matchMedia('(prefers-color-scheme: dark)').matches
  return false
}

export function applyColorMode(mode: ColorMode) {
  const dark = resolveDark(mode)
  document.documentElement.classList.toggle('dark', dark)
  if (activeTheme) {
    applySurfaceVars(activeTheme, dark)
  }
}
