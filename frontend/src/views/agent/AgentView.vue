<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { getWorkflowSnapshot } from '@/api/conversation'
import { formatDateTime } from '@/utils/datetime'
import { useAgentStore } from '@/stores/agent'
import { useChatStore } from '@/stores/chat'
import { useNotifySocket } from '@/composables/useNotifySocket'

const route = useRoute()
const router = useRouter()
const agentStore = useAgentStore()
const chatStore = useChatStore()
const notifySocket = useNotifySocket()

const selectedConvId = ref<string>('')
const loadingSnapshot = ref(false)

const hasHistory = computed(() =>
  agentStore.orderedNodes.some((n) => n.state.status === 'success' || n.state.status === 'error')
)

const NODE_LABELS: Record<string, string> = {
  planner: '规划',
  researcher: '检索',
  tool: '工具',
  reviewer: '审阅',
  summarizer: '总结'
}

const STATUS_LABELS: Record<string, string> = {
  pending: '等待',
  running: '运行中',
  success: '完成',
  error: '失败'
}

const STATUS_TAG: Record<string, 'info' | 'primary' | 'success' | 'danger'> = {
  pending: 'info',
  running: 'primary',
  success: 'success',
  error: 'danger'
}

const progress = computed(() => {
  const nodes = agentStore.orderedNodes
  const done = nodes.filter((n) => n.state.status === 'success' || n.state.status === 'error').length
  return Math.round((done / nodes.length) * 100)
})

const runningNode = computed(() =>
  agentStore.orderedNodes.find((n) => n.state.status === 'running')
)

const totalElapsed = computed(() =>
  agentStore.orderedNodes.reduce((sum, n) => sum + (n.state.elapsedMs ?? 0), 0)
)

const metricCards = computed(() => {
  const current = runningNode.value
  return [
    {
      title: '执行进度',
      value: progress.value,
      unit: '%',
      color: '#4f46e5',
      trend: 'flat' as const,
      trendText: `已完成 ${agentStore.orderedNodes.filter((n) => n.state.status === 'success').length} / ${agentStore.orderedNodes.length} 步`
    },
    {
      title: '当前节点',
      value: current ? (NODE_LABELS[current.node] ?? current.node) : '—',
      unit: '',
      color: current ? '#0d9488' : '#64748b',
      trend: current ? ('up' as const) : ('flat' as const),
      trendText: current ? '正在执行' : hasHistory.value ? '显示上次执行结果' : '等待任务触发'
    },
    {
      title: '累计耗时',
      value: formatElapsed(totalElapsed.value, false),
      unit: formatElapsed(totalElapsed.value, true),
      color: '#7c3aed',
      trend: 'flat' as const,
      trendText: '各节点耗时合计'
    }
  ]
})

function formatElapsed(ms: number, unitOnly: boolean) {
  if (!ms) return unitOnly ? '' : '—'
  if (ms < 1000) return unitOnly ? 'ms' : String(ms)
  return unitOnly ? 's' : (ms / 1000).toFixed(1)
}

function subscribe(convId: string) {
  if (!convId) return
  notifySocket.subscribe([`agent:${convId}`])
}

function unsubscribe(convId: string) {
  if (convId) notifySocket.unsubscribe([`agent:${convId}`])
}

async function loadSnapshot(convId: string) {
  if (!convId) return
  loadingSnapshot.value = true
  agentStore.setActiveConversation(convId)
  try {
    const snapshot = await getWorkflowSnapshot(convId)
    if (selectedConvId.value === convId) {
      agentStore.applySnapshot(snapshot)
    }
  } catch {
    if (selectedConvId.value === convId) {
      agentStore.setActiveConversation(convId)
    }
  } finally {
    if (selectedConvId.value === convId) {
      loadingSnapshot.value = false
    }
  }
}

async function onConvChange(convId: string) {
  const prev = agentStore.activeConversationId
  if (prev && prev !== convId) unsubscribe(prev)
  selectedConvId.value = convId
  await loadSnapshot(convId)
  subscribe(convId)
  void router.replace({ query: { conversationId: convId } })
}

onMounted(async () => {
  await chatStore.fetchConversations()
  const fromQuery = route.query.conversationId as string | undefined
  const initial = fromQuery || chatStore.currentId || chatStore.conversations[0]?.id || ''
  if (initial) {
    selectedConvId.value = initial
    await loadSnapshot(initial)
    subscribe(initial)
  }
})

onUnmounted(() => {
  unsubscribe(agentStore.activeConversationId ?? '')
})

watch(
  () => route.query.conversationId,
  async (id) => {
    if (typeof id === 'string' && id && id !== selectedConvId.value) {
      await onConvChange(id)
    }
  }
)
</script>

<template>
  <div class="view-page agent-page">
    <PageHeader title="工作流监控" subtitle="LangGraph 节点状态实时推送">
      <template #action>
        <el-select
          v-model="selectedConvId"
          placeholder="选择会话"
          filterable
          class="conv-select"
          @change="onConvChange"
        >
          <el-option
            v-for="conv in chatStore.conversations"
            :key="conv.id"
            :label="conv.title"
            :value="conv.id"
          />
        </el-select>
      </template>
    </PageHeader>

    <el-card v-if="!selectedConvId" shadow="hover" class="empty-card">
      <el-empty description="请选择一个会话以监控工作流">
        <router-link to="/chat"><el-button type="primary">前往对话</el-button></router-link>
      </el-empty>
    </el-card>

    <template v-else>
      <div class="dashboard-metrics-panel">
        <div class="dashboard-metrics dashboard-metrics--3">
          <div
            v-for="card in metricCards"
            :key="card.title"
            class="dashboard-metric"
            :style="{ borderColor: card.color }"
          >
            <div class="dashboard-metric__label">{{ card.title }}</div>
            <div class="dashboard-metric__value-row">
              <span class="dashboard-metric__value" :style="{ color: card.color }">{{ card.value }}</span>
              <span v-if="card.unit" class="dashboard-metric__unit">{{ card.unit }}</span>
            </div>
            <div
              v-if="card.trendText"
              class="dashboard-metric__trend"
              :class="`dashboard-metric__trend--${card.trend}`"
            >
              {{ card.trendText }}
            </div>
          </div>
        </div>
      </div>

      <el-card shadow="hover" class="pipeline-card" v-loading="loadingSnapshot">
        <template #header>
          <div class="pipeline-card__header">
            <span>执行流水线</span>
            <div class="pipeline-card__meta">
              <el-tag v-if="agentStore.snapshotUpdatedAt" effect="plain" size="small" type="success">
                上次执行 {{ formatDateTime(agentStore.snapshotUpdatedAt) }}
              </el-tag>
              <el-tag effect="plain" size="small">共 {{ agentStore.orderedNodes.length }} 步</el-tag>
            </div>
          </div>
        </template>

        <div class="agent-pipeline">
          <template v-for="(item, index) in agentStore.orderedNodes" :key="item.node">
            <div
              class="pipeline-node"
              :class="[`is-${item.state.status}`, { 'is-active': item.state.status === 'running' }]"
            >
              <div class="pipeline-node__step">{{ index + 1 }}</div>
              <div class="pipeline-node__name">{{ NODE_LABELS[item.node] ?? item.node }}</div>
              <el-tag :type="STATUS_TAG[item.state.status] ?? 'info'" size="small" round>
                {{ STATUS_LABELS[item.state.status] ?? item.state.status }}
              </el-tag>
              <div v-if="item.state.tool || item.state.elapsedMs" class="pipeline-node__extra">
                <span v-if="item.state.tool">{{ item.state.tool }}</span>
                <span v-if="item.state.elapsedMs">{{ formatElapsed(item.state.elapsedMs, false) }}{{ formatElapsed(item.state.elapsedMs, true) }}</span>
              </div>
              <div v-if="item.state.error" class="pipeline-node__error">{{ item.state.error }}</div>
            </div>
            <div v-if="index < agentStore.orderedNodes.length - 1" class="pipeline-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </template>
        </div>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.agent-page {
  padding-bottom: 24px;
}

.conv-select {
  width: 240px;
}

.empty-card {
  border-radius: 16px;
}

.pipeline-card {
  border-radius: 16px;
}

.pipeline-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
}

.pipeline-card__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.agent-pipeline {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 8px 4px 4px;
  overflow-x: auto;
}

.pipeline-node {
  flex: 1;
  min-width: 148px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 14px 16px;
  border-radius: 16px;
  background: var(--ao-surface-muted);
  border: 1.5px solid var(--ao-surface-border);
  text-align: center;
  transition: all 0.25s ease;
}

.pipeline-node:hover {
  background: var(--ao-surface);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
}

.pipeline-node.is-running {
  border-color: rgba(59, 130, 246, 0.55);
  background: rgba(59, 130, 246, 0.1);
}

.pipeline-node.is-success {
  border-color: rgba(34, 197, 94, 0.45);
  background: rgba(34, 197, 94, 0.08);
}

.pipeline-node.is-error {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.08);
}

.pipeline-node__step {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--theme-primary-gradient);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pipeline-node.is-success .pipeline-node__step {
  background: linear-gradient(135deg, #22c55e, #10b981);
}

.pipeline-node.is-error .pipeline-node__step {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.pipeline-node__name {
  font-size: 15px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.pipeline-node__extra {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: var(--ao-text-muted);
}

.pipeline-node__error {
  font-size: 11px;
  color: var(--ao-danger);
  line-height: 1.4;
  max-width: 100%;
  word-break: break-word;
}

.pipeline-arrow {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 6px;
  color: var(--ao-text-muted);
  font-size: 18px;
}

@media (max-width: 900px) {
  .agent-pipeline {
    flex-direction: column;
    align-items: center;
  }

  .pipeline-node {
    width: 100%;
    max-width: 360px;
  }

  .pipeline-arrow {
    transform: rotate(90deg);
    padding: 4px 0;
  }
}
</style>
