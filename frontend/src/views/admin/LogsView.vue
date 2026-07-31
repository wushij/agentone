<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, Delete, Document, Download } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import { deleteLog, exportLogs, fetchLogs, clearLogs } from '@/api/admin'

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
const { page, size, total, resetPage } = usePagination(10)

async function loadLogs() {
  loading.value = true
  try {
    const data = await fetchLogs(activeTab.value, page.value, size.value)
    logs.value = data.records
    total.value = data.total
  } catch {
    logs.value = []
    total.value = 0
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

const moduleMap: Record<string, string> = {
  system: '系统运维',
  user: '用户中心',
  auth: '认证中心',
  agent: 'Agent 工作流',
  tool: '工具调用',
  file: '文件服务',
  profile: '个人中心'
}

const typeMap: Record<string, string> = {
  update_settings: '修改系统配置',
  update_prompt: '编辑提示词模板',
  clear_logs: '清空审计日志',
  login: '用户登录',
  logout: '退出登录',
  upload: '关联文件上传',
  delete_file: '删除文件',
  update_profile: '更新个人资料',
  execution_start: '启动 Agent 工作流',
  file: '文件知识库检索',
  calculator: '数值计算工具',
  web_search: '联网检索工具',
  python_interpreter: 'Python 代码执行器',
  db_query: '数据库 SQL 查询',
  'planner:success': '任务规划器 - 完成',
  'planner:error': '任务规划器 - 异常',
  'researcher:success': '意图分析器 - 完成',
  'researcher:error': '意图分析器 - 异常',
  'tool:success': '工具执行节点 - 完成',
  'tool:error': '工具执行节点 - 异常',
  'reviewer:success': '质量审核员 - 校验通过',
  'reviewer:error': '质量审核员 - 驳回',
  'error_handler:success': '异常处理器 - 已处理',
  'unsupported:success': '未支持功能 - 降级处理'
}

const fieldKeyMap: Record<string, string> = {
  siteName: '网站名称',
  announcement: '系统公告',
  defaultModel: '默认模型',
  defaultTemperature: '温度参数',
  maxContext: '最大上下文',
  jwtExpireMinutes: '登录过期时间',
  rateLimitEnabled: '限流控制',
  rateLimitPerMinute: '频次限制',
  theme: '系统主题',
  colorMode: '亮暗模式'
}

function formatModuleLabel(mod: string): string {
  return moduleMap[mod] || mod
}

function formatTypeLabel(type: string): string {
  return typeMap[type] || type
}

function formatStatusLabel(status: string): string {
  if (status === 'success') return '成功'
  if (status === 'error' || status === 'fail' || status === 'failed') return '失败'
  if (status === 'running') return '处理中'
  return status
}

function formatDetailMessage(msg: string): string {
  if (!msg) return '—'
  if (msg.startsWith('ip=')) return `用户安全登录成功 (客户端 IP: ${msg.replace('ip=', '')})`
  if (msg.startsWith('username=')) return `成功创建新用户账号 [${msg.replace('username=', '')}]`
  if (msg === 'reviewer') return '【回答质量审核员】完成最终回答风控与质量审核，校验符合交付标准'
  if (msg === 'planner') return '【任务规划器】分析用户输入，拆解生成 Agent 执行步骤与拓扑图'
  if (msg === 'researcher') return '【意图分析器】检索知识库上下文并完成意图路由分发'
  if (msg === 'tool') return '【工具执行节点】调用底层关联工具完成功能计算'

  let result = msg
  Object.entries(fieldKeyMap).forEach(([key, cn]) => {
    const reg = new RegExp(`\\b${key}\\b`, 'g')
    result = result.replace(reg, cn)
  })
  return result
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

async function handleClearAll() {
  const tabName = tabLabels[activeTab.value] ?? activeTab.value
  const ok = await confirmAction({
    title: '清空确认',
    message: `确定清空所有「${tabName}」吗？清空后无法恢复。`,
    confirmButtonText: '确定清空',
    type: 'warning'
  })
  if (!ok) return

  try {
    await clearLogs(activeTab.value)
    ElMessage.success('清空成功')
    await loadLogs()
  } catch {
    ElMessage.error('清空失败')
  }
}

watch(activeTab, (val) => {
  localStorage.setItem('logs_active_tab', val)
  resetPage()
  void loadLogs()
})

onMounted(() => void loadLogs())
</script>

<template>
  <div class="view-page">
    <PageHeader title="日志中心" subtitle="用户 / Agent / Tool / 系统运行日志">
      <template #action>
        <el-button type="danger" plain :icon="Delete" @click="handleClearAll">清空{{ tabLabels[activeTab] || '日志' }}</el-button>
        <el-button :icon="Download" @click="handleExport">导出{{ tabLabels[activeTab] || '日志' }}</el-button>
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
        <el-table-column prop="module" label="模块" width="110" align="center">
          <template #default="{ row }">
            <span>{{ formatModuleLabel(row.module) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" min-width="150" align="center">
          <template #default="{ row }">
            <span>{{ formatTypeLabel(row.type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" round size="small">
              {{ formatStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="详情" min-width="240" align="center">
          <template #default="{ row }">
            <span class="cell-message-text">{{ formatDetailMessage(row.message) }}</span>
          </template>
        </el-table-column>
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

      <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="loadLogs" />

      <EmptyState
        v-if="!loading && total === 0"
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
            <span class="meta-item__val code-highlight">{{ formatModuleLabel(current.module) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-item__label">类型</span>
            <span class="meta-item__val">{{ formatTypeLabel(current.type) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-item__label">状态 / 耗时</span>
            <span class="meta-item__val meta-item__status-row">
              <el-tag :type="current.status === 'success' ? 'success' : 'danger'" round size="small">
                {{ formatStatusLabel(current.status) }}
              </el-tag>
              <span v-if="current.durationMs != null" class="duration-badge">
                ⚡ {{ current.durationMs }} ms
              </span>
            </span>
          </div>
        </div>

        <div class="detail-content-block">
          <div class="detail-content-block__label">详情</div>
          <div class="detail-content-block__body">{{ formatDetailMessage(current.message) }}</div>
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

.cell-message-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.meta-item__status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.08);
  color: var(--theme-primary, #6366f1);
  font-size: 11px;
  font-weight: 600;
}
</style>
