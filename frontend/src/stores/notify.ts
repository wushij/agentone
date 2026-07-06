import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { NotificationItem } from '@/types'

export const useNotifyStore = defineStore('notify', () => {
  const notifications = ref<NotificationItem[]>([])
  const announcements = ref<NotificationItem[]>([])
  const wsConnected = ref(false)
  const reconnecting = ref(false)

  const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length)

  const recentActivity = computed(() =>
    [...notifications.value]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 8)
  )

  function addNotification(item: Omit<NotificationItem, 'read'>) {
    const entry: NotificationItem = { ...item, read: false }
    notifications.value.unshift(entry)

    if (item.title.includes('公告') || item.level === 'info') {
      announcements.value.unshift(entry)
      if (announcements.value.length > 5) {
        announcements.value = announcements.value.slice(0, 5)
      }
    }

    if (notifications.value.length > 50) {
      notifications.value = notifications.value.slice(0, 50)
    }
  }

  function markRead(id: string) {
    const item = notifications.value.find((n) => n.id === id)
    if (item) item.read = true
  }

  function markAllRead() {
    notifications.value.forEach((n) => {
      n.read = true
    })
  }

  function setWsConnected(value: boolean) {
    wsConnected.value = value
    if (value) reconnecting.value = false
  }

  function setReconnecting(value: boolean) {
    reconnecting.value = value
  }

  function reset() {
    notifications.value = []
    announcements.value = []
    wsConnected.value = false
    reconnecting.value = false
  }

  return {
    notifications,
    announcements,
    wsConnected,
    reconnecting,
    unreadCount,
    recentActivity,
    addNotification,
    markRead,
    markAllRead,
    setWsConnected,
    setReconnecting,
    reset
  }
})
