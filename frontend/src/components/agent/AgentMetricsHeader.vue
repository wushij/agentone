<script setup lang="ts">
defineProps<{
  metricCards: Array<{
    title: string
    value: string | number
    unit: string
    color: string
    trend: 'up' | 'flat'
    trendText: string
  }>
}>()
</script>

<template>
  <div class="metrics-grid">
    <div
      v-for="(card, index) in metricCards"
      :key="index"
      class="ao-card metric-card"
      :style="{ '--accent-color': card.color }"
    >
      <div class="metric-card__header">
        <span class="metric-card__title">{{ card.title }}</span>
        <div class="metric-card__indicator" :style="{ background: card.color }" />
      </div>
      <div class="metric-card__value-box">
        <span class="metric-card__value" :style="{ color: card.color }">{{ card.value }}</span>
        <span v-if="card.unit" class="metric-card__unit">{{ card.unit }}</span>
      </div>
      <div class="metric-card__footer">
        <span class="metric-card__trend-text">{{ card.trendText }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.metric-card {
  padding: 20px;
  border-radius: 16px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
  transition: all 0.25s ease;
}
.metric-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent-color);
}
.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.metric-card__title {
  font-size: 13px;
  color: var(--ao-text-muted);
  font-weight: 500;
}
.metric-card__indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.metric-card__value-box {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}
.metric-card__value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
}
.metric-card__unit {
  font-size: 14px;
  color: var(--ao-text-muted);
  font-weight: 600;
}
.metric-card__footer {
  font-size: 12px;
  color: var(--ao-text-muted);
}
.metric-card__trend-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}
</style>
