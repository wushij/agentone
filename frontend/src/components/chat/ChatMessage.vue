<script setup lang="ts">
import { computed } from 'vue'
import { CopyDocument, Delete, RefreshRight, Compass } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useStreamingMarkdown } from '@/composables/useStreamingMarkdown'
import ToolCallCard from './ToolCallCard.vue'
import ChatThinkingSteps from './ChatThinkingSteps.vue'
import BrandMark from '@/components/BrandMark.vue'
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
const showThinking = computed(
  () => (props.message.steps?.length ?? 0) > 0 && (props.message.streaming || !props.message.content)
)
const thinkingCompact = computed(() => Boolean(props.message.content))

const { html } = useStreamingMarkdown(
  computed(() => props.message.content),
  computed(() => props.message.streaming)
)

const directRetrieval = computed(() => {
  const content = props.message.content
  if (!content || props.message.role !== 'assistant') return null
  if (!content.includes('直检结果（未启用大模型总结）')) return null

  const sources = []
  const parts = content.split('### 📄 来源')
  const header = parts[0].trim()

  for (let i = 1; i < parts.length; i++) {
    const rawSource = parts[i]
    const lines = rawSource.split('\n')
    if (lines.length === 0) continue

    const titleLine = lines[0].trim()
    const fullTitle = '📄 来源 ' + titleLine.replace(/`/g, '').replace(/\*\*/g, '')

    let kbName = '默认知识库'
    const kbLine = lines.find((l) => l.includes('**知识库**：'))
    if (kbLine) {
      kbName = kbLine.replace(/> \*\*知识库\*\*：/, '').trim()
    }

    let isQa = false
    let question = ''
    let answer = ''
    const contentLines: string[] = []

    const qLine = lines.find((l) => l.includes('❓ **问**：'))
    const aLine = lines.find((l) => l.includes('💡 **答**：'))

    if (qLine && aLine) {
      isQa = true
      question = qLine.replace(/> ❓ \*\*问\*\*：/, '').trim()
      answer = aLine.replace(/> 💡 \*\*答\*\*：/, '').trim()
    } else {
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('>') && !trimmed.includes('**知识库**：')) {
          contentLines.push(trimmed.replace(/^>\s?/, ''))
        }
      }
    }

    sources.push({
      title: fullTitle,
      kbName,
      content: contentLines.join('\n').trim(),
      isQa,
      question,
      answer
    })
  }

  return {
    header,
    sources
  }
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
      <BrandMark :size="22" />
    </div>

    <div class="message-body">
      <div v-if="message.tools?.length" class="message-tools">
        <ToolCallCard v-for="tool in message.tools" :key="tool.clientId || tool.id" :tool="tool" />
      </div>

      <ChatThinkingSteps
        v-if="showThinking"
        :steps="message.steps ?? []"
        :compact="thinkingCompact"
      />

      <div v-if="isUser" class="bubble bubble--user">
        {{ message.content }}
      </div>

      <div v-else class="bubble bubble--ai" :class="{ 'bubble--retrieve': !!directRetrieval }">
        <div v-if="directRetrieval" class="direct-retrieval-container">
          <div class="retrieval-header">
            <div class="header-icon"><el-icon><Compass /></el-icon></div>
            <div class="header-text">
              <h4>知识库直接检索结果</h4>
            </div>
          </div>
          
          <div class="retrieval-sources">
            <div v-for="(source, idx) in directRetrieval.sources" :key="idx" class="source-card">
              <div class="source-meta">
                <span class="source-title">{{ source.title }}</span>
                <el-tag size="small" class="kb-tag" effect="light">{{ source.kbName }}</el-tag>
              </div>
              
              <div v-if="source.isQa" class="source-content qa-format">
                <div class="qa-item q-item">
                  <span class="qa-badge q-badge">问</span>
                  <p class="qa-text">{{ source.question }}</p>
                </div>
                <div class="qa-item a-item">
                  <span class="qa-badge a-badge">答</span>
                  <p class="qa-text">{{ source.answer }}</p>
                </div>
              </div>
              <div v-else class="source-content text-format">
                <pre class="raw-content">{{ source.content }}</pre>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="html" class="chat-markdown" v-html="html" />
        <div v-else-if="message.streaming && !message.content" class="bubble-placeholder">
          <span class="placeholder-text">正在组织回答…</span>
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
  box-shadow: var(--ao-shadow-sm);
  overflow: hidden;
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

.message-row--assistant .message-body {
  max-width: min(900px, 92%);
  width: 100%;
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
  width: 100%;
  background: var(--ao-chat-bubble-ai-bg);
  border: none;
  border-top-left-radius: 6px;
  border-radius: 18px;
  color: var(--ao-chat-bubble-ai-text);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
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
  padding: 2px 0;
  color: var(--ao-text-muted);
  font-size: 13px;
}

.placeholder-text {
  opacity: 0.85;
}

.bubble-empty {
  color: var(--ao-text-muted);
  font-style: italic;
}

/* 知识库直检卡片专属优美排版 */
.bubble--retrieve {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.direct-retrieval-container {
  width: 100%;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
  border-radius: 18px;
  padding: 20px;
  margin-top: 4px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.retrieval-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px dashed var(--ao-border);
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(79, 70, 229, 0.08);
  color: var(--theme-primary);
  font-size: 18px;
}

.header-text h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.header-text .subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--ao-text-muted);
}

.retrieval-sources {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.source-card {
  background: var(--ao-retrieval-source-bg);
  border: 1px solid var(--ao-border);
  border-radius: 12px;
  padding: 14px 16px;
  transition: all 0.2s ease;
}

.source-card:hover {
  background: var(--ao-surface);
  border-color: rgba(79, 70, 229, 0.22);
  box-shadow: 0 6px 18px rgba(79, 70, 229, 0.04);
}

.source-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.source-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.kb-tag {
  border-radius: 6px;
  background: rgba(79, 70, 229, 0.04);
  color: var(--theme-primary);
  border: 1px solid rgba(79, 70, 229, 0.08);
}

.source-content {
  font-size: 13px;
  line-height: 1.65;
  color: var(--ao-text-secondary);
}

.text-format .raw-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 13px;
  background: var(--ao-retrieval-inner-bg);
  padding: 12px 14px;
  border-radius: 8px;
  color: var(--ao-text-secondary);
  border: 1px solid var(--ao-border);
}

.qa-format {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--ao-retrieval-inner-bg);
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--ao-border);
}

.qa-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.qa-badge {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.q-badge {
  background: rgba(239, 68, 68, 0.12);
  color: var(--ao-qa-q-color);
}

.a-badge {
  background: rgba(13, 148, 136, 0.12);
  color: var(--ao-qa-a-color);
}

.qa-text {
  margin: 0;
  flex: 1;
  font-size: 13px;
}
</style>
