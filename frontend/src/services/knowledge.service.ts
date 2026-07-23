/**
 * src/services/knowledge.service.ts — 知识库业务服务层
 */

import { fetchKnowledge, createKnowledge, deleteKnowledge } from '@/api/admin'

export class KnowledgeService {
  static async getList(params?: any) {
    return fetchKnowledge(params)
  }

  static async create(data: { name: string; description?: string }) {
    return createKnowledge(data)
  }

  static async delete(id: string) {
    return deleteKnowledge(id)
  }
}
