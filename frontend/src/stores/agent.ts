import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { WorkflowSnapshot } from '@/api/conversation'

export interface AgentNodeStatus {
  conversationId: string
  node: string
  status: 'pending' | 'running' | 'success' | 'error'
  label?: string
  detail?: string
  tool?: string
  elapsedMs?: number
  error?: string
  updatedAt: string
}

const NODE_ORDER = ['planner', 'researcher', 'tool', 'reviewer', 'summarizer']

/** Map stream/graph node names to pipeline slots shown in the monitor. */
const PIPELINE_NODE_MAP: Record<string, string> = {
  prepare: 'planner',
  rag: 'researcher',
  planner: 'planner',
  researcher: 'researcher',
  tool: 'tool',
  reviewer: 'reviewer',
  summarizer: 'summarizer',
  format: 'summarizer',
}

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
    const rawNode = String(payload.node ?? '')
    const node = PIPELINE_NODE_MAP[rawNode] ?? rawNode
    if (!node || !NODE_ORDER.includes(node)) return

    const prev = nodeStates.value[node]
    const elapsedMs =
      typeof payload.elapsedMs === 'number' && payload.elapsedMs > 0
        ? payload.elapsedMs
        : prev?.elapsedMs

    nodeStates.value[node] = {
      conversationId: String(payload.conversationId ?? prev?.conversationId ?? ''),
      node,
      status: (payload.status as AgentNodeStatus['status']) ?? 'running',
      label: payload.label ? String(payload.label) : prev?.label,
      detail: payload.detail ? String(payload.detail) : prev?.detail,
      tool: payload.tool ? String(payload.tool) : prev?.tool,
      elapsedMs,
      error: payload.error ? String(payload.error) : prev?.error,
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
        label: item.label,
        detail: item.detail,
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
