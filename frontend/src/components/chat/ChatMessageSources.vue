<script setup lang="ts">
import { Compass, Document } from '@element-plus/icons-vue'
import type { MessageSource } from '@/types'

defineProps<{
  directRetrieval?: {
    header: string
    sources: Array<{
      title: string
      kbName: string
      content: string
      isQa: boolean
      question: string
      answer: string
    }>
  } | null
  sources?: MessageSource[]
}>()
</script>

<template>
  <div>
    <!-- Direct Retrieval View -->
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

    <!-- Citations Bar -->
    <div v-if="sources?.length" class="message-citations">
      <span class="citations-label">
        <el-icon :size="13"><Document /></el-icon>
        引用来源
      </span>
      <el-popover
        v-for="src in sources"
        :key="src.index"
        placement="top"
        :width="320"
        trigger="click"
        popper-class="citation-popover"
      >
        <template #reference>
          <button type="button" class="citation-tag">
            <span class="citation-num">[{{ src.index }}]</span>
            <span class="citation-name">{{ src.fileName || '知识点' }}</span>
          </button>
        </template>
        <div class="citation-popover-content">
          <div class="citation-header">
            <span class="citation-kb">{{ src.kbName || '默认知识库' }}</span>
            <span v-if="src.score" class="citation-score">匹配度 {{ Math.round(src.score * 100) }}%</span>
          </div>
          <p v-if="src.text" class="citation-text">{{ src.text }}</p>
        </div>
      </el-popover>
    </div>
  </div>
</template>

<style scoped>
.direct-retrieval-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.retrieval-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  color: var(--theme-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.retrieval-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.retrieval-sources {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.source-card {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--ao-panel-border);
}
.source-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.source-title {
  font-size: 13px;
  font-weight: 600;
}
.kb-tag {
  border-radius: 6px;
}
.raw-content {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ao-text-secondary);
}
.qa-format {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.qa-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.qa-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.q-badge {
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}
.a-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.qa-text {
  margin: 0;
  font-size: 13px;
}
.message-citations {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.citations-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--ao-text-muted);
}
.citation-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--ao-panel-border);
  font-size: 11px;
  color: var(--ao-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.citation-tag:hover {
  background: rgba(99, 102, 241, 0.15);
  color: var(--theme-primary);
}
</style>
