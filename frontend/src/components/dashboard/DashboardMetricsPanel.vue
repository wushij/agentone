<script setup lang="ts">
import { useDashboard } from '@/composables/useDashboard'

const { stats } = useDashboard()
</script>

<template>
  <div class="dashboard-metrics-panel">
    <div class="dashboard-metrics">
      <div
        v-for="card in stats"
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
</template>

<style scoped>
@media (max-width: 1100px) {
  .dashboard-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .dashboard-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
