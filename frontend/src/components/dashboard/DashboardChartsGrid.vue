<script setup lang="ts">
import { useDashboard } from '@/composables/useDashboard'

const { weeklyData, maxWeekly, tokenPercent } = useDashboard()
</script>

<template>
  <section class="charts-grid">
    <div class="panel ao-card chart-panel">
      <div class="panel-header">
        <h2>近 7 日对话趋势</h2>
      </div>
      <div v-if="weeklyData.length" class="bar-chart">
        <div v-for="bar in weeklyData" :key="bar.date" class="bar-col">
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{ height: `${Math.max(8, (bar.count / maxWeekly) * 100)}%` }"
            />
          </div>
          <span class="bar-value">{{ bar.count }}</span>
          <span class="bar-label">{{ bar.date }}</span>
        </div>
      </div>
      <div v-else class="chart-empty">暂无数据</div>
    </div>

    <div class="panel ao-card chart-panel">
      <div class="panel-header">
        <h2>Token 使用占比</h2>
      </div>
      <div class="donut-wrap">
        <svg viewBox="0 0 120 120" class="donut-chart">
          <circle cx="60" cy="60" r="48" fill="none" stroke="rgba(148,163,184,0.15)" stroke-width="14" />
          <circle
            cx="60"
            cy="60"
            r="48"
            fill="none"
            stroke="url(#donut-grad)"
            stroke-width="14"
            stroke-linecap="round"
            :stroke-dasharray="`${tokenPercent * 3.01} 301`"
            transform="rotate(-90 60 60)"
          />
          <defs>
            <linearGradient id="donut-grad" x1="0" y1="0" x2="1" y2="1">
              <stop stop-color="#4f46e5" />
              <stop offset="1" stop-color="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
        <div class="donut-center">
          <span class="donut-pct">{{ tokenPercent }}%</span>
          <span class="donut-sub">已使用</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.charts-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  margin-top: 16px;
  margin-bottom: 16px;
}

.chart-panel {
  padding: 22px 24px;
  min-height: 220px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  height: 160px;
  padding-top: 8px;
}

.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  height: 100%;
}

.bar-track {
  flex: 1;
  width: 100%;
  max-width: 48px;
  display: flex;
  align-items: flex-end;
  background: rgba(79, 70, 229, 0.06);
  border-radius: var(--ao-radius) var(--ao-radius) 0 0;
}

.bar-fill {
  width: 100%;
  border-radius: var(--ao-radius) var(--ao-radius) 0 0;
  background: var(--theme-primary-gradient);
  transition: height 0.6s ease;
  min-height: 8px;
}

.bar-value {
  font-size: 11px;
  font-weight: 700;
  color: var(--theme-primary);
}

.bar-label {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.donut-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 160px;
}

.donut-chart {
  width: 140px;
  height: 140px;
}

.donut-center {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.donut-pct {
  font-size: 26px;
  font-weight: 800;
  color: var(--ao-text-primary);
}

.donut-sub {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 140px;
  color: var(--ao-text-muted);
  font-size: 13px;
}

@media (max-width: 1100px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
