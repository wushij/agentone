<script setup lang="ts">
import { ref } from 'vue'
import { ArrowDown, ArrowUp, Setting } from '@element-plus/icons-vue'
import type { ToolCallState } from '@/types'

defineProps<{
  tool: ToolCallState
}>()

const isOutputExpanded = ref(false)

function toggleOutput() {
  isOutputExpanded.value = !isOutputExpanded.value
}
</script>

<template>
  <div class="tool-card" :class="`tool-card--${tool.status}`">
    <div class="tool-card__header">
      <div class="tool-card__icon">
        <el-icon :size="16"><Setting /></el-icon>
      </div>
      <div class="tool-card__meta">
        <span class="tool-card__name">{{ tool.tool }}</span>
        <span class="tool-card__status">
          {{ tool.status === 'running' ? '执行中…' : tool.status === 'done' ? '已完成' : '失败' }}
          <template v-if="tool.durationMs != null"> · {{ tool.durationMs }}ms</template>
        </span>
      </div>
    </div>

    <div v-if="tool.status === 'running'" class="tool-card__skeleton">
      <el-skeleton :rows="2" animated />
    </div>

    <template v-else>
      <!-- 输入默认保留展示 -->
      <div v-if="tool.input && Object.keys(tool.input).length" class="tool-card__section">
        <span class="tool-card__label">输入</span>
        <pre class="tool-card__code">{{ JSON.stringify(tool.input, null, 2) }}</pre>
      </div>

      <!-- 输出默认折叠，支持手动展开 -->
      <div v-if="tool.output" class="tool-card__section">
        <button type="button" class="tool-card__toggle-btn" @click="toggleOutput">
          <span class="tool-card__label">输出</span>
          <span class="toggle-action-text">
            {{ isOutputExpanded ? '收起输出' : '点击展开输出' }}
            <el-icon class="toggle-arrow" :class="{ 'is-active': isOutputExpanded }">
              <ArrowDown />
            </el-icon>
          </span>
        </button>

        <Transition name="expand-output">
          <div v-show="isOutputExpanded" class="tool-card__output-wrapper">
            <pre class="tool-card__code tool-card__code--result">{{ tool.output }}</pre>
            <div class="tool-card__bottom-actions">
              <button type="button" class="tool-card__collapse-link" title="收起输出内容" @click="toggleOutput">
                <span>收起输出</span>
                <el-icon class="collapse-icon"><ArrowUp /></el-icon>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tool-card {
  border-radius: var(--ao-radius-lg);
  background: var(--ao-tool-card-bg);
  border: 1px solid var(--ao-border);
  padding: 12px 14px;
  box-shadow: var(--ao-shadow-sm);
  animation: ao-fade-in 0.3s ease both;
}

.tool-card--running {
  border-color: rgba(59, 130, 246, 0.25);
  background: var(--ao-tool-card-running-bg);
}

.tool-card--done {
  border-color: rgba(34, 197, 94, 0.2);
}

.tool-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.tool-card__icon {
  width: 32px;
  height: 32px;
  border-radius: var(--ao-radius);
  background: var(--theme-primary-muted);
  color: var(--theme-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-card__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.tool-card__name {
  font-size: 13px;
  font-weight: 700;
}

.tool-card__status {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.tool-card__section {
  margin-top: 8px;
}

.tool-card__label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--ao-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.tool-card__toggle-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 4px 0;
  border: none;
  background: transparent;
  cursor: pointer;
  margin-bottom: 4px;
}
.tool-card__toggle-btn:hover .toggle-action-text {
  color: var(--theme-primary, #6366f1);
}

.toggle-action-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ao-text-muted);
  transition: color 0.2s ease;
}

.toggle-arrow {
  font-size: 12px;
  transition: transform 0.25s ease;
}
.toggle-arrow.is-active {
  transform: rotate(180deg);
}

.tool-card__code {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--ao-radius);
  background: #1e293b;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

.tool-card__code--result {
  background: rgba(34, 197, 94, 0.08);
  color: #166534;
  border: 1px solid rgba(34, 197, 94, 0.15);
  margin-top: 4px;
}

.tool-card__output-wrapper {
  position: relative;
  margin-top: 4px;
}

.tool-card__bottom-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}

.tool-card__collapse-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--ao-text-muted, #94a3b8);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  padding: 3px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.tool-card__collapse-link:hover {
  color: var(--theme-primary, #6366f1);
  background: rgba(99, 102, 241, 0.08);
}

.collapse-icon {
  font-size: 11px;
}

.expand-output-enter-active,
.expand-output-leave-active {
  transition: all 0.25s ease;
}
.expand-output-enter-from,
.expand-output-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
