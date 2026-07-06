import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  applyColorMode,
  applyCustomTheme,
  applyThemePreset,
  findPresetIdByPrimary,
  getThemePreset,
  initThemeFromStorage,
  loadColorMode,
  loadStoredTheme,
  resolveDark,
  saveColorMode,
  saveThemeSelection,
  type ColorMode,
  type ThemePresetId
} from '@/utils/theme'

export type { ColorMode, ThemePresetId as ThemePreset } from '@/utils/theme'

export const useThemeStore = defineStore('theme', () => {
  const stored = loadStoredTheme()
  const themeColor = ref(initThemeFromStorage())
  const themePreset = ref<ThemePresetId>(stored === 'custom' ? 'slate' : stored)
  const colorMode = ref<ColorMode>(loadColorMode())

  const activePresetId = computed(() => findPresetIdByPrimary(themeColor.value) ?? 'custom')
  const isDark = computed(() => resolveDark(colorMode.value))

  function applyMode() {
    applyColorMode(colorMode.value)
  }

  function setTheme(id: ThemePresetId) {
    themePreset.value = id
    applyThemePreset(id)
    themeColor.value = getThemePreset(id).primary
    saveThemeSelection(id)
    applyMode()
  }

  function setCustomColor(color: string | null) {
    if (!color) return
    const presetId = findPresetIdByPrimary(color)
    if (presetId) {
      setTheme(presetId)
      return
    }
    themeColor.value = applyCustomTheme(color)
    saveThemeSelection('custom', color)
    applyMode()
  }

  function setColorMode(next: ColorMode) {
    colorMode.value = next
    saveColorMode(next)
    applyMode()
  }

  function toggleColorMode() {
    setColorMode(isDark.value ? 'light' : 'dark')
  }

  function init() {
    initThemeFromStorage()
    applyMode()
    if (colorMode.value === 'system') {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyMode)
    }
  }

  function applyFromSettings(data: { theme?: string; colorMode?: string }) {
    const validPresets: ThemePresetId[] = [
      'slate', 'indigo', 'teal', 'violet', 'emerald', 'rose', 'amber', 'blush'
    ]
    if (data.theme && validPresets.includes(data.theme as ThemePresetId)) {
      setTheme(data.theme as ThemePresetId)
    }
    if (data.colorMode && ['light', 'dark', 'system'].includes(data.colorMode)) {
      setColorMode(data.colorMode as ColorMode)
    }
  }

  return {
    theme: themePreset,
    themeColor,
    activePresetId,
    colorMode,
    isDark,
    setTheme,
    setCustomColor,
    setColorMode,
    toggleColorMode,
    init,
    applyFromSettings
  }
})
