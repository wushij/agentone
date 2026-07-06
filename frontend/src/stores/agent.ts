import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { WorkflowSnapshot } from '@/api/conversation'

export interface AgentNodeStatus {
  conversationId: string
  node: string
  status: 'pending' | 'running' | 'success' | 'error'
  tool?: string
  elapsedMs?: number
  error?: string
  updatedAt: string
}

const NODE_ORDER = ['planner', 'researcher', 'tool', 'reviewer', 'summarizer']

export const useAgentStore = defineStore('agent', () => {
  const nodeStates = ref<Record<string, AgentNodeStatus>>({})
  const activeConversationId = ref<string | null>(null)
  const snapshotUpdatedAt = ref<string | null>(null)

  const orderedNodes = computed(() =>
    NODE_ORDER.map((node) => ({
      node,
      state: nodeStates.value[node] ?? {
        conversationId: activeConversationId.value ?? '',
        node,
        status: 'pending' as const,
        updatedAt: '',
      },
    }))
  )

  function setActiveConversation(id: string | null) {
    activeConversationId.value = id
    nodeStates.value = {}
    snapshotUpdatedAt.value = null
  }

  function applyStatus(payload: Record<string, unknown>) {
    const node = String(payload.node ?? '')
    if (!node) return
    nodeStates.value[node] = {
      conversationId: String(payload.conversationId ?? ''),
      node,
      status: (payload.status as AgentNodeStatus['status']) ?? 'running',
      tool: payload.tool ? String(payload.tool) : undefined,
      elapsedMs: typeof payload.elapsedMs === 'number' ? payload.elapsedMs : undefined,
      error: payload.error ? String(payload.error) : undefined,
      updatedAt: new Date().toISOString(),
    }
    if (payload.conversationId) {
      activeConversationId.value = String(payload.conversationId)
    }
  }

  function applySnapshot(snapshot: WorkflowSnapshot) {
    activeConversationId.value = snapshot.conversationId
    snapshotUpdatedAt.value = snapshot.updatedAt || null
    nodeStates.value = {}
    for (const item of snapshot.nodes) {
      nodeStates.value[item.node] = {
        conversationId: snapshot.conversationId,
        node: item.node,
        status: item.status,
        tool: item.tool,
        elapsedMs: item.elapsedMs,
        error: item.error,
        updatedAt: snapshot.updatedAt || new Date().toISOString(),
      }
    }
  }

  function reset() {
    nodeStates.value = {}
    activeConversationId.value = null
    snapshotUpdatedAt.value = null
  }

  return {
    nodeStates,
    activeConversationId,
    snapshotUpdatedAt,
    orderedNodes,
    setActiveConversation,
    applyStatus,
    applySnapshot,
    reset,
  }
})
