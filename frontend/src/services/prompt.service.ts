/**
 * src/services/prompt.service.ts — 提示词模板业务服务层
 */

import { fetchPrompts, createPrompt, deletePrompt } from '@/api/admin'

export class PromptService {
  static async getList(params?: any) {
    return fetchPrompts(params)
  }

  static async create(data: { name: string; content: string; type?: string }) {
    return createPrompt(data)
  }

  static async delete(name: string) {
    return deletePrompt(name)
  }
}
