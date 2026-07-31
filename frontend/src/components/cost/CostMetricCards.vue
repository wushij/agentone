<script setup lang="ts">
import { Coin, Select, TrendCharts, Wallet } from '@element-plus/icons-vue'
import type { CostSummary, MyCost } from '@/api/cost'

defineProps<{
  summary: CostSummary | null
  mine: MyCost | null
  days: number
  loading: boolean
}>()

function fmtUsd(v: number | undefined): string {
  return `$${(v ?? 0).toFixed(4)}`
}
</script>

<template>
  <div v-loading="loading" class="metrics-grid">
    <!-- 总成本卡片 -->
    <div class="ao-card metric-card">
      <div class="metric-card__top">
        <div class="metric-card__header-left">
          <div class="metric-card__icon icon--indigo">
            <el-icon><Wallet /></el-icon>
          </div>
          <div>
            <span class="metric-card__label">总成本（近 {{ days }} 天）</span>
            <div class="metric-card__val-row">
              <span class="metric-card__unit">$</span>
              <span class="metric-card__val">{{ (summary?.totalUsd ?? 0).toFixed(4) }}</span>
            </div>
          </div>
        </div>
        <span class="metric-card__badge">周期成本</span>
      </div>

      <div class="metric-card__footer">
        <el-icon><TrendCharts /></el-icon>
        <span>包含 LLM Token + 向量化存储费用</span>
      </div>
    </div>

    <!-- 今日用量卡片 -->
    <div class="ao-card metric-card">
      <div class="metric-card__top">
        <div class="metric-card__header-left">
          <div class="metric-card__icon icon--emerald">
            <el-icon><Coin /></el-icon>
          </div>
          <div>
            <span class="metric-card__label">我的今日用量</span>
            <div class="metric-card__val-row">
              <span class="metric-card__unit">$</span>
              <span class="metric-card__val">{{ (mine?.todayUsd ?? 0).toFixed(4) }}</span>
            </div>
          </div>
        </div>
        <span
          class="metric-card__badge"
          :class="mine && mine.dailyLimitUsd > 0 ? 'badge--warning' : 'badge--info'"
        >
          {{ mine && mine.dailyLimitUsd > 0 ? '受额度限制' : '不限制额度' }}
        </span>
      </div>

      <div class="metric-card__footer">
        <template v-if="mine && mine.dailyLimitUsd > 0">
          <div class="limit-info">
            <span>每日限额: {{ fmtUsd(mine.dailyLimitUsd) }}</span>
            <el-progress
              :percentage="Math.min(100, Math.round(((mine?.todayUsd ?? 0) / mine.dailyLimitUsd) * 100))"
              :show-text="false"
              :stroke-width="5"
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
</template>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  position: relative;
  padding: 16px 20px;
  border-radius: 16px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  transition: all 0.25s ease;
}
.metric-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.3);
}

.metric-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.metric-card__header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.metric-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.icon--indigo {
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}
.icon--emerald {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.metric-card__label {
  font-size: 12px;
  color: var(--ao-text-muted);
  display: block;
  margin-bottom: 2px;
}

.metric-card__val-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.metric-card__unit {
  font-size: 15px;
  font-weight: 700;
  color: var(--ao-text-muted);
}
.metric-card__val {
  font-size: 24px;
  font-weight: 800;
  color: var(--ao-text-primary);
  line-height: 1.1;
  letter-spacing: -0.5px;
}

.metric-card__badge {
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  background: var(--ao-panel-border, rgba(255, 255, 255, 0.08));
  color: var(--ao-text-secondary);
  white-space: nowrap;
}
.badge--warning {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}
.badge--info {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.metric-card__footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px dashed var(--ao-panel-border, rgba(255, 255, 255, 0.08));
  font-size: 12px;
  color: var(--ao-text-muted);
}

.limit-info {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.limit-progress {
  flex: 1;
}
</style>
