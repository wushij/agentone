<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Document, Download } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import { deleteLog, exportLogs, fetchLogs } from '@/api/admin'

interface LogRow {
  id: number
  time: string
  module: string
  type: string
  status: string
  message: string
  durationMs?: number
}

const activeTab = ref(localStorage.getItem('logs_active_tab') || 'user')
const logs = ref<LogRow[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const current = ref<LogRow | null>(null)

async function loadLogs() {
  loading.value = true
  try {
    const data = await fetchLogs(activeTab.value)
    logs.value = data.items ?? []
  } catch {
    logs.value = []
  } finally {
    loading.value = false
  }
}

const tabLabels: Record<string, string> = {
  user: '用户日志',
  agent: 'Agent 日志',
  tool: 'Tool 日志',
  system: '系统日志'
}

async function handleExport() {
  const tabName = tabLabels[activeTab.value] ?? activeTab.value
  const ok = await confirmAction({
    title: '导出确认',
    message: `确定导出「${tabName}」吗？将下载为文本文件。`,
    confirmButtonText: '导出'
  })
  if (!ok) return

  try {
    const content = await exportLogs(activeTab.value)
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${activeTab.value}.txt`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

function openDetail(row: LogRow) {
  current.value = row
  detailVisible.value = true
}

function formatLogText(row: LogRow) {
  const duration = row.durationMs != null ? ` (${row.durationMs}ms)` : ''
  return `[${row.time}] ${row.module}/${row.type} (${row.status})${duration}\n${row.message || '—'}`
}

async function copyLog(row: LogRow) {
  try {
    await navigator.clipboard.writeText(formatLogText(row))
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleDelete(row: LogRow) {
  const ok = await confirmDelete('确定删除这条日志吗？删除后无法恢复。')
  if (!ok) return
  try {
    await deleteLog(row.id, activeTab.value)
    ElMessage.success('删除成功')
    if (current.value?.id === row.id) {
      detailVisible.value = false
      current.value = null
    }
    await loadLogs()
  } catch {
    ElMessage.error('删除失败')
  }
}

watch(activeTab, (val) => {
  localStorage.setItem('logs_active_tab', val)
  void loadLogs()
})

onMounted(() => void loadLogs())
</script>

<template>
  <div class="view-page">
    <PageHeader title="日志中心" subtitle="用户 / Agent / Tool / 系统运行日志">
      <template #action>
        <el-button :icon="Download" @click="handleExport">导出日志</el-button>
      </template>
    </PageHeader>

    <el-card shadow="hover" class="content-card logs-card">
      <el-tabs v-model="activeTab" class="logs-tabs">
        <el-tab-pane label="用户日志" name="user" />
        <el-tab-pane label="Agent 日志" name="agent" />
        <el-tab-pane label="Tool 日志" name="tool" />
        <el-tab-pane label="系统日志" name="system" />
      </el-tabs>

      <el-table
        v-loading="loading"
        :data="logs"
        stripe
        border
        highlight-current-row
        empty-text="暂无日志"
        header-cell-class-name="table-header-style"
        style="width: 100%"
      >
        <el-table-column
          prop="time"
          label="时间"
          width="180"
          align="center"
          class-name="col-time"
          label-class-name="col-time"
        />
        <el-table-column prop="module" label="模块" width="100" align="center" />
        <el-table-column prop="type" label="类型" min-width="140" show-overflow-tooltip align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" round size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="详情" min-width="240" show-overflow-tooltip align="center" />
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" class="action-btn action-btn--view" @click="openDetail(row)">详情</el-button>
              <el-button size="small" class="action-btn action-btn--neutral" :icon="CopyDocument" @click="copyLog(row)">
                复制
              </el-button>
              <el-button size="small" class="action-btn action-btn--danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <EmptyState
        v-if="!loading && !logs.length"
        title="暂无日志"
        :description="activeTab === 'tool' ? 'Tool 调用后将在此记录' : '该类型日志将在有操作后显示'"
      />
    </el-card>

    <el-dialog
      v-model="detailVisible"
      width="560px"
      class="ao-detail-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><Document /></el-icon>
          <span class="detail-dialog-header__title">日志详情</span>
        </div>
      </template>

      <template v-if="current">
        <div class="detail-meta-grid">
          <div class="meta-item">
            <span class="meta-item__label">时间</span>
            <span class="meta-item__val">{{ current.time }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-item__label">模块</span>
            <span class="meta-item__val code-highlight">{{ current.module }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-item__label">类型</span>
            <span class="meta-item__val">{{ current.type }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-item__label">状态</span>
            <span class="meta-item__val">
              <el-tag :type="current.status === 'success' ? 'success' : 'danger'" round size="small">
                {{ current.status }}
              </el-tag>
            </span>
          </div>
          <div v-if="current.durationMs != null" class="meta-item">
            <span class="meta-item__label">耗时</span>
            <span class="meta-item__val">{{ current.durationMs }} ms</span>
          </div>
        </div>

        <div class="detail-content-block">
          <div class="detail-content-block__label">详情</div>
          <div class="detail-content-block__body">{{ current.message || '—' }}</div>
        </div>
      </template>

      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="detailVisible = false">关闭</el-button>
          <el-button
            v-if="current"
            type="primary"
            class="detail-dialog-footer__submit"
            :icon="CopyDocument"
            @click="copyLog(current)"
          >
            复制全文
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.logs-card :deep(.el-card__body) {
  padding: 0 !important;
}

.logs-tabs {
  padding: 0 16px;
}
</style>
