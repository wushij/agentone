import type { ConversationSummary } from '@/types'

export function uid(prefix = 'msg') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export function nowIso() {
  return new Date().toISOString()
}

export function isEmptyNewConversation(conv: ConversationSummary) {
  return conv.title === '新对话' && (conv.messageCount ?? 0) === 0 && !(conv.isArchived ?? false)
}

export function sortConversations(list: ConversationSummary[]) {
  const emptyNew: ConversationSummary[] = []
  const rest: ConversationSummary[] = []
  for (const conv of list) {
    if (isEmptyNewConversation(conv)) emptyNew.push(conv)
    else rest.push(conv)
  }
  const byUpdatedAtDesc = (a: ConversationSummary, b: ConversationSummary) =>
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  emptyNew.sort(byUpdatedAtDesc)
  rest.sort(byUpdatedAtDesc)
  return [...emptyNew, ...rest]
}

const LAST_CONVERSATION_KEY = 'agentone-last-conversation-id'

export function saveLastConversationId(id: string | null) {
  try {
    if (id) localStorage.setItem(LAST_CONVERSATION_KEY, id)
    else localStorage.removeItem(LAST_CONVERSATION_KEY)
  } catch {
    /* ignore */
  }
}

export function loadLastConversationId() {
  try {
    return localStorage.getItem(LAST_CONVERSATION_KEY)
  } catch {
    return null
  }
}

/** 与后端 graph_runner 一致：约 4 字符 ≈ 1 token（流式阶段估算用） */
export function estimateMessageTokens(content: string): number {
  const text = content.trim()
  if (!text) return 0
  return Math.max(1, Math.ceil(text.length / 4))
}
