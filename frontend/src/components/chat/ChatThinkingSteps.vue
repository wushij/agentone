<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue'
import type { WorkflowStep } from '@/types'

const props = defineProps<{
  steps: WorkflowStep[]
  compact?: boolean
}>()

const visibleSteps = computed(() => props.steps.filter((s) => s.status !== 'pending'))

function formatMs(ms?: number) {
  if (!ms) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
</script>

<template>
  <div class="thinking-panel" :class="{ 'thinking-panel--compact': compact }">
    <div class="thinking-panel__title">思考过程</div>
    <ul class="thinking-steps">
      <li
        v-for="step in visibleSteps"
        :key="step.node"
        class="thinking-step"
        :class="`thinking-step--${step.status}`"
      >
        <span class="thinking-step__icon">
          <el-icon v-if="step.status === 'running'" class="is-loading"><Loading /></el-icon>
          <el-icon v-else-if="step.status === 'success'" class="ok"><CircleCheck /></el-icon>
          <el-icon v-else-if="step.status === 'error'" class="err"><CircleClose /></el-icon>
        </span>
        <span class="thinking-step__label">
          {{ step.label }}
          <span v-if="step.tool" class="thinking-step__tool">· {{ step.tool }}</span>
        </span>
        <span v-if="step.elapsedMs" class="thinking-step__time">{{ formatMs(step.elapsedMs) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.thinking-panel {
  width: 100%;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--ao-thinking-panel-bg);
  border: 1px solid rgba(99, 102, 241, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.thinking-panel--compact {
  padding: 10px 12px;
}

.thinking-panel__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--ao-text-muted);
  margin-bottom: 8px;
  letter-spacing: 0.02em;
}

.thinking-steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ao-text-primary);
}

.thinking-step__icon {
  width: 16px;
  height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--theme-primary);
}

.thinking-step__icon .ok {
  color: #10b981;
}

.thinking-step__icon .err {
  color: #ef4444;
}

.thinking-step--running .thinking-step__label {
  color: var(--theme-primary);
  font-weight: 600;
}

.thinking-step__label {
  flex: 1;
  min-width: 0;
}

.thinking-step__tool {
  color: var(--ao-text-muted);
  font-weight: 500;
}

.thinking-step__time {
  font-size: 11px;
  color: var(--ao-text-muted);
  flex-shrink: 0;
}
</style>
