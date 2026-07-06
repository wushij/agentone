import request, { type ExtendedRequestConfig } from './request'

export interface DashboardStats {
  todayConversations: number
  todayConversationsDelta?: number
  totalTokens: number
  tokensPeriod?: string
  toolCalls: number
  toolCallsDelta?: number
  modelName: string
  modelStatus: 'online' | 'offline' | 'degraded'
  tokenUsagePercent?: number
  weeklyConversations?: number[]
}

export function getDashboardStats() {
  return request
    .get<DashboardStats>('/dashboard/stats', {
      skipErrorHandler: true
    } as ExtendedRequestConfig)
    .then((res) => res.data)
}
