<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { useNotifySocket } from '@/composables/useNotifySocket'
import { fetchPublicSettings } from '@/api/admin'

const userStore = useUserStore()
const themeStore = useThemeStore()
const notifySocket = useNotifySocket()

watch(
  () => userStore.token,
  (token) => {
    if (token) notifySocket.connect(token)
    else notifySocket.disconnect()
  },
  { immediate: true }
)

onMounted(async () => {
  themeStore.init()
  try {
    const pub = await fetchPublicSettings()
    if (!localStorage.getItem('ao_theme')) {
      themeStore.applyFromSettings(pub)
    }
  } catch {
    /* use local theme */
  }
  if (userStore.token) notifySocket.connect(userStore.token)
})
</script>
