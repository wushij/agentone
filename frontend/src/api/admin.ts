import request from './request'

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
  embeddingModel: string
  retrievalMode: 'hybrid' | 'vector' | 'fulltext'
  topK: number
  scoreThreshold: number
  createdAt: string
}

export function fetchDashboardStats() {
  return request.get<DashboardStats>('/dashboard/stats').then((r) => r.data)
}

export function fetchPublicSettings() {
  return request
    .get<{ siteName: string; theme: string; colorMode: string }>('/settings/public', { skipAuth: true } as never)
    .then((r) => r.data)
}

export function fetchTools() {
  return request.get<Array<{ name: string; description: string; type: string; status: string }>>('/tools').then((r) => r.data)
}

export function updateTool(name: string, data: { description?: string; status?: string }) {
  return request.put(`/tools/${name}`, data).then((r) => r.data)
}

export function toggleToolStatus(name: string, enabled: boolean) {
  return request.patch(`/tools/${name}/status`, null, { params: { enabled } }).then((r) => r.data)
}

export function fetchPrompts() {
  return request.get<PromptItem[]>('/prompts').then((r) => r.data)
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

export function fetchPromptHistory(name: string) {
  return request.get<PromptHistoryItem[]>(`/prompts/${name}/history`).then((r) => r.data)
}

export function rollbackPrompt(name: string, version: number) {
  return request.post<PromptItem>(`/prompts/${name}/rollback`, { version }).then((r) => r.data)
}

export function fetchModels() {
  return request.get<ModelItem[]>('/models').then((r) => r.data)
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

export function fetchLogs(type = 'tool', page = 1, pageSize = 20) {
  return request
    .get<{
      items: Array<{
        id: number
        time: string
        module: string
        type: string
        status: string
        message: string
        durationMs?: number
      }>
    }>('/logs', { params: { type, page, pageSize } })
    .then((r) => r.data)
}

export function deleteLog(id: number, type = 'tool') {
  return request.delete(`/logs/${id}`, { params: { type } }).then((r) => r.data)
}

export function exportLogs(type = 'tool') {
  return request
    .get<string>('/logs/export', { params: { type }, responseType: 'text' as never })
    .then((r) => r.data as unknown as string)
}

export function fetchFiles() {
  return request.get<FileItem[]>('/files').then((r) => r.data)
}

export function uploadFile(file: File, category = 'general') {
  const form = new FormData()
  form.append('file', file)
  return request.post<FileItem>('/files/upload', form, { params: { category } }).then((r) => r.data)
}

export function deleteFile(id: string) {
  return request.delete(`/files/${id}`).then((r) => r.data)
}

export function fetchKnowledge() {
  return request.get<KnowledgeItem[]>('/knowledge').then((r) => r.data)
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

export function fetchUsers() {
  return request.get<UserItem[]>('/users').then((r) => r.data)
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
