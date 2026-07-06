import request from './request'
import { TOKEN_STORAGE_KEY } from './request'
import type { AvailableModel, ChatRegenerateRequest, ChatStreamRequest } from '@/types'

export type SseEventType = 'token' | 'tool_start' | 'tool_end' | 'usage' | 'done' | 'error'

export interface SseTokenPayload {
  conversationId: string
  messageId: string
  delta: string
}

export interface SseToolStartPayload {
  conversationId: string
  messageId: string
  tool: string
  input?: Record<string, unknown>
}

export interface SseToolEndPayload {
  conversationId: string
  messageId: string
  tool: string
  output?: string
  durationMs?: number
}

export interface SseUsagePayload {
  conversationId: string
  messageId: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
}

export interface SseDonePayload {
  conversationId: string
  messageId: string
  finishReason?: string
}

export interface SseErrorPayload {
  conversationId?: string
  messageId?: string
  code?: string
  message: string
}

export interface ChatStreamHandlers {
  onToken?: (payload: SseTokenPayload) => void
  onToolStart?: (payload: SseToolStartPayload) => void
  onToolEnd?: (payload: SseToolEndPayload) => void
  onUsage?: (payload: SseUsagePayload) => void
  onDone?: (payload: SseDonePayload) => void
  onError?: (payload: SseErrorPayload) => void
}

interface ParsedSseEvent {
  event: SseEventType
  data: string
}

function getApiBase(): string {
  return import.meta.env.VITE_API_BASE_URL || '/api'
}

function parseSseChunk(buffer: string): { events: ParsedSseEvent[]; rest: string } {
  const events: ParsedSseEvent[] = []
  const blocks = buffer.split('\n\n')
  const rest = blocks.pop() ?? ''

  for (const block of blocks) {
    if (!block.trim()) continue
    let event: SseEventType = 'token'
    const dataLines: string[] = []

    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim() as SseEventType
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim())
      }
    }

    if (dataLines.length) {
      events.push({ event, data: dataLines.join('\n') })
    }
  }

  return { events, rest }
}

function dispatchEvent(event: ParsedSseEvent, handlers: ChatStreamHandlers) {
  let payload: unknown
  try {
    payload = JSON.parse(event.data)
  } catch {
    handlers.onError?.({ message: 'SSE 数据解析失败' })
    return
  }

  switch (event.event) {
    case 'token':
      handlers.onToken?.(payload as SseTokenPayload)
      break
    case 'tool_start':
      handlers.onToolStart?.(payload as SseToolStartPayload)
      break
    case 'tool_end':
      handlers.onToolEnd?.(payload as SseToolEndPayload)
      break
    case 'usage':
      handlers.onUsage?.(payload as SseUsagePayload)
      break
    case 'done':
      handlers.onDone?.(payload as SseDonePayload)
      break
    case 'error':
      handlers.onError?.(payload as SseErrorPayload)
      break
    default:
      break
  }
}

export async function createChatStream(
  body: ChatStreamRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  return streamChatEndpoint('/chat/stream', body, handlers, signal)
}

export async function createRegenerateStream(
  body: ChatRegenerateRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  return streamChatEndpoint('/chat/regenerate', body, handlers, signal)
}

export function fetchAvailableModels() {
  return request.get<AvailableModel[]>('/models/available').then((r) => r.data)
}

async function streamChatEndpoint(
  path: string,
  body: ChatStreamRequest | ChatRegenerateRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  const response = await fetch(`${getApiBase()}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body),
    signal
  })

  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const json = await response.json()
      message = json.message || message
    } catch {
      /* ignore */
    }
    handlers.onError?.({ message })
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    handlers.onError?.({ message: '无法读取流式响应' })
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSseChunk(buffer)
      buffer = parsed.rest

      for (const event of parsed.events) {
        dispatchEvent(event, handlers)
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseChunk(`${buffer}\n\n`)
      for (const event of parsed.events) {
        dispatchEvent(event, handlers)
      }
    }
  } catch (error) {
    if (signal?.aborted) return
    const message = error instanceof Error ? error.message : '流式连接中断'
    handlers.onError?.({ message })
  } finally {
    reader.releaseLock()
  }
}

