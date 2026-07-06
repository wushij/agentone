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
import {
  createChatStream,
  createRegenerateStream,
  fetchAvailableModels as loadAvailableModels,
  type SseTokenPayload,
  type SseToolEndPayload,
  type SseToolStartPayload
} from '@/api/chat'
import type { AvailableModel, ChatMessage, ConversationSummary } from '@/types'

function uid(prefix = 'msg') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function nowIso() {
  return new Date().toISOString()
}

function isEmptyNewConversation(conv: ConversationSummary) {
  return conv.title === '新对话' && (conv.messageCount ?? 0) === 0 && !(conv.isArchived ?? false)
}

function sortConversations(list: ConversationSummary[]) {
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

function saveLastConversationId(id: string | null) {
  try {
    if (id) localStorage.setItem(LAST_CONVERSATION_KEY, id)
    else localStorage.removeItem(LAST_CONVERSATION_KEY)
  } catch {
    /* ignore */
  }
}

function loadLastConversationId() {
  try {
    return localStorage.getItem(LAST_CONVERSATION_KEY)
  } catch {
    return null
  }
}

export const useChatStore = defineStore('chat', () => {
  const initialized = ref(false)
  const conversations = ref<ConversationSummary[]>([])
  const currentId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const totalTokens = ref(0)
  const loadingConversations = ref(false)

  function applyConversationTokens(detail: { messages?: ChatMessage[]; totalTokens?: number }) {
    messages.value = detail.messages ?? []
    totalTokens.value =
      detail.totalTokens ??
      messages.value.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
  }

  function recalculateTotalTokens() {
    totalTokens.value = messages.value.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
  }
  const loadingMessages = ref(false)
  const creatingConversation = ref(false)
  const searchQuery = ref('')
  const abortController = ref<AbortController | null>(null)
  const selectedModelId = ref<string | null>(null)
  const availableModels = ref<AvailableModel[]>([])
  let ensureConversationPromise: Promise<ConversationSummary> | null = null

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
      conversations.value = sortConversations(await listConversations())
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
        conversations.value = sortConversations([local, ...conversations.value.filter((c) => c.id !== local.id)])
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
        await openDefaultConversation()
      }
    } else {
      await openDefaultConversation()
    }
    initialized.value = true
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
          detail.totalTokens ??
          serverMsgs.reduce((sum, m) => sum + (m.tokens ?? 0), 0)
      }
    } catch {
      /* keep local state */
    }
  }

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

  function upsertConversation(conv: ConversationSummary) {
    const idx = conversations.value.findIndex((c) => c.id === conv.id)
    if (idx >= 0) {
      conversations.value[idx] = { ...conversations.value[idx], ...conv }
    } else {
      conversations.value.unshift(conv)
    }
    conversations.value = sortConversations([...conversations.value])
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
      /* local fallback */
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
      const idx = conversations.value.findIndex(c => c.id === id)
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

  function appendUserMessage(content: string) {
    const id = uid()
    const msg: ChatMessage = {
      id,
      clientId: id,
      role: 'user',
      content,
      createdAt: nowIso()
    }
    messages.value.push(msg)
    return msg
  }

  function beginAssistantMessage() {
    const id = uid()
    const msg: ChatMessage = {
      id,
      clientId: id,
      role: 'assistant',
      content: '',
      createdAt: nowIso(),
      streaming: true,
      tools: []
    }
    messages.value.push(msg)
    return msg
  }

  function getStreamingMessage(): ChatMessage | undefined {
    return [...messages.value].reverse().find((m) => m.role === 'assistant' && m.streaming)
  }

  function appendDelta(delta: string) {
    const msg = getStreamingMessage()
    if (msg) msg.content += delta
  }

  function startTool(payload: SseToolStartPayload) {
    const msg = getStreamingMessage()
    if (!msg) return
    if (!msg.tools) msg.tools = []
    const tempId = `${payload.tool}_${msg.tools.length}`
    msg.tools.push({
      id: tempId,
      clientId: tempId,
      tool: payload.tool,
      input: payload.input,
      status: 'running'
    })
  }

  function endTool(payload: SseToolEndPayload) {
    const msg = getStreamingMessage()
    if (!msg?.tools?.length) return
    const tool = [...msg.tools].reverse().find((t) => t.tool === payload.tool && t.status === 'running')
    if (!tool) return
    tool.status = 'done'
    tool.output = payload.output
    tool.durationMs = payload.durationMs
  }

  function finishMessage() {
    const msg = getStreamingMessage()
    if (msg) msg.streaming = false
    streaming.value = false
    abortController.value = null

    if (currentId.value) {
      saveLastConversationId(currentId.value)
      const conv = conversations.value.find((c) => c.id === currentId.value)
      if (conv) {
        conv.messageCount = messages.value.length
        conv.updatedAt = nowIso()
        if (conv.title === '新对话') {
          const firstUser = messages.value.find((m) => m.role === 'user')
          if (firstUser) {
            conv.title = firstUser.content.slice(0, 24) + (firstUser.content.length > 24 ? '…' : '')
          }
        }
      }
      void syncCurrentConversation()
    }
  }

  function abortStream() {
    abortController.value?.abort()
    abortController.value = null
    streaming.value = false
    const msg = getStreamingMessage()
    if (msg) msg.streaming = false
  }

  function buildStreamHandlers() {
    return {
      onToken: (p: SseTokenPayload) => appendDelta(p.delta),
      onToolStart: (p: SseToolStartPayload) => startTool(p),
      onToolEnd: (p: SseToolEndPayload) => endTool(p),
      onUsage: (p: { totalTokens: number }) => {
        const msg = getStreamingMessage()
        if (msg) msg.tokens = p.totalTokens
        recalculateTotalTokens()
      },
      onDone: () => finishMessage(),
      onError: (err: { message: string; code?: string }) => {
        const msg =
          err.code === 'CONVERSATION_BUSY'
            ? '该会话正在生成中，请稍后再试'
            : err.message || '对话出错'
        ElMessage.error(msg)
        finishMessage()
      }
    }
  }

  function streamOptions(options?: { modelId?: string; kbId?: string; enableTools?: boolean }) {
    return {
      modelId: options?.modelId ?? selectedModelId.value ?? undefined,
      kbId: options?.kbId ?? undefined,
      enableTools: options?.enableTools ?? true
    }
  }

  async function sendMessage(content: string, options?: { modelId?: string; kbId?: string; enableTools?: boolean }) {
    const text = content.trim()
    if (!text || streaming.value) return null

    let convId = currentId.value
    if (!convId) {
      const conv = await startNewChat()
      convId = conv.id
    }

    appendUserMessage(text)
    beginAssistantMessage()
    streaming.value = true

    const controller = new AbortController()
    abortController.value = controller
    const opts = streamOptions(options)

    await createChatStream(
      {
        conversationId: convId,
        message: text,
        modelId: opts.modelId,
        kbId: opts.kbId,
        enableTools: opts.enableTools
      },
      buildStreamHandlers(),
      controller.signal
    )

    if (streaming.value) finishMessage()
    saveLastConversationId(convId)
    return convId
  }

  async function regenerateMessage(
    messageId?: string,
    options?: { modelId?: string; kbId?: string; enableTools?: boolean }
  ) {
    const convId = currentId.value
    if (!convId || streaming.value) return

    const target = messageId
      ? messages.value.find((m) => m.id === messageId)
      : [...messages.value].reverse().find((m) => m.role === 'assistant')

    if (!target || target.role !== 'assistant') return

    const targetIdx = messages.value.findIndex((m) => m.id === target.id)
    if (targetIdx >= 0) {
      messages.value = messages.value.slice(0, targetIdx)
      recalculateTotalTokens()
    }

    beginAssistantMessage()
    streaming.value = true

    const controller = new AbortController()
    abortController.value = controller
    const opts = streamOptions(options)

    await createRegenerateStream(
      {
        conversationId: convId,
        messageId: target.id,
        modelId: opts.modelId,
        kbId: opts.kbId,
        enableTools: opts.enableTools
      },
      buildStreamHandlers(),
      controller.signal
    )

    if (streaming.value) finishMessage()
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
