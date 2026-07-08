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
  messages: Ref<ChatMessage[]>
  conversations: Ref<ConversationSummary[]>
  currentId: Ref<string | null>
  streaming: Ref<boolean>
  abortController: Ref<AbortController | null>
  selectedModelId: Ref<string | null>
  recalculateTotalTokens: () => void
  syncCurrentConversation: () => Promise<void>
  startNewChat: () => Promise<ConversationSummary>
}

export function createChatStreaming(ctx: ChatStreamContext) {
  function appendUserMessage(content: string) {
    const id = uid()
    const msg: ChatMessage = {
      id,
      clientId: id,
      role: 'user',
      content,
      createdAt: nowIso()
    }
    ctx.messages.value.push(msg)
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
      tools: [],
      steps: []
    }
    ctx.messages.value.push(msg)
    return msg
  }

  function getStreamingMessage(): ChatMessage | undefined {
    return [...ctx.messages.value].reverse().find((m) => m.role === 'assistant' && m.streaming)
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
    ctx.streaming.value = false
    ctx.abortController.value = null

    if (ctx.currentId.value) {
      saveLastConversationId(ctx.currentId.value)
      const conv = ctx.conversations.value.find((c) => c.id === ctx.currentId.value)
      if (conv) {
        conv.messageCount = ctx.messages.value.length
        conv.updatedAt = nowIso()
      }
      void ctx.syncCurrentConversation()
    }
  }

  function abortStream() {
    ctx.abortController.value?.abort()
    ctx.abortController.value = null
    ctx.streaming.value = false
    const msg = getStreamingMessage()
    if (msg) msg.streaming = false
  }

  function updateStep(payload: SseStepPayload) {
    const msg = getStreamingMessage()
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

  function buildStreamHandlers() {
    return {
      onToken: (p: SseTokenPayload) => appendDelta(p.delta),
      onStep: (p: SseStepPayload) => updateStep(p),
      onToolStart: (p: SseToolStartPayload) => startTool(p),
      onToolEnd: (p: SseToolEndPayload) => endTool(p),
      onUsage: (p: { totalTokens: number }) => {
        const msg = getStreamingMessage()
        if (msg) msg.tokens = p.totalTokens
        ctx.recalculateTotalTokens()
      },
      onTitle: (p: { conversationId: string; title: string }) => {
        const conv = ctx.conversations.value.find((c) => c.id === p.conversationId)
        if (conv && p.title) conv.title = p.title
      },
      onDone: () => finishMessage(),
      onError: (err: { message: string; code?: string }) => {
        const message =
          err.code === 'CONVERSATION_BUSY'
            ? '该会话正在生成中，请稍后再试'
            : err.message || '对话出错'
        ElMessage.error(message)
        finishMessage()
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
    if (!text || ctx.streaming.value) return null

    let convId = ctx.currentId.value
    if (!convId) {
      const conv = await ctx.startNewChat()
      convId = conv.id
    }

    appendUserMessage(text)
    beginAssistantMessage()
    ctx.streaming.value = true

    const controller = new AbortController()
    ctx.abortController.value = controller
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
      buildStreamHandlers(),
      controller.signal
    )

    if (ctx.streaming.value) finishMessage()
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
    if (!convId || ctx.streaming.value) return

    const target = messageId
      ? ctx.messages.value.find((m) => m.id === messageId || m.clientId === messageId)
      : [...ctx.messages.value].reverse().find((m) => m.role === 'assistant')

    if (!target || target.role !== 'assistant') {
      ElMessage.warning('找不到要重新生成的消息')
      return
    }

    const targetIdx = ctx.messages.value.findIndex((m) => m.id === target.id)
    if (targetIdx >= 0) {
      ctx.messages.value = ctx.messages.value.slice(0, targetIdx)
      ctx.recalculateTotalTokens()
    }

    beginAssistantMessage()
    ctx.streaming.value = true

    const controller = new AbortController()
    ctx.abortController.value = controller
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
      buildStreamHandlers(),
      controller.signal
    )

    if (ctx.streaming.value) finishMessage()
  }

  return {
    appendUserMessage,
    beginAssistantMessage,
    abortStream,
    sendMessage,
    regenerateMessage
  }
}
