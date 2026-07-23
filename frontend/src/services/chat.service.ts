/**
 * src/services/chat.service.ts — 对话业务服务层
 */

import { createChatStream } from '@/api/chat'
import { listConversations, createConversation, deleteConversation } from '@/api/conversation'

export class ChatService {
  /**
   * 发送流式对话消息
   */
  static async sendStreamMessage(
    payload: { conversationId: string; message: string; modelId?: string },
    options: {
      onToken?: (delta: string) => void
      onStep?: (step: any) => void
      onDone?: () => void
      onError?: (err: Error) => void
      signal?: AbortSignal
    }
  ) {
    return createChatStream(
      {
        conversationId: payload.conversationId,
        message: payload.message,
        modelId: payload.modelId,
      },
      {
        onToken: (p) => options.onToken?.(p.delta),
        onStep: (s) => options.onStep?.(s),
        onDone: () => options.onDone?.(),
        onError: (e) => options.onError?.(new Error(e.message)),
      },
      options.signal
    )
  }

  /**
   * 获取历史会话列表
   */
  static async fetchHistory(page = 1, pageSize = 20) {
    return listConversations({ page, size: pageSize })
  }

  /**
   * 新建会话
   */
  static async newConversation(title?: string) {
    return createConversation(title ? { title } : undefined)
  }

  /**
   * 删除会话
   */
  static async removeConversation(id: string) {
    return deleteConversation(id)
  }
}
