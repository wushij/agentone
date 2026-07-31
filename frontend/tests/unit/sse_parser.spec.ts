import { describe, expect, it } from 'vitest'
import { parseSseChunk } from '@/api/chat'

describe('parseSseChunk - SSE 数据流解包测试', () => {
  it('应成功解析完整的 token 与 step 事件', () => {
    const rawChunk =
      'event: step\ndata: {"conversationId":"c1","node":"planner","status":"running"}\n\n' +
      'event: token\ndata: {"conversationId":"c1","delta":"AgentOne"}\n\n'

    const { events, rest } = parseSseChunk(rawChunk)

    expect(events).toHaveLength(2)
    expect(events[0].event).toBe('step')
    expect(events[0].data).toContain('"planner"')
    expect(events[1].event).toBe('token')
    expect(events[1].data).toContain('"AgentOne"')
    expect(rest).toBe('')
  })

  it('当数据不完整（缺少结尾换行）时，应把未完成块保存在 rest 中', () => {
    const rawChunk =
      'event: token\ndata: {"delta":"Hello"}\n\n' +
      'event: token\ndata: {"delta":"World'

    const { events, rest } = parseSseChunk(rawChunk)

    expect(events).toHaveLength(1)
    expect(events[0].data).toContain('Hello')
    expect(rest).toBe('event: token\ndata: {"delta":"World')
  })
})
