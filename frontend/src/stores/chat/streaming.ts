import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createChatStream,
  createRegenerateStream,
  type SseTokenPayload,
  type SseStepPayload,
  type SseToolEndPayload,
  type SseToolStartPayload
} from '@/api/chat'
import type { ChatMessage, ConversationSummary, WorkflowStep } from '@/types'
import { nowIso, saveLastConversationId, uid } from './helpers'

export interface ChatStreamContext {
  conversations: Ref<ConversationSummary[]>
  currentId: Ref<string | null>
  ensureMessageList: (convId: string) => ChatMessage[]
  isConversationStreaming: (convId: string) => boolean
  setConversationStreaming: (convId: string, on: boolean) => void
  getAbortController: (convId: string) => AbortController | undefined
  setAbortController: (convId: string, controller: AbortController | null) => void
  selectedModelId: Ref<string | null>
  recalculateTotalTokens: () => void
  syncConversation: (convId: string) => Promise<void>
  startNewChat: () => Promise<ConversationSummary>
}

export function createChatStreaming(ctx: ChatStreamContext) {
  function appendUserMessage(convId: string, content: string) {
    const list = ctx.ensureMessageList(convId)
    const id = uid()
    const msg: ChatMessage = {
      id,
      clientId: id,
      role: 'user',
      content,
      createdAt: nowIso()
    }
    list.push(msg)
    return msg
  }

  function beginAssistantMessage(convId: string) {
    const list = ctx.ensureMessageList(convId)
    const id = uid()
    const msg: ChatMessage = {
      id,
      clientId: id,
      role: 'assistant',
      content: '',
      createdAt: nowIso(),
      streaming: true,
      tools: [],
      steps: []
    }
    list.push(msg)
    return msg
  }

  function getStreamingMessage(convId: string): ChatMessage | undefined {
    return [...ctx.ensureMessageList(convId)]
      .reverse()
      .find((m) => m.role === 'assistant' && m.streaming)
  }

  function appendDelta(convId: string, delta: string) {
    const msg = getStreamingMessage(convId)
    if (msg) msg.content += delta
    ctx.recalculateTotalTokens()
  }

  function startTool(convId: string, payload: SseToolStartPayload) {
    const msg = getStreamingMessage(convId)
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

  function endTool(convId: string, payload: SseToolEndPayload) {
    const msg = getStreamingMessage(convId)
    if (!msg?.tools?.length) return
    const tool = [...msg.tools].reverse().find((t) => t.tool === payload.tool && t.status === 'running')
    if (!tool) return
    tool.status = 'done'
    tool.output = payload.output
    tool.durationMs = payload.durationMs
  }

  function finishMessage(convId: string) {
    const msg = getStreamingMessage(convId)
    if (msg) msg.streaming = false
    ctx.setConversationStreaming(convId, false)
    ctx.setAbortController(convId, null)

    saveLastConversationId(convId)
    const conv = ctx.conversations.value.find((c) => c.id === convId)
    const list = ctx.ensureMessageList(convId)
    if (conv) {
      conv.messageCount = list.length
      conv.updatedAt = nowIso()
    }
    ctx.recalculateTotalTokens()
    void ctx.syncConversation(convId)
  }

  function abortStream(convId?: string) {
    const id = convId ?? ctx.currentId.value
    if (!id) return
    ctx.getAbortController(id)?.abort()
    ctx.setAbortController(id, null)
    ctx.setConversationStreaming(id, false)
    const msg = getStreamingMessage(id)
    if (msg) msg.streaming = false
  }

  function updateStep(convId: string, payload: SseStepPayload) {
    const msg = getStreamingMessage(convId)
    if (!msg) return
    if (!msg.steps) msg.steps = []
    const label = payload.label || payload.node
    const next: WorkflowStep = {
      node: payload.node,
      label,
      status: payload.status,
      tool: payload.tool,
      elapsedMs: payload.elapsedMs,
      error: payload.error
    }
    const idx = msg.steps.findIndex((s) => s.node === payload.node)
    if (idx >= 0) {
      msg.steps[idx] = { ...msg.steps[idx], ...next }
    } else {
      msg.steps.push(next)
    }
  }

  function buildStreamHandlers(convId: string) {
    return {
      onToken: (p: SseTokenPayload) => appendDelta(convId, p.delta),
      onStep: (p: SseStepPayload) => updateStep(convId, p),
      onToolStart: (p: SseToolStartPayload) => startTool(convId, p),
      onToolEnd: (p: SseToolEndPayload) => endTool(convId, p),
      onUsage: (p: { totalTokens: number }) => {
        const msg = getStreamingMessage(convId)
        if (msg) msg.tokens = p.totalTokens
        ctx.recalculateTotalTokens()
      },
      onTitle: (p: { conversationId: string; title: string }) => {
        const conv = ctx.conversations.value.find((c) => c.id === p.conversationId)
        if (conv && p.title) conv.title = p.title
      },
      onDone: () => finishMessage(convId),
      onError: (err: { message: string; code?: string }) => {
        const message =
          err.code === 'CONVERSATION_BUSY'
            ? '该会话正在生成中，请稍后再试'
            : err.message || '对话出错'
        ElMessage.error(message)
        finishMessage(convId)
      }
    }
  }

  function streamOptions(options?: {
    modelId?: string
    kbIds?: string[]
    kbMode?: 'generate' | 'retrieve'
    enableTools?: boolean
  }) {
    const kbIds = (options?.kbIds ?? []).filter(Boolean)
    return {
      modelId: options?.modelId ?? ctx.selectedModelId.value ?? undefined,
      kbIds: kbIds.length ? kbIds : undefined,
      kbMode: options?.kbMode,
      enableTools: options?.enableTools ?? true
    }
  }

  async function sendMessage(
    content: string,
    options?: {
      modelId?: string
      kbIds?: string[]
      kbMode?: 'generate' | 'retrieve'
      enableTools?: boolean
    }
  ) {
    const text = content.trim()
    if (!text) return null

    let convId = ctx.currentId.value
    if (!convId) {
      const conv = await ctx.startNewChat()
      convId = conv.id
    }

    if (ctx.isConversationStreaming(convId)) return null

    appendUserMessage(convId, text)
    beginAssistantMessage(convId)
    ctx.recalculateTotalTokens()
    ctx.setConversationStreaming(convId, true)

    const controller = new AbortController()
    ctx.setAbortController(convId, controller)
    const opts = streamOptions(options)

    await createChatStream(
      {
        conversationId: convId,
        message: text,
        modelId: opts.modelId,
        kbIds: opts.kbIds,
        kbMode: opts.kbMode,
        enableTools: opts.enableTools
      },
      buildStreamHandlers(convId),
      controller.signal
    )

    if (ctx.isConversationStreaming(convId)) finishMessage(convId)
    saveLastConversationId(convId)
    return convId
  }

  async function regenerateMessage(
    messageId: string | undefined,
    options?: {
      modelId?: string
      kbIds?: string[]
      kbMode?: 'generate' | 'retrieve'
      enableTools?: boolean
    }
  ) {
    const convId = ctx.currentId.value
    if (!convId || ctx.isConversationStreaming(convId)) return

    const list = ctx.ensureMessageList(convId)
    const target = messageId
      ? list.find((m) => m.id === messageId || m.clientId === messageId)
      : [...list].reverse().find((m) => m.role === 'assistant')

    if (!target || target.role !== 'assistant') {
      ElMessage.warning('找不到要重新生成的消息')
      return
    }

    const targetIdx = list.findIndex((m) => m.id === target.id)
    if (targetIdx >= 0) {
      list.splice(targetIdx)
      ctx.recalculateTotalTokens()
    }

    beginAssistantMessage(convId)
    ctx.setConversationStreaming(convId, true)

    const controller = new AbortController()
    ctx.setAbortController(convId, controller)
    const opts = streamOptions(options)

    await createRegenerateStream(
      {
        conversationId: convId,
        messageId: target.id,
        modelId: opts.modelId,
        kbIds: opts.kbIds,
        kbMode: opts.kbMode,
        enableTools: opts.enableTools
      },
      buildStreamHandlers(convId),
      controller.signal
    )

    if (ctx.isConversationStreaming(convId)) finishMessage(convId)
  }

  return {
    appendUserMessage,
    beginAssistantMessage,
    abortStream,
    sendMessage,
    regenerateMessage
  }
}
