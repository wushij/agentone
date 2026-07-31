import { describe, expect, it } from 'vitest'
import { estimateMessageTokens, isEmptyNewConversation, nowIso, sortConversations, uid } from '@/stores/chat/helpers'
import type { ConversationSummary } from '@/types'

import { renderMarkdown } from '@/utils/markdown'

describe('chat/helpers - 辅助算法与 Token 估算测试', () => {
  it('renderMarkdown() 应将图片 Markdown 正确渲染为 img 标签', () => {
    const input = '![壁纸.jpg](/api/v1/files/file_123/download) 请分析'
    const html = renderMarkdown(input)
    expect(html).toContain('<img src="/api/v1/files/file_123/download" alt="壁纸.jpg"')
  })
  it('uid() 应按前缀生成带时间戳的唯一 ID', () => {
    const id1 = uid('conv')
    const id2 = uid('conv')
    expect(id1).toContain('conv_')
    expect(id1).not.toBe(id2)
  })

  it('nowIso() 应生成标准 ISO 8601 时间戳', () => {
    const iso = nowIso()
    expect(iso).toMatch(/^\d{4}-\d{2}-\d{2}T/)
  })

  it('estimateMessageTokens() 应按约 4 字符 1 Token 估算', () => {
    expect(estimateMessageTokens('')).toBe(0)
    expect(estimateMessageTokens('AgentOne')).toBe(2) // 8 chars / 4 = 2
    expect(estimateMessageTokens('123456789012')).toBe(3) // 12 chars / 4 = 3
  })

  it('isEmptyNewConversation() 应准确识别空新对话', () => {
    const emptyConv: ConversationSummary = {
      id: 'c1',
      title: '新对话',
      messageCount: 0,
      updatedAt: nowIso(),
      isArchived: false
    }
    expect(isEmptyNewConversation(emptyConv)).toBe(true)

    const filledConv: ConversationSummary = {
      id: 'c2',
      title: '架构分析',
      messageCount: 5,
      updatedAt: nowIso()
    }
    expect(isEmptyNewConversation(filledConv)).toBe(false)
  })

  it('sortConversations() 应将最新更新的对话置顶排序', () => {
    const older: ConversationSummary = {
      id: 'c1',
      title: '旧对话',
      messageCount: 2,
      updatedAt: '2026-01-01T00:00:00Z'
    }
    const newer: ConversationSummary = {
      id: 'c2',
      title: '新对话',
      messageCount: 3,
      updatedAt: '2026-06-01T00:00:00Z'
    }
    const sorted = sortConversations([older, newer])
    expect(sorted[0].id).toBe('c2')
  })
})
