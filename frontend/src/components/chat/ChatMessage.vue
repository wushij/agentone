<script setup lang="ts">
import { computed } from 'vue'
import { CopyDocument, Delete, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { renderMarkdown } from '@/utils/markdown'
import ToolCallCard from './ToolCallCard.vue'
import type { ChatMessage } from '@/types'

const props = defineProps<{
  message: ChatMessage
  userInitial?: string
  streaming?: boolean
}>()

const emit = defineEmits<{
  regenerate: [messageId: string]
  delete: [messageId: string]
}>()

const isUser = computed(() => props.message.role === 'user')
const showActions = computed(() => !props.streaming && !props.message.streaming)

const html = computed(() => {
  if (isUser.value) return ''
  return renderMarkdown(props.message.content)
})

async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<template>
  <div
    class="message-row ao-fade-in"
    :class="{ 'message-row--user': isUser, 'message-row--assistant': !isUser }"
  >
    <div v-if="!isUser" class="message-avatar message-avatar--ai">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2a4 4 0 0 1 4 4v1h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z" />
        <circle cx="9" cy="13" r="1" fill="currentColor" stroke="none" />
        <circle cx="15" cy="13" r="1" fill="currentColor" stroke="none" />
      </svg>
    </div>

    <div class="message-body">
      <div v-if="message.tools?.length" class="message-tools">
        <ToolCallCard v-for="tool in message.tools" :key="tool.clientId || tool.id" :tool="tool" />
      </div>

      <div v-if="isUser" class="bubble bubble--user">
        {{ message.content }}
      </div>

      <div
        v-else
        class="bubble bubble--ai"
        :class="{ 'typing-cursor': message.streaming && message.content }"
      >
        <div v-if="html" class="chat-markdown" v-html="html" />
        <div v-else-if="message.streaming" class="bubble-placeholder">
          <span class="dot" /><span class="dot" /><span class="dot" />
        </div>
        <div v-else class="bubble-empty">（无内容）</div>
      </div>

      <div v-if="showActions" class="message-actions">
        <button type="button" class="action-chip" title="复制" @click="copyContent">
          <el-icon :size="14"><CopyDocument /></el-icon>
        </button>
        <button
          v-if="!isUser"
          type="button"
          class="action-chip"
          title="重新生成"
          @click="emit('regenerate', message.id)"
        >
          <el-icon :size="14"><RefreshRight /></el-icon>
        </button>
        <button
          type="button"
          class="action-chip action-chip--danger"
          title="删除"
          @click="emit('delete', message.id)"
        >
          <el-icon :size="14"><Delete /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message-row--user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  margin-top: 2px;
}

.message-avatar--ai {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--ao-border);
  color: var(--theme-primary);
  box-shadow: var(--ao-shadow-sm);
}

.message-avatar--user {
  background: var(--theme-primary-gradient);
  color: #fff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.message-body {
  max-width: min(720px, 78%);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-row--user .message-body {
  align-items: flex-end;
}

.message-tools {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.bubble {
  padding: 14px 18px;
  border-radius: 20px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}

.bubble--user {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #8b5cf6 100%);
  color: #fff;
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.bubble--ai {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  color: var(--ao-text-primary);
  box-shadow: 0 4px 20px rgba(100, 120, 150, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.message-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message-row:hover .message-actions {
  opacity: 1;
}

.message-row--user .message-actions {
  justify-content: flex-end;
}

.action-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--ao-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--ao-text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-chip:hover {
  color: var(--theme-primary);
  border-color: rgba(79, 70, 229, 0.25);
  background: #fff;
}

.action-chip--danger:hover {
  color: var(--ao-danger);
  border-color: rgba(239, 68, 68, 0.25);
}

.bubble-placeholder {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ao-text-muted);
  animation: bounce 1.2s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.15s; }
.dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

.bubble-empty {
  color: var(--ao-text-muted);
  font-style: italic;
}
</style>
