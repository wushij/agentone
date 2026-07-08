export type UserRole = 'super_admin' | 'admin' | 'user'

export interface UserProfile {
  id: number | string
  username: string
  nickname?: string
  avatar?: string
  role: UserRole
  status?: number
  createTime?: string
  permissions?: string[]
  fullAccess?: boolean
}

export interface LoginPayload {
  username: string
  password: string
  captchaId?: string
  captchaAnswer?: string
}

export interface LoginResponse {
  token: string
  refreshToken?: string
  expiresAt?: string
  user: UserProfile
}

export interface CaptchaState {
  id: string
  img: string
  required?: boolean
}

export interface ConversationSummary {
  id: string
  title: string
  messageCount: number
  totalTokens?: number
  updatedAt: string
  starred?: boolean
  isArchived?: boolean
}

export interface ChatMessage {
  id: string
  clientId?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt?: string
  tokens?: number
  tools?: ToolCallState[]
  steps?: WorkflowStep[]
  streaming?: boolean
}

export interface ToolCallState {
  id: string
  clientId?: string
  tool: string
  input?: Record<string, unknown>
  output?: string
  durationMs?: number
  status: 'running' | 'done' | 'error'
}

export interface WorkflowStep {
  node: string
  label: string
  status: 'pending' | 'running' | 'success' | 'error'
  tool?: string
  elapsedMs?: number
  error?: string
}

export type KbMode = 'generate' | 'retrieve'

export interface ChatStreamRequest {
  conversationId: string
  message: string
  modelId?: string
  /** @deprecated use kbIds */
  kbId?: string
  kbIds?: string[]
  kbMode?: KbMode
  enableTools?: boolean
}

export interface ChatRegenerateRequest {
  conversationId: string
  messageId?: string
  modelId?: string
  /** @deprecated use kbIds */
  kbId?: string
  kbIds?: string[]
  kbMode?: KbMode
  enableTools?: boolean
}

export interface AvailableModel {
  name: string
  modelName: string
  provider: string
  isDefault: boolean
}

export interface NotificationItem {
  id: string
  level: 'info' | 'success' | 'warning' | 'error'
  title: string
  body: string
  timestamp: string
  read: boolean
  action?: { label: string; route: string }
}
