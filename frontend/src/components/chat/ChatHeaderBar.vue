<script setup lang="ts">
import { Cpu, Download } from '@element-plus/icons-vue'
import { useChatView } from '@/composables/useChatView'

const {
  chatStore,
  models,
  selectedModelId,
  kbs,
  selectedKbIds,
  kbRetrieveOnly,
  setKbRetrieveOnly,
  enableTools,
  goAgentMonitor,
  handleExport
} = useChatView()

function onKbModeChange(value: string | number | boolean) {
  setKbRetrieveOnly(Boolean(value))
}
</script>

<template>
  <header class="chat-header">
    <div class="chat-header__left">
      <h2>{{ chatStore.currentConversation?.title || 'AI 对话' }}</h2>
      <span class="chat-header__meta">
        {{ models.find((m) => m.name === selectedModelId)?.modelName || '默认模型' }} ·
        {{ chatStore.totalTokens || 0 }} tokens
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
      <el-select
        v-model="selectedModelId"
        class="header-select header-model-select"
        size="small"
        placeholder="选择模型"
        :disabled="chatStore.streaming || (selectedKbIds.length > 0 && kbRetrieveOnly)"
      >
        <el-option v-for="m in models" :key="m.name" :label="m.modelName" :value="m.name" />
      </el-select>
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
</style>
