import request from './request'

export interface CostGroupRow {
  key: string
  costUsd: number
  tokens: number
}

export interface CostSummary {
  totalUsd: number
  byModel: CostGroupRow[]
  byProvider: CostGroupRow[]
  byAgentRole: CostGroupRow[]
}

export interface MyCost {
  todayUsd: number
  dailyLimitUsd: number
  allowed: boolean
}

export function fetchCostSummary(days = 7) {
  return request.get<CostSummary>('/cost/summary', { params: { days } }).then((r) => r.data)
}

export function fetchMyCost() {
  return request.get<MyCost>('/cost/me').then((r) => r.data)
}
