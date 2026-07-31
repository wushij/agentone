<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, Check, Cpu } from '@element-plus/icons-vue'
import { parseModelMeta } from '@/utils/model_short_name'
import type { AvailableModel, ThinkingLevel } from '@/types'

export type { ThinkingLevel }

const props = withDefaults(
  defineProps<{
    models: AvailableModel[]
    modelValue: string
    disabled?: boolean
    thinkingLevel?: ThinkingLevel
  }>(),
  {
    disabled: false,
    thinkingLevel: 'standard'
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:thinkingLevel', value: ThinkingLevel): void
}>()

const popoverRef = ref()

// 格式化模型列表，包含模型全称、简称与描述
const formattedModels = computed(() => {
  return props.models.map((m) => {
    const meta = parseModelMeta(m.name, m.modelName)
    const fullName = m.modelName || m.name

    return {
      ...m,
      fullName,
      shortName: meta.shortName,
      description: meta.description
    }
  })
})

const activeModel = computed(() => {
  return formattedModels.value.find((m) => m.name === props.modelValue) || formattedModels.value[0]
})

const activeShortName = computed(() => {
  if (!activeModel.value) return 'Flash'
  return activeModel.value.shortName
})

function selectModel(name: string) {
  emit('update:modelValue', name)
  popoverRef.value?.hide()
}

function setThinking(level: ThinkingLevel) {
  emit('update:thinkingLevel', level)
  popoverRef.value?.hide()
}
</script>

<template>
  <el-popover
    ref="popoverRef"
    placement="top-start"
    :width="280"
    trigger="click"
    :show-after="0"
    :hide-after="0"
    popper-class="gemini-model-popover"
    :disabled="disabled"
  >
    <template #reference>
      <button
        type="button"
        class="model-capsule-trigger"
        :class="{ 'is-disabled': disabled }"
        :disabled="disabled"
      >
        <span class="model-name-text">{{ activeShortName }}</span>
        <el-icon class="arrow-icon"><ArrowDown /></el-icon>
      </button>
    </template>

    <div class="model-popover-panel">
      <!-- 模型列表：显示模型全称 + 简称徽章 + 描述 -->
      <div class="model-list">
        <div
          v-for="m in formattedModels"
          :key="m.name"
          class="model-item"
          :class="{ 'is-active': m.name === modelValue }"
          @click="selectModel(m.name)"
        >
          <div class="model-item__left">
            <span class="check-slot">
              <el-icon v-if="m.name === modelValue" class="check-icon"><Check /></el-icon>
            </span>
            <div class="model-item__text">
              <div class="model-item__header-row">
                <span class="model-item__fullName">{{ m.fullName }}</span>
                <span class="model-item__shortBadge">{{ m.shortName }}</span>
              </div>
              <span class="model-item__desc">
                {{ m.description }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 扩展思考模块 -->
      <div class="thinking-section">
        <div class="thinking-header">
          <el-icon><Cpu /></el-icon>
          <span>扩展思考 (Reasoning)</span>
        </div>
        <div class="thinking-options">
          <button
            type="button"
            class="thinking-btn"
            :class="{ 'is-active': (thinkingLevel ?? 'standard') === 'fast' }"
            @click="setThinking('fast')"
          >
            快速
          </button>
          <button
            type="button"
            class="thinking-btn"
            :class="{ 'is-active': (thinkingLevel ?? 'standard') === 'standard' }"
            @click="setThinking('standard')"
          >
            标准
          </button>
          <button
            type="button"
            class="thinking-btn"
            :class="{ 'is-active': (thinkingLevel ?? 'standard') === 'extended' }"
            @click="setThinking('extended')"
          >
            深度思考
          </button>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<style scoped>
.model-capsule-trigger {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: var(--ao-text-primary, #1e293b);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.model-capsule-trigger:hover:not(.is-disabled) {
  background: var(--ao-panel-border, rgba(0, 0, 0, 0.06));
}
.model-capsule-trigger.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.arrow-icon {
  font-size: 11px;
  color: var(--ao-text-muted, #94a3b8);
  transition: transform 0.2s ease;
}

.model-popover-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 2px;
}
.model-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.model-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.model-item:hover {
  background: var(--ao-panel-border, rgba(0, 0, 0, 0.05));
}
.model-item.is-active {
  background: rgba(99, 102, 241, 0.08);
}
.model-item__left {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.check-slot {
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.check-icon {
  font-size: 14px;
  color: var(--theme-primary, #6366f1);
  font-weight: bold;
}
.model-item__text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.model-item__header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.model-item__fullName {
  font-size: 13px;
  font-weight: 700;
  color: var(--ao-text-primary);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.model-item__shortBadge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.12);
  color: var(--theme-primary, #6366f1);
  white-space: nowrap;
  flex-shrink: 0;
}
.model-item__desc {
  font-size: 11px;
  color: var(--ao-text-muted);
  margin-top: 3px;
}

/* 扩展思考 */
.thinking-section {
  padding-top: 10px;
  border-top: 1px dashed var(--ao-panel-border, rgba(0, 0, 0, 0.08));
}
.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-muted);
  margin-bottom: 8px;
}
.thinking-options {
  display: flex;
  gap: 6px;
}
.thinking-btn {
  flex: 1;
  height: 28px;
  border: 1px solid var(--ao-panel-border, rgba(0, 0, 0, 0.1));
  border-radius: 999px;
  background: transparent;
  font-size: 11px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.thinking-btn:hover {
  background: rgba(99, 102, 241, 0.05);
}
.thinking-btn.is-active {
  background: var(--theme-primary, #6366f1);
  color: #ffffff;
  border-color: var(--theme-primary, #6366f1);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
}
</style>

<style>
.gemini-model-popover {
  border-radius: 16px !important;
  padding: 10px !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
  transition: opacity 0.12s cubic-bezier(0.4, 0, 0.2, 1), transform 0.12s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
</style>
