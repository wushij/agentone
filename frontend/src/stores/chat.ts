import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import {
  createConversation,
  deleteConversation,
  deleteConversationsBatch,
  deleteMessage as deleteMessageApi,
  exportConversation,
  getConversation,
  listConversations,
  updateConversation
} from '@/api/conversation'
import { fetchAvailableModels as loadAvailableModels } from '@/api/chat'
import type { AvailableModel, ChatMessage, ConversationSummary } from '@/types'
import {
  isEmptyNewConversation,
  loadLastConversationId,
  nowIso,
  saveLastConversationId,
  sortConversations,
  uid
} from './chat/helpers'
import { createChatStreaming } from './chat/streaming'

export const useChatStore = defineStore('chat', () => {
  const initialized = ref(false)
  const conversations = ref<ConversationSummary[]>([])
  const currentId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const totalTokens = ref(0)
  const loadingConversations = ref(false)
  const loadingMessages = ref(false)
  const creatingConversation = ref(false)
  const searchQuery = ref('')
  const abortController = ref<AbortController | null>(null)
  const selectedModelId = ref<string | null>(null)
  const availableModels = ref<AvailableModel[]>([])
  let ensureConversationPromise: Promise<ConversationSummary> | null = null

  function applyConversationTokens(detail: { messages?: ChatMessage[]; totalTokens?: number }) {
    messages.value = detail.messages ?? []
    totalTokens.value =
      detail.totalTokens ?? messages.value.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
  }

  function recalculateTotalTokens() {
    totalTokens.value = messages.value.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
  }

  const currentConversation = computed(() =>
    conversations.value.find((c) => c.id === currentId.value) ?? null
  )

  const filteredConversations = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return conversations.value
    return conversations.value.filter((c) => c.title.toLowerCase().includes(q))
  })

  const selectedModelLabel = computed(() => {
    const model = availableModels.value.find((m) => m.name === selectedModelId.value)
    return model?.modelName || model?.name || '默认模型'
  })

  async function fetchAvailableModels() {
    try {
      availableModels.value = await loadAvailableModels()
      if (!selectedModelId.value) {
        const def = availableModels.value.find((m) => m.isDefault)
        selectedModelId.value = def?.name || availableModels.value[0]?.name || null
      }
    } catch {
      availableModels.value = []
    }
  }

  async function fetchConversations() {
    loadingConversations.value = true
    try {
      const data = await listConversations({ page: 1, size: 200 })
      conversations.value = sortConversations(data.records)
    } catch {
      conversations.value = []
    } finally {
      loadingConversations.value = false
    }
  }

  function findReusableEmptyConversation() {
    return conversations.value.find((conv) => isEmptyNewConversation(conv)) ?? null
  }

  function findLatestConversationWithMessages() {
    const withMessages = conversations.value.filter(
      (c) => (c.messageCount ?? 0) > 0 && !(c.isArchived ?? false)
    )
    if (!withMessages.length) return null
    return [...withMessages].sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    )[0]
  }

  function upsertConversation(conv: ConversationSummary) {
    const idx = conversations.value.findIndex((c) => c.id === conv.id)
    if (idx >= 0) {
      conversations.value[idx] = { ...conversations.value[idx], ...conv }
    } else {
      conversations.value.unshift(conv)
    }
    conversations.value = sortConversations([...conversations.value])
  }

  function activateConversation(conv: ConversationSummary) {
    currentId.value = conv.id
    messages.value = []
    totalTokens.value = 0
    conv.updatedAt = nowIso()
    upsertConversation(conv)
    saveLastConversationId(conv.id)
    return conv
  }

  async function createNewConversation() {
    if (ensureConversationPromise) return ensureConversationPromise

    ensureConversationPromise = (async () => {
      creatingConversation.value = true
      try {
        const conv = await createConversation({ title: '新对话' })
        return activateConversation(conv)
      } catch {
        const local: ConversationSummary = {
          id: uid('conv'),
          title: '新对话',
          messageCount: 0,
          updatedAt: nowIso()
        }
        conversations.value = sortConversations([
          local,
          ...conversations.value.filter((c) => c.id !== local.id)
        ])
        currentId.value = local.id
        messages.value = []
        totalTokens.value = 0
        return local
      } finally {
        creatingConversation.value = false
      }
    })().finally(() => {
      ensureConversationPromise = null
    })

    return ensureConversationPromise
  }

  async function syncCurrentConversation() {
    if (!currentId.value) return
    try {
      const detail = await getConversation(currentId.value)
      upsertConversation(detail)
      if (!streaming.value) {
        const localMsgs = messages.value
        const serverMsgs = detail.messages ?? []
        let localIdx = 0
        for (const sMsg of serverMsgs) {
          while (localIdx < localMsgs.length && localMsgs[localIdx].role !== sMsg.role) {
            localIdx++
          }
          if (localIdx < localMsgs.length) {
            const localMsg = localMsgs[localIdx]
            sMsg.clientId = localMsg.clientId || localMsg.id

            if (sMsg.tools && localMsg.tools) {
              for (let tIdx = 0; tIdx < sMsg.tools.length; tIdx++) {
                const sTool = sMsg.tools[tIdx]
                const lTool = localMsg.tools[tIdx]
                if (lTool && lTool.tool === sTool.tool) {
                  sTool.clientId = lTool.clientId || lTool.id
                }
              }
            }

            localIdx++
          }
        }
        messages.value = serverMsgs
        totalTokens.value =
          detail.totalTokens ?? serverMsgs.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
      }
    } catch {
      /* keep local state */
    }
  }

  const { abortStream, sendMessage, regenerateMessage } = createChatStreaming({
    messages,
    conversations,
    currentId,
    streaming,
    abortController,
    selectedModelId,
    recalculateTotalTokens,
    syncCurrentConversation,
    startNewChat: () => startNewChat()
  })

  async function selectConversation(id: string) {
    if (streaming.value) abortStream()
    currentId.value = id
    saveLastConversationId(id)

    loadingMessages.value = true
    try {
      const detail = await getConversation(id)
      applyConversationTokens(detail)
      upsertConversation(detail)
    } catch {
      messages.value = []
      totalTokens.value = 0
      if (loadLastConversationId() === id) saveLastConversationId(null)
      throw new Error('加载会话失败')
    } finally {
      loadingMessages.value = false
    }
  }

  async function startNewChat() {
    if (streaming.value) abortStream()

    if (currentId.value && currentConversation.value) {
      const current = currentConversation.value
      if (isEmptyNewConversation(current) && messages.value.length === 0) {
        return activateConversation(current)
      }
    }

    const reusable = findReusableEmptyConversation()
    if (reusable) {
      return activateConversation(reusable)
    }

    return createNewConversation()
  }

  async function openDefaultConversation() {
    if (streaming.value && currentId.value) {
      return currentConversation.value
    }

    const lastId = loadLastConversationId()
    if (lastId) {
      try {
        await selectConversation(lastId)
        if (currentConversation.value) return currentConversation.value
      } catch {
        saveLastConversationId(null)
      }
    }

    const latest = findLatestConversationWithMessages()
    if (latest) {
      await selectConversation(latest.id)
      return latest
    }

    const reusable = findReusableEmptyConversation()
    if (reusable) {
      return activateConversation(reusable)
    }

    if (conversations.value.length > 0) {
      const first = conversations.value[0]
      await selectConversation(first.id)
      return first
    }

    return createNewConversation()
  }

  async function ensureInitialized(preferredId?: string | null) {
    if (initialized.value) return
    await fetchConversations()
    if (preferredId) {
      try {
        await selectConversation(preferredId)
      } catch {
        await startNewChat()
      }
    } else {
      await startNewChat()
    }
    initialized.value = true
  }

  async function pickNextConversationAfterDelete() {
    const next =
      findLatestConversationWithMessages() ??
      findReusableEmptyConversation() ??
      conversations.value[0] ??
      null
    if (next) {
      await selectConversation(next.id)
    } else {
      await startNewChat()
    }
  }

  async function removeConversation(id: string) {
    try {
      await deleteConversation(id)
    } catch {
      ElMessage.error('删除失败')
      throw new Error('delete failed')
    }
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (loadLastConversationId() === id) saveLastConversationId(null)
    if (currentId.value === id) {
      currentId.value = null
      messages.value = []
      totalTokens.value = 0
      await pickNextConversationAfterDelete()
    }
    return currentId.value
  }

  async function removeConversationsBatch(ids: string[]) {
    if (!ids.length) return
    try {
      await deleteConversationsBatch(ids)
      ElMessage.success('批量删除成功')
    } catch {
      ElMessage.error('批量删除失败')
    }
    conversations.value = conversations.value.filter((c) => !ids.includes(c.id))
    if (ids.includes(loadLastConversationId() ?? '')) saveLastConversationId(null)
    if (currentId.value && ids.includes(currentId.value)) {
      currentId.value = null
      messages.value = []
      totalTokens.value = 0
      await pickNextConversationAfterDelete()
    }
  }

  async function archiveConversation(id: string, archive: boolean) {
    try {
      await updateConversation(id, { isArchived: archive })
      const idx = conversations.value.findIndex((c) => c.id === id)
      if (idx !== -1) {
        conversations.value[idx].isArchived = archive
      }
      if (currentId.value === id && archive) {
        currentId.value = null
        messages.value = []
        totalTokens.value = 0
        await pickNextConversationAfterDelete()
      }
      ElMessage.success(archive ? '已归档' : '已取消归档')
    } catch {
      ElMessage.error('归档操作失败')
    }
  }

  async function renameConversation(id: string, title: string) {
    try {
      const updated = await updateConversation(id, { title })
      upsertConversation(updated)
    } catch {
      const conv = conversations.value.find((c) => c.id === id)
      if (conv) conv.title = title
    }
  }

  async function removeMessage(messageId: string) {
    if (!currentId.value) return
    const convId = currentId.value
    try {
      await deleteMessageApi(convId, messageId)
      ElMessage.success('消息已删除')
    } catch {
      ElMessage.error('删除失败')
      return
    }
    try {
      const detail = await getConversation(convId)
      applyConversationTokens(detail)
      upsertConversation(detail)
    } catch {
      messages.value = messages.value.filter((m) => m.id !== messageId)
      recalculateTotalTokens()
    }
    const conv = conversations.value.find((c) => c.id === convId)
    if (conv) conv.messageCount = messages.value.length
  }

  async function exportCurrentConversation() {
    if (!currentId.value) return
    try {
      const content = await exportConversation(currentId.value)
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentConversation.value?.title || 'conversation'}.md`
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    } catch {
      ElMessage.error('导出失败')
    }
  }

  return {
    initialized,
    conversations,
    currentId,
    messages,
    streaming,
    totalTokens,
    loadingConversations,
    loadingMessages,
    creatingConversation,
    searchQuery,
    selectedModelId,
    availableModels,
    selectedModelLabel,
    currentConversation,
    filteredConversations,
    ensureInitialized,
    openDefaultConversation,
    fetchConversations,
    fetchAvailableModels,
    selectConversation,
    startNewChat,
    removeConversation,
    removeConversationsBatch,
    archiveConversation,
    renameConversation,
    sendMessage,
    regenerateMessage,
    removeMessage,
    exportCurrentConversation,
    abortStream
  }
})
