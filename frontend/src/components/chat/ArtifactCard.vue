<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, DataAnalysis, Cpu, Files } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { renderMarkdown } from '@/utils/markdown'
import type { MessageArtifact } from '@/types'

const props = defineProps<{ artifact: MessageArtifact }>()
const dialogVisible = ref(false)

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    markdown: '文档', code: '代码', chart: '图表', html: 'HTML',
    csv: '表格', excel: '表格', image: '图片', mermaid: '流程图', pdf: 'PDF'
  }
  return map[props.artifact.type] || props.artifact.type
})

const typeIcon = computed(() => {
  if (props.artifact.type === 'chart') return DataAnalysis
  if (props.artifact.type === 'code') return Cpu
  if (props.artifact.type === 'csv' || props.artifact.type === 'excel') return Files
  return Document
})

const prettyContent = computed(() => {
  const a = props.artifact
  if (a.type === 'chart') {
    try {
      return '```json\n' + JSON.stringify(JSON.parse(a.content), null, 2) + '\n```'
    } catch {
      return a.content
    }
  }
  if (a.type === 'code') {
    return '```' + (a.language || '') + '\n' + a.content + '\n```'
  }
  return a.content
})

const renderedContent = computed(() => renderMarkdown(prettyContent.value))

async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.artifact.content)
    ElMessage.success('已复制产物内容')
  } catch {
    ElMessage.error('复制失败')
  }
}

function download() {
  const ext = props.artifact.type === 'code' ? props.artifact.language || 'txt'
    : props.artifact.type === 'chart' ? 'json' : 'md'
  const blob = new Blob([props.artifact.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.artifact.title || 'artifact'}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="artifact-card" @click="dialogVisible = true">
    <el-icon class="artifact-icon" :size="18"><component :is="typeIcon" /></el-icon>
    <div class="artifact-meta">
      <span class="artifact-title">{{ artifact.title }}</span>
      <el-tag size="small" effect="light" round>{{ typeLabel }}</el-tag>
    </div>
    <span class="artifact-open">查看</span>
  </div>

  <el-dialog
    v-model="dialogVisible"
    :title="artifact.title"
    width="720px"
    append-to-body
    destroy-on-close
    class="ao-detail-dialog artifact-dialog"
  >
    <div class="artifact-body chat-markdown" v-html="renderedContent" />
    <template #footer>
      <el-button @click="copyContent">复制</el-button>
      <el-button type="primary" @click="download">下载</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.artifact-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--ao-border, rgba(148, 163, 184, 0.25));
  border-radius: 10px;
  background: var(--ao-card-bg, rgba(148, 163, 184, 0.06));
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.artifact-card:hover {
  border-color: var(--theme-primary, #4f46e5);
  background: color-mix(in srgb, var(--theme-primary, #4f46e5) 8%, transparent);
}
.artifact-icon {
  color: var(--theme-primary, #4f46e5);
}
.artifact-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.artifact-title {
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.artifact-open {
  font-size: 12px;
  color: var(--theme-primary, #4f46e5);
}
.artifact-body {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
