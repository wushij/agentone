<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import CostMetricCards from '@/components/cost/CostMetricCards.vue'
import CostBreakdownCard from '@/components/cost/CostBreakdownCard.vue'
import { fetchCostSummary, fetchMyCost, type CostSummary, type MyCost } from '@/api/cost'

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
    <CostMetricCards :summary="summary" :mine="mine" :days="days" :loading="loading" />

    <!-- 空状态 -->
    <EmptyState
      v-if="isEmpty"
      title="暂无成本消费数据"
      description="在近 {{ days }} 天内尚未产生模型 Token 消耗记录"
    />

    <!-- 三栏成本细分统计 -->
    <div v-else v-loading="loading" class="breakdown-grid">
      <!-- 维度 1: 模型提供商 -->
      <CostBreakdownCard
        title="按模型提供商"
        subtitle="Provider 消耗分布"
        color-theme="purple"
        :rows="providerRows"
        :total-usd="summary?.totalUsd ?? 0"
      />

      <!-- 维度 2: 模型型号 -->
      <CostBreakdownCard
        title="按模型型号"
        subtitle="Model ID 消耗分布"
        color-theme="blue"
        :rows="modelRows"
        :total-usd="summary?.totalUsd ?? 0"
      />

      <!-- 维度 3: Agent 角色 -->
      <CostBreakdownCard
        title="按 Agent 角色"
        subtitle="Workflow Node 消耗分布"
        color-theme="amber"
        :rows="roleRows"
        :total-usd="summary?.totalUsd ?? 0"
        :role-labels="roleLabels"
      />
    </div>
  </div>
</template>

<style scoped>
.cost-center-page {
  padding-bottom: 40px;
}
.breakdown-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
}
</style>
