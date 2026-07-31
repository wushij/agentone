<script setup lang="ts">
import type { CostGroupRow } from '@/api/cost'

defineProps<{
  title: string
  subtitle: string
  colorTheme?: 'purple' | 'blue' | 'amber'
  rows: CostGroupRow[]
  totalUsd: number
  roleLabels?: Record<string, string>
}>()

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
</script>

<template>
  <div class="ao-card breakdown-card">
    <div class="breakdown-card__header">
      <h3 class="breakdown-card__title">{{ title }}</h3>
      <p class="breakdown-card__sub">{{ subtitle }}</p>
    </div>

    <div class="breakdown-card__body">
      <div v-if="!rows.length" class="empty-rows">暂无数据记录</div>
      <div v-else class="rows-list">
        <div v-for="r in rows" :key="r.groupKey" class="cost-row">
          <div class="cost-row__meta">
            <span class="cost-row__name">
              {{ roleLabels?.[r.groupKey] || r.groupKey || '未知' }}
            </span>
            <span class="cost-row__val">{{ fmtUsd(r.costUsd) }}</span>
          </div>

          <div class="cost-row__bar-track">
            <div
              class="cost-row__bar-fill"
              :class="`bar--${colorTheme ?? 'purple'}`"
              :style="{ width: `${(r.costUsd / maxCost(rows)) * 100}%` }"
            />
          </div>

          <div class="cost-row__sub-meta">
            <span>{{ (r.tokens ?? 0).toLocaleString() }} Tokens</span>
            <span class="cost-row__pct">{{ getPercent(r.costUsd, totalUsd) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.breakdown-card {
  padding: 24px;
  border-radius: 20px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
}
.breakdown-card__header {
  margin-bottom: 20px;
}
.breakdown-card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ao-text-primary);
  line-height: 1.3;
}
.breakdown-card__sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--ao-text-muted);
}
.empty-rows {
  padding: 32px 0;
  text-align: center;
  font-size: 13px;
  color: var(--ao-text-muted);
}
.rows-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.cost-row__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  margin-bottom: 6px;
}
.cost-row__name {
  font-weight: 600;
  color: var(--ao-text-primary);
}
.cost-row__val {
  font-weight: 700;
  color: var(--ao-text-primary);
}
.cost-row__bar-track {
  height: 8px;
  background: var(--ao-panel-border, rgba(255, 255, 255, 0.08));
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 4px;
}
.cost-row__bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}
.bar--purple {
  background: linear-gradient(90deg, #c084fc 0%, #a855f7 100%);
}
.bar--blue {
  background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%);
}
.bar--amber {
  background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%);
}
.cost-row__sub-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--ao-text-muted);
}
.cost-row__pct {
  font-weight: 600;
}
</style>
