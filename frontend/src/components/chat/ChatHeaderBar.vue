<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, Check, Cpu, Download } from '@element-plus/icons-vue'
import { useChatView } from '@/composables/useChatView'
import type { AgentMode } from '@/types'

const {
  chatStore,
  models,
  selectedModelId,
  thinkingLevel,
  kbs,
  selectedKbIds,
  kbRetrieveOnly,
  setKbRetrieveOnly,
  enableTools,
  agentMode,
  setAgentMode,
  goAgentMonitor,
  handleExport
} = useChatView()

const popoverRef = ref()

const thinkingLevelLabel = computed(() => {
  if (thinkingLevel.value === 'fast') return '快速'
  if (thinkingLevel.value === 'extended') return '深度思考'
  return '标准'
})

const agentModeOptions: Array<{ value: AgentMode; title: string; badge: string; pillClass: string; desc: string }> = [
  {
    value: 'standard',
    title: '标准模式',
    badge: '标准',
    pillClass: 'pill--standard',
    desc: 'ReAct 自主推理与多工具调度'
  },
  {
    value: 'multi',
    title: '多 Agent 协同',
    badge: '多Agent',
    pillClass: 'pill--multi',
    desc: 'Supervisor 智能路由分派专家 Agent'
  },
  {
    value: 'plan',
    title: '计划执行模式',
    badge: '计划',
    pillClass: 'pill--plan',
    desc: '结构化拆解步骤并分阶段逐步执行'
  }
]

const currentModeInfo = computed(() => {
  return agentModeOptions.find((opt) => opt.value === agentMode.value) || agentModeOptions[0]
})

function selectAgentMode(mode: AgentMode) {
  setAgentMode(mode)
  popoverRef.value?.hide()
}

function onKbModeChange(value: string | number | boolean) {
  setKbRetrieveOnly(Boolean(value))
}
</script>

<template>
  <header class="chat-header">
    <div class="chat-header__left">
      <h2>{{ chatStore.currentConversation?.title || 'AI 对话' }}</h2>
      <span class="chat-header__meta">
        {{ models.find((m) => m.name === selectedModelId)?.modelName || '默认模型' }} · {{ thinkingLevelLabel }} ·
        {{ chatStore.streaming ? '~' : '' }}{{ chatStore.totalTokens || 0 }} tokens
        <template v-if="selectedKbIds.length">
          · {{ selectedKbIds.length }} 个知识库{{ kbRetrieveOnly ? '仅检索' : 'RAG' }}
        </template>
      </span>
    </div>
    <div class="chat-header__actions">
      <el-select
        v-model="selectedKbIds"
        class="header-select header-kb-select"
        multiple
        collapse-tags
        collapse-tags-tooltip
        :max-collapse-tags="1"
        size="small"
        placeholder="挂载知识库"
        clearable
        :multiple-limit="10"
        :disabled="chatStore.streaming"
      >
        <el-option v-for="k in kbs" :key="k.id" :label="k.name" :value="k.id" />
      </el-select>
      <el-tooltip
        v-if="selectedKbIds.length"
        content="可同时挂载最多 10 个知识库。RAG：检索后由大模型组织回答；仅检索：直接返回知识库原文，不调用对话大模型"
        placement="bottom"
      >
        <el-switch
          :model-value="kbRetrieveOnly"
          inline-prompt
          active-text="仅检索"
          inactive-text="RAG"
          :disabled="chatStore.streaming"
          style="--el-switch-on-color: #0d9488"
          @change="onKbModeChange"
        />
      </el-tooltip>
      <el-tooltip content="导出 Markdown" placement="bottom">
        <el-button text circle :disabled="!chatStore.messages.length" @click="handleExport">
          <el-icon><Download /></el-icon>
        </el-button>
      </el-tooltip>
      <el-tooltip content="Agent 工作流监控" placement="bottom">
        <el-button text circle @click="goAgentMonitor">
          <el-icon><Cpu /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- Agent 协同模式：精品胶囊下拉选单 -->
      <el-popover
        ref="popoverRef"
        placement="bottom-end"
        :width="270"
        trigger="click"
        :show-after="0"
        :hide-after="0"
        popper-class="agent-mode-dropdown-panel"
      >
        <template #reference>
          <button
            type="button"
            class="agent-mode-trigger-btn"
            :class="`btn--${agentMode}`"
            :disabled="chatStore.streaming || (selectedKbIds.length > 0 && kbRetrieveOnly)"
          >
            <span>{{ currentModeInfo.badge }}</span>
            <el-icon class="arrow-icon"><ArrowDown /></el-icon>
          </button>
        </template>

        <div class="agent-mode-dropdown-menu">
          <div class="dropdown-menu-header">Agent 协同模式</div>
          <div
            v-for="item in agentModeOptions"
            :key="item.value"
            class="dropdown-menu-item"
            :class="{ 'is-active': item.value === agentMode }"
            @click="selectAgentMode(item.value)"
          >
            <div class="item-left">
              <span class="check-slot">
                <el-icon v-if="item.value === agentMode" class="check-icon"><Check /></el-icon>
              </span>
              <div class="item-text">
                <div class="item-title-row">
                  <span class="item-title">{{ item.title }}</span>
                  <span class="mode-pill" :class="item.pillClass">{{ item.badge }}</span>
                </div>
                <span class="item-desc">{{ item.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-popover>
      <el-switch
        v-model="enableTools"
        inline-prompt
        active-text="Tool"
        inactive-text="Tool"
        :disabled="chatStore.streaming || (selectedKbIds.length > 0 && kbRetrieveOnly)"
        style="--el-switch-on-color: #4f46e5"
      />
    </div>
  </header>
</template>

<style scoped>
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--ao-panel-border);
  flex-shrink: 0;
  background: var(--ao-panel-header-bg);
}
.chat-header__left {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chat-header h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--ao-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chat-header__meta {
  font-size: 12px;
  color: var(--ao-text-muted);
}
.chat-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-select :deep(.el-select__wrapper) {
  border-radius: 10px !important;
  min-height: 28px;
  padding: 0 28px 0 10px !important;
  box-shadow: 0 0 0 1px var(--ao-border) inset !important;
}

.header-select :deep(.el-select__placeholder) {
  color: var(--ao-text-muted) !important;
  position: relative !important;
  transform: none !important;
  width: auto !important;
}

.header-kb-select {
  width: min(168px, 28vw);
}

.header-kb-select :deep(.el-select__selection:has(.el-tag)) {
  flex-wrap: nowrap;
  overflow: hidden;
}

.header-model-select {
  width: min(130px, 24vw);
}

.agent-mode-trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.agent-mode-trigger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--standard {
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.2);
}
.btn--standard:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.35);
}

.btn--multi {
  background: rgba(168, 85, 247, 0.08);
  color: #a855f7;
  border-color: rgba(168, 85, 247, 0.2);
}
.btn--multi:hover:not(:disabled) {
  background: rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.35);
}

.btn--plan {
  background: rgba(59, 130, 246, 0.08);
  color: #3b82f6;
  border-color: rgba(59, 130, 246, 0.2);
}
.btn--plan:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.35);
}

.arrow-icon {
  font-size: 11px;
  opacity: 0.75;
}

.dropdown-menu-header {
  font-size: 12px;
  font-weight: 700;
  color: var(--ao-text-muted);
  margin-bottom: 6px;
  padding: 0 4px;
}
.agent-mode-dropdown-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 2px;
}
.dropdown-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.dropdown-menu-item:hover {
  background: rgba(0, 0, 0, 0.04);
}
.dropdown-menu-item.is-active {
  background: rgba(99, 102, 241, 0.08);
}
.item-left {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}
.check-slot {
  width: 16px;
  margin-top: 2px;
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
.item-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.item-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.item-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ao-text-primary);
}
.item-desc {
  font-size: 11px;
  color: var(--ao-text-muted);
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mode-pill {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}
.pill--standard {
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}
.pill--multi {
  background: rgba(168, 85, 247, 0.12);
  color: #a855f7;
}
.pill--plan {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}
</style>

<style>
.agent-mode-dropdown-panel {
  border-radius: 16px !important;
  padding: 10px !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
  transition: opacity 0.12s cubic-bezier(0.4, 0, 0.2, 1), transform 0.12s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
</style>
