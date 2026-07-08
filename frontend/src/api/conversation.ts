import request from './request'
import type { ApiListParams, ApiPage } from '@/types/pagination'
import { normalizePage } from '@/utils/normalizePage'
import type { ChatMessage, ConversationSummary } from '@/types'

export interface ConversationDetail extends ConversationSummary {
  messages: ChatMessage[]
  totalTokens?: number
}

export interface WorkflowSnapshotNode {
  node: string
  status: 'pending' | 'running' | 'success' | 'error'
  label?: string
  detail?: string
  tool?: string
  elapsedMs?: number
  error?: string
}

export interface WorkflowSnapshot {
  conversationId: string
  updatedAt?: string | null
  nodes: WorkflowSnapshotNode[]
}

export interface CreateConversationPayload {
  title?: string
}

export interface UpdateConversationPayload {
  title?: string
  starred?: boolean
  isArchived?: boolean
}

export function listConversations(params?: ApiListParams & { q?: string }) {
  return request
    .get<ApiPage<ConversationSummary>>('/conversations', { params })
    .then((res) => normalizePage(res.data))
}

export function createConversation(payload?: CreateConversationPayload) {
  return request
    .post<ConversationSummary>('/conversations', payload ?? {})
    .then((res) => res.data)
}

export function getConversation(id: string) {
  return request
    .get<ConversationDetail>(`/conversations/${id}`)
    .then((res) => res.data)
}

export function getWorkflowSnapshot(id: string) {
  return request
    .get<WorkflowSnapshot>(`/conversations/${id}/workflow-snapshot`)
    .then((res) => res.data)
}

export function updateConversation(id: string, payload: UpdateConversationPayload) {
  return request
    .put<ConversationSummary>(`/conversations/${id}`, payload)
    .then((res) => res.data)
}

export function deleteConversation(id: string) {
  return request.delete<void>(`/conversations/${id}`).then((res) => res.data)
}

export function deleteConversationsBatch(ids: string[]) {
  return request.post<void>('/conversations/batch-delete', { ids }).then((res) => res.data)
}

export function deleteMessage(conversationId: string, messageId: string) {
  return request
    .delete<void>(`/conversations/${conversationId}/messages/${messageId}`)
    .then((res) => res.data)
}

export function batchDeleteConversations(ids: string[]) {
  return request
    .post<{ deleted: number }>('/conversations/batch-delete', { ids })
    .then((res) => res.data)
}

export function exportConversation(conversationId: string) {
  return request
    .get<string>(`/conversations/${conversationId}/export`, { responseType: 'text' as never })
    .then((res) => res.data as unknown as string)
}

export function searchConversations(q: string, page = 1, size = 50) {
  return listConversations({ q, page, size })
}
