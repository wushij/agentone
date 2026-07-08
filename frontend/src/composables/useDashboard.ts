import { computed, inject, onMounted, provide, ref, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import { fetchDashboardStats, type DashboardStats } from '@/api/admin'
import { useChatStore } from '@/stores/chat'
import { useNotifyStore } from '@/stores/notify'
import { useUserStore } from '@/stores/user'
import type { ConversationSummary, NotificationItem } from '@/types'

export interface DashboardMetric {
  title: string
  value: string | number
  unit: string
  color: string
  trend: 'flat' | 'up' | 'down'
  trendText: string
}

export interface DashboardAnnouncement {
  id: string
  title: string
  body: string
  time: string
}

export interface DashboardContext {
  userStore: ReturnType<typeof useUserStore>
  notifyStore: ReturnType<typeof useNotifyStore>
  stats: Ref<DashboardMetric[]>
  weeklyData: Ref<{ date: string; count: number }[]>
  maxWeekly: Ref<number>
  tokenPercent: Ref<number>
  announcements: Ref<DashboardAnnouncement[]>
  recentChats: ComputedRef<ConversationSummary[]>
  recentActivity: ComputedRef<NotificationItem[]>
}

export const DASHBOARD_KEY: InjectionKey<DashboardContext> = Symbol('dashboard')

export function useDashboardProvider(): DashboardContext {
  const chatStore = useChatStore()
  const notifyStore = useNotifyStore()
  const userStore = useUserStore()

  const apiStats = ref<DashboardStats>({
    todayConversations: 0,
    totalTokens: 0,
    toolCalls: 0,
    modelStatus: 'online',
    modelName: 'mock-chat',
    recentConversations: []
  })

  const stats = computed(() => {
    const online = apiStats.value.modelStatus === 'online'
    return [
      {
        title: '今日对话',
        value: apiStats.value.todayConversations || chatStore.conversations.length,
        unit: '条',
        color: '#4f46e5',
        trend: 'flat' as const,
        trendText: '今日会话数'
      },
      {
        title: 'Token 消耗',
        value: apiStats.value.totalTokens || chatStore.totalTokens || 0,
        unit: '',
        color: '#0d9488',
        trend: 'flat' as const,
        trendText: '全平台累计'
      },
      {
        title: 'Tool 调用',
        value: apiStats.value.toolCalls,
        unit: '次',
        color: '#7c3aed',
        trend: 'flat' as const,
        trendText: '历史累计'
      },
      {
        title: '模型状态',
        value: online ? '在线' : '离线',
        unit: '',
        color: online ? '#16a34a' : '#e11d48',
        trend: online ? ('up' as const) : ('down' as const),
        trendText: online ? `当前模型：${apiStats.value.modelName}` : '请检查模型配置'
      }
    ]
  })

  const weeklyData = computed(() => apiStats.value.weeklyConversations ?? [])
  const maxWeekly = computed(() => Math.max(...weeklyData.value.map((d) => d.count), 1))
  const tokenPercent = computed(() => apiStats.value.tokenUsagePercent ?? 0)

  const defaultAnnouncements: DashboardAnnouncement[] = [
    {
      id: 'ann_1',
      title: '系统公告',
      body: 'AgentOne V1.0 已上线，欢迎使用企业级 AI 智能体平台。',
      time: '今天'
    }
  ]

  const announcements = computed(() => {
    if (apiStats.value.announcements?.length) {
      return apiStats.value.announcements.map((a) => ({
        id: a.id,
        title: a.title,
        body: a.body,
        time: new Date(a.timestamp).toLocaleDateString('zh-CN')
      }))
    }
    if (notifyStore.announcements.length) {
      return notifyStore.announcements.map((a) => ({
        id: a.id,
        title: a.title,
        body: a.body,
        time: new Date(a.timestamp).toLocaleDateString('zh-CN')
      }))
    }
    return defaultAnnouncements
  })

  const recentChats = computed(() => {
    if (apiStats.value.recentConversations?.length) {
      return apiStats.value.recentConversations
    }
    return chatStore.conversations.slice(0, 5)
  })

  const recentActivity = computed(() => notifyStore.recentActivity)

  onMounted(async () => {
    void chatStore.fetchConversations()
    try {
      apiStats.value = await fetchDashboardStats()
    } catch {
      /* fallback */
    }
  })

  const ctx: DashboardContext = {
    userStore,
    notifyStore,
    stats,
    weeklyData,
    maxWeekly,
    tokenPercent,
    announcements,
    recentChats,
    recentActivity
  }

  provide(DASHBOARD_KEY, ctx)
  return ctx
}

export function useDashboard(): DashboardContext {
  const ctx = inject(DASHBOARD_KEY)
  if (!ctx) {
    throw new Error('useDashboard() must be used within Dashboard')
  }
  return ctx
}
