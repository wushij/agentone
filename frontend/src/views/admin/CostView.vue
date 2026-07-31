<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Coin, Connection, Cpu, Select, TrendCharts, User, Wallet } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { fetchCostSummary, fetchMyCost, type CostGroupRow, type CostSummary, type MyCost } from '@/api/cost'

const loading = ref(false)
const days = ref(7)
const summary = ref<CostSummary | null>(null)
const mine = ref<MyCost | null>(null)

const dayOptions = [
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 },
  { label: '近 90 天', value: 90 }
]

async function load() {
  loading.value = true
  try {
    const [s, m] = await Promise.all([fetchCostSummary(days.value), fetchMyCost().catch(() => null)])
    summary.value = s
    mine.value = m
  } catch {
    summary.value = null
  } finally {
    loading.value = false
  }
}

function fmtUsd(v: number | undefined): string {
  return `$${(v ?? 0).toFixed(4)}`
}

function getPercent(part: number, total: number | undefined): string {
  if (!total || total <= 0) return '0.0'
  return ((part / total) * 100).toFixed(1)
}

function maxCost(rows: CostGroupRow[]): number {
  return rows.reduce((mx, r) => Math.max(mx, r.costUsd), 0) || 1
}

const providerRows = computed(() => summary.value?.byProvider ?? [])
const modelRows = computed(() => summary.value?.byModel ?? [])
const roleRows = computed(() => summary.value?.byAgentRole ?? [])
const isEmpty = computed(() => !loading.value && (summary.value?.totalUsd ?? 0) === 0)

const roleLabels: Record<string, string> = {
  react: 'ReAct 循环',
  summary: '总结生成',
  planner: '任务规划',
  reviewer: '结果审阅',
  embedding: '向量化',
  unknown: '其他调用'
}

onMounted(load)
</script>

<template>
  <div class="view-page cost-center-page">
    <PageHeader title="成本中心" subtitle="按用户 / 模型 / Agent 角色的 Token 成本出账与账单统计">
      <template #action>
        <el-select v-model="days" class="cost-days-select" style="width: 120px" @change="load">
          <el-option v-for="opt in dayOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
      </template>
    </PageHeader>

    <!-- 顶部概览指标面板 -->
    <div v-loading="loading" class="metrics-grid">
      <!-- 总成本卡片 -->
      <div class="ao-card metric-card metric-card--primary">
        <div class="metric-card__header">
          <div class="metric-card__icon-box metric-card__icon--indigo">
            <el-icon><Wallet /></el-icon>
          </div>
          <span class="metric-card__badge">周期成本</span>
        </div>
        <div class="metric-card__body">
          <span class="metric-card__label">总成本（近 {{ days }} 天）</span>
          <div class="metric-card__val-row">
            <span class="metric-card__unit">$</span>
            <span class="metric-card__val">{{ (summary?.totalUsd ?? 0).toFixed(4) }}</span>
          </div>
        </div>
        <div class="metric-card__footer">
          <el-icon><TrendCharts /></el-icon>
          <span>包含 LLM Token + 向量化存储费用</span>
        </div>
      </div>

      <!-- 今日用量卡片 -->
      <div class="ao-card metric-card metric-card--emerald">
        <div class="metric-card__header">
          <div class="metric-card__icon-box metric-card__icon--emerald">
            <el-icon><Coin /></el-icon>
          </div>
          <span
            class="metric-card__badge"
            :class="mine && mine.dailyLimitUsd > 0 ? 'badge--warning' : 'badge--info'"
          >
            {{ mine && mine.dailyLimitUsd > 0 ? '受额度限制' : '不限制额度' }}
          </span>
        </div>
        <div class="metric-card__body">
          <span class="metric-card__label">我的今日用量</span>
          <div class="metric-card__val-row">
            <span class="metric-card__unit">$</span>
            <span class="metric-card__val">{{ (mine?.todayUsd ?? 0).toFixed(4) }}</span>
          </div>
        </div>
        <div class="metric-card__footer">
          <template v-if="mine && mine.dailyLimitUsd > 0">
            <div class="limit-info">
              <span>每日限额: {{ fmtUsd(mine.dailyLimitUsd) }}</span>
              <el-progress
                :percentage="Math.min(100, Math.round(((mine?.todayUsd ?? 0) / mine.dailyLimitUsd) * 100))"
                :show-text="false"
                :stroke-width="6"
                class="limit-progress"
              />
            </div>
          </template>
          <template v-else>
            <el-icon><Select /></el-icon>
            <span>未设置个人单日限额上限</span>
          </template>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <EmptyState
      v-if="isEmpty"
      title="暂无成本记录"
      description="发生大模型或向量化 API 调用后，将在此自动按维度计费出账"
    />

    <!-- 多维度成本分布图表面板 -->
    <div v-else class="cost-breakdown-grid">
      <!-- 按提供商 -->
      <div class="ao-card breakdown-card">
        <div class="breakdown-card__header">
          <div class="header-title">
            <div class="title-icon icon--purple">
              <el-icon><Connection /></el-icon>
            </div>
            <h3>按提供商分布</h3>
          </div>
          <span class="header-count">{{ providerRows.length }} 个提供商</span>
        </div>
        <div class="breakdown-card__body">
          <div v-for="row in providerRows" :key="row.key" class="cost-item">
            <div class="cost-item__info">
              <span class="cost-item__name" :title="row.key">{{ row.key }}</span>
              <span class="cost-item__percent">{{ getPercent(row.costUsd, summary?.totalUsd) }}%</span>
            </div>
            <div class="cost-item__bar-wrapper">
              <div class="cost-item__track">
                <div
                  class="cost-item__fill fill--purple"
                  :style="{ width: `${(row.costUsd / maxCost(providerRows)) * 100}%` }"
                />
              </div>
              <span class="cost-item__amt">{{ fmtUsd(row.costUsd) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 按模型 -->
      <div class="ao-card breakdown-card">
        <div class="breakdown-card__header">
          <div class="header-title">
            <div class="title-icon icon--blue">
              <el-icon><Cpu /></el-icon>
            </div>
            <h3>按模型分布</h3>
          </div>
          <span class="header-count">{{ modelRows.length }} 个模型</span>
        </div>
        <div class="breakdown-card__body">
          <div v-for="row in modelRows" :key="row.key" class="cost-item">
            <div class="cost-item__info">
              <span class="cost-item__name" :title="row.key || '未知'">{{ row.key || '未知' }}</span>
              <span class="cost-item__percent">{{ getPercent(row.costUsd, summary?.totalUsd) }}%</span>
            </div>
            <div class="cost-item__bar-wrapper">
              <div class="cost-item__track">
                <div
                  class="cost-item__fill fill--blue"
                  :style="{ width: `${(row.costUsd / maxCost(modelRows)) * 100}%` }"
                />
              </div>
              <span class="cost-item__amt">{{ fmtUsd(row.costUsd) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 按 Agent 角色 -->
      <div class="ao-card breakdown-card">
        <div class="breakdown-card__header">
          <div class="header-title">
            <div class="title-icon icon--amber">
              <el-icon><User /></el-icon>
            </div>
            <h3>按 Agent 角色</h3>
          </div>
          <span class="header-count">{{ roleRows.length }} 个角色</span>
        </div>
        <div class="breakdown-card__body">
          <div v-for="row in roleRows" :key="row.key" class="cost-item">
            <div class="cost-item__info">
              <span class="cost-item__name" :title="roleLabels[row.key] || row.key">
                {{ roleLabels[row.key] || row.key || '其他' }}
              </span>
              <span class="cost-item__percent">{{ getPercent(row.costUsd, summary?.totalUsd) }}%</span>
            </div>
            <div class="cost-item__bar-wrapper">
              <div class="cost-item__track">
                <div
                  class="cost-item__fill fill--amber"
                  :style="{ width: `${(row.costUsd / maxCost(roleRows)) * 100}%` }"
                />
              </div>
              <span class="cost-item__amt">{{ fmtUsd(row.costUsd) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cost-center-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 顶部指标卡片 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.metric-card {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px 24px;
  border-radius: 20px;
  border: 1px solid var(--ao-surface-border, rgba(226, 232, 240, 0.8));
  background: var(--ao-surface, #ffffff);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
}

.metric-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.metric-card__icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  font-size: 20px;
}

.metric-card__icon--indigo {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(79, 70, 229, 0.25));
  color: #6366f1;
}

.metric-card__icon--emerald {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.25));
  color: #10b981;
}

.metric-card__badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  background: var(--ao-surface-muted, #f1f5f9);
  color: var(--ao-text-secondary, #64748b);
}

.badge--warning {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.badge--info {
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}

.metric-card__body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-card__label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ao-text-secondary, #64748b);
}

.metric-card__val-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.metric-card__unit {
  font-size: 20px;
  font-weight: 700;
  color: var(--ao-text-primary, #0f172a);
}

.metric-card__val {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--ao-text-primary, #0f172a);
}

.metric-card--primary .metric-card__val {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.metric-card--emerald .metric-card__val {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.metric-card__footer {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--ao-surface-border, #e2e8f0);
  font-size: 12px;
  color: var(--ao-text-muted, #94a3b8);
}

.limit-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.limit-progress {
  width: 80px;
}

/* 分布折算多列卡片 */
.cost-breakdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.breakdown-card {
  display: flex;
  flex-direction: column;
  padding: 22px 24px;
  border-radius: 20px;
  border: 1px solid var(--ao-surface-border, rgba(226, 232, 240, 0.8));
  background: var(--ao-surface, #ffffff);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.breakdown-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--ao-text-primary, #0f172a);
}

.title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 16px;
}

.icon--purple {
  background: rgba(139, 92, 246, 0.12);
  color: #8b5cf6;
}

.icon--blue {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.icon--amber {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.header-count {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 12px;
  background: var(--ao-surface-muted, #f1f5f9);
  color: var(--ao-text-secondary, #64748b);
}

.breakdown-card__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cost-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cost-item__info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}

.cost-item__name {
  font-weight: 600;
  color: var(--ao-text-primary, #1e293b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.cost-item__percent {
  font-size: 12px;
  font-weight: 500;
  color: var(--ao-text-muted, #94a3b8);
}

.cost-item__bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cost-item__track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: var(--ao-surface-muted, #f1f5f9);
  overflow: hidden;
}

.cost-item__fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fill--purple {
  background: linear-gradient(90deg, #8b5cf6 0%, #c084fc 100%);
}

.fill--blue {
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
}

.fill--amber {
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
}

.cost-item__amt {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ao-text-primary, #0f172a);
  min-width: 68px;
  text-align: right;
}

/* 深色模式兼容 */
:deep(html.dark) .metric-card,
:deep(html.dark) .breakdown-card {
  background: var(--ao-surface, #1e293b) !important;
  border-color: var(--ao-surface-border, rgba(255, 255, 255, 0.08)) !important;
}

:deep(html.dark) .metric-card__unit,
:deep(html.dark) .header-title h3,
:deep(html.dark) .cost-item__name,
:deep(html.dark) .cost-item__amt {
  color: #f8fafc !important;
}

:deep(html.dark) .cost-item__track {
  background: rgba(255, 255, 255, 0.06) !important;
}

:deep(html.dark) .metric-card__badge,
:deep(html.dark) .header-count {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #94a3b8 !important;
}
</style>
