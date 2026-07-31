import request from './request'
import type { ApiListParams, ApiPage } from '@/types/pagination'
import { normalizePage } from '@/utils/normalizePage'

export interface MemoryItem {
  id: number
  content: string
  kind: string
  scope: string
  importance: number
  accessCount: number
  pinned: boolean
  createdAt?: string
}

export function fetchMemories(params?: ApiListParams) {
  return request.get<ApiPage<MemoryItem>>('/memories', { params }).then((r) => normalizePage<MemoryItem>(r.data))
}

export function deleteMemory(id: number) {
  return request.delete(`/memories/${id}`).then((r) => r.data)
}

export function pinMemory(id: number, pinned: boolean) {
  return request.put(`/memories/${id}/pin`, { pinned }).then((r) => r.data)
}
