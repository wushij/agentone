/**
 * src/enums/chat.ts — 对话相关枚举
 */

export enum ChatStatusEnum {
  IDLE = 'idle',
  CONNECTING = 'connecting',
  STREAMING = 'streaming',
  COMPLETED = 'completed',
  ERROR = 'error',
}

export enum MessageRoleEnum {
  SYSTEM = 'system',
  USER = 'user',
  ASSISTANT = 'assistant',
  TOOL = 'tool',
}
