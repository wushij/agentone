import request from './request'
import type { ApiListParams, ApiPage } from '@/types/pagination'
import { normalizePage, fetchAllPages } from '@/utils/normalizePage'

export interface DashboardStats {
  todayConversations: number
  totalTokens: number
  toolCalls: number
  modelStatus: string
  modelName: string
  recentConversations: Array<{
    id: string
    title: string
    messageCount: number
    updatedAt: string
  }>
  weeklyConversations?: Array<{ date: string; count: number }>
  tokenUsagePercent?: number
  announcements?: Array<{ id: string; title: string; body: string; timestamp: string }>
}

export interface ModelItem {
  name: string
  provider: string
  modelName: string
  baseUrl?: string
  apiKey?: string
  hasApiKey?: boolean
  temperature: number
  status: string
  isDefault: boolean
}

export interface PromptItem {
  name: string
  type: string
  content: string
  version: number
  enabled: boolean
  updatedAt?: string
}

export interface FileItem {
  id: string
  name: string
  type: string
  size: string
  sizeBytes?: number
  category?: string
  time: string
  createdAt?: string
}

export interface KnowledgeItem {
  id: string
  name: string
  description: string
  fileIds: string[]
  chunkSize: number
  chunkOverlap: number
  segmentDelimiter?: 'newline' | 'paragraph' | 'none'
  embeddingModel: string
  retrievalMode: 'hybrid' | 'vector' | 'fulltext'
  topK: number
  scoreThreshold: number
  createdAt: string
}

export interface KnowledgeSegment {
  id: string
  fileId: string
  fileName: string
  index: number
  charCount: number
  text: string
}

export interface KnowledgePreviewResult {
  kbId: string
  kbName: string
  total: number
  chunkSize: number
  chunkOverlap: number
  segmentDelimiter: string
  segmentDelimiterLabel: string
  fileErrors?: string[]
  segments: KnowledgeSegment[]
}

export function fetchDashboardStats() {
  return request.get<DashboardStats>('/dashboard/stats').then((r) => r.data)
}

export function fetchPublicSettings() {
  return request
    .get<{ siteName: string; theme: string; colorMode: string }>('/settings/public', { skipAuth: true } as never)
    .then((r) => r.data)
}

export function fetchTools(params?: ApiListParams) {
  return request
    .get<ApiPage<{ name: string; description: string; type: string; status: string }>>('/tools', { params })
    .then((r) => normalizePage(r.data))
}

export function updateTool(name: string, data: { description?: string; status?: string }) {
  return request.put(`/tools/${name}`, data).then((r) => r.data)
}

export function toggleToolStatus(name: string, enabled: boolean) {
  return request.patch(`/tools/${name}/status`, null, { params: { enabled } }).then((r) => r.data)
}

export function fetchPrompts(params?: ApiListParams) {
  return request.get<ApiPage<PromptItem>>('/prompts', { params }).then((r) => normalizePage(r.data))
}

export function createPrompt(data: { name: string; content: string; type?: string }) {
  return request.post<PromptItem>('/prompts', data).then((r) => r.data)
}

export function updatePrompt(name: string, content: string) {
  return request.put<PromptItem>(`/prompts/${name}`, { content }).then((r) => r.data)
}

export interface PromptHistoryItem {
  id: number
  version: number
  content: string
  createdAt?: string
}

export function setPromptEnabled(name: string, enabled: boolean) {
  return request.patch<PromptItem>(`/prompts/${name}/status`, { enabled }).then((r) => r.data)
}

export function deletePrompt(name: string) {
  return request.delete(`/prompts/${name}`).then((r) => r.data)
}

export function fetchPromptHistory(name: string, params?: ApiListParams) {
  return request
    .get<ApiPage<PromptHistoryItem>>(`/prompts/${name}/history`, { params })
    .then((r) => normalizePage(r.data))
}

export function rollbackPrompt(name: string, version: number) {
  return request.post<PromptItem>(`/prompts/${name}/rollback`, { version }).then((r) => r.data)
}

export function fetchModels(params?: ApiListParams) {
  return request.get<ApiPage<ModelItem>>('/models', { params }).then((r) => normalizePage(r.data))
}

/** 下拉选择器等场景：分页拉取全量 */
export function fetchAllModels() {
  return fetchAllPages((page, size) => fetchModels({ page, size }))
}

export function createModel(data: Partial<ModelItem> & { name: string; provider: string; modelName: string }) {
  return request.post<ModelItem>('/models', data).then((r) => r.data)
}

export function updateModel(name: string, data: Partial<ModelItem>) {
  return request.put<ModelItem>(`/models/${name}`, data).then((r) => r.data)
}

export function deleteModel(name: string) {
  return request.delete(`/models/${name}`).then((r) => r.data)
}

export function setDefaultModel(name: string) {
  return request.post(`/models/${name}/default`).then((r) => r.data)
}

export function testModel(name: string) {
  return request.post<{ latencyMs?: number }>(`/models/${name}/test`).then((r) => r.data)
}

export function fetchSettings() {
  return request.get<Record<string, unknown>>('/settings').then((r) => r.data)
}

export function updateSettings(data: Record<string, unknown>) {
  return request.put('/settings', data).then((r) => r.data)
}

export function fetchLogs(type = 'tool', page = 1, size = 10) {
  return request
    .get<ApiPage<{
      id: number
      time: string
      module: string
      type: string
      status: string
      message: string
      durationMs?: number
    }>>('/logs', { params: { type, page, size } })
    .then((r) => normalizePage(r.data))
}

export function deleteLog(id: number, type = 'tool') {
  return request.delete(`/logs/${id}`, { params: { type } }).then((r) => r.data)
}

export function clearLogs(type = 'tool') {
  return request.delete('/logs/clear', { params: { type } }).then((r) => r.data)
}

export function exportLogs(type = 'tool') {
  return request
    .get<string>('/logs/export', { params: { type }, responseType: 'text' as never })
    .then((r) => r.data as unknown as string)
}

export function fetchFiles(params?: ApiListParams) {
  return request.get<ApiPage<FileItem>>('/files', { params }).then((r) => normalizePage(r.data))
}

/** 知识库文件选择器等场景 */
export function fetchAllFiles(keyword = '') {
  return fetchAllPages((page, size) => fetchFiles({ page, size, keyword }))
}

export function uploadFile(file: File, category = 'general') {
  const form = new FormData()
  form.append('file', file)
  return request.post<FileItem>('/files/upload', form, { params: { category } }).then((r) => r.data)
}

export function deleteFile(id: string) {
  return request.delete(`/files/${id}`).then((r) => r.data)
}

export function fetchKnowledge(params?: ApiListParams) {
  return request.get<ApiPage<KnowledgeItem>>('/knowledge', { params }).then((r) => normalizePage(r.data))
}

/** 聊天知识库选择器等场景 */
export function fetchAllKnowledge() {
  return fetchAllPages((page, size) => fetchKnowledge({ page, size }))
}

export function createKnowledge(data: Partial<KnowledgeItem>) {
  return request.post<KnowledgeItem>('/knowledge', data).then((r) => r.data)
}

export function updateKnowledge(id: string, data: Partial<KnowledgeItem>) {
  return request.put<KnowledgeItem>(`/knowledge/${id}`, data).then((r) => r.data)
}

export function deleteKnowledge(id: string) {
  return request.delete(`/knowledge/${id}`).then((r) => r.data)
}

export function fetchKnowledgePreview(kbId: string, params?: ApiListParams) {
  return request
    .get<KnowledgePreviewResult>(`/knowledge/${kbId}/preview`, { params })
    .then((r) => r.data)
}

export function previewKnowledgeDraft(data: Partial<KnowledgeItem>, params?: ApiListParams) {
  return request.post<KnowledgePreviewResult>('/knowledge/preview', data, { params }).then((r) => r.data)
}

export interface UserItem {
  id: number
  username: string
  nickname?: string
  avatar?: string
  role: string
  status: number
  createdAt?: string
  lastLoginAt?: string
}

export function fetchUsers(params?: ApiListParams) {
  return request.get<ApiPage<UserItem>>('/users', { params }).then((r) => normalizePage(r.data))
}

export function createUser(data: {
  username: string
  password: string
  nickname?: string
  role?: string
}) {
  return request.post<UserItem>('/users', data).then((r) => r.data)
}

export function updateUser(
  id: number,
  data: { nickname?: string; role?: string; status?: number }
) {
  return request.put<UserItem>(`/users/${id}`, data).then((r) => r.data)
}

export function deleteUser(id: number) {
  return request.delete(`/users/${id}`).then((r) => r.data)
}
