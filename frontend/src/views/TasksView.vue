<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  Check,
  CircleCheck,
  CircleClose,
  Clock,
  Cpu,
  Document,
  Loading,
  Promotion,
  VideoPlay
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { useNotifySocket } from '@/composables/useNotifySocket'
import { useTaskStore } from '@/stores/task'
import { createTask, fetchTasks, type TaskItem } from '@/api/task'
import { formatDateTime } from '@/utils/datetime'
import { renderMarkdown } from '@/utils/markdown'
import { CopyDocument } from '@element-plus/icons-vue'

const tasks = ref<TaskItem[]>([])
const loading = ref(false)
const submitting = ref(false)
const newTaskInput = ref('')
const { page, size, total } = usePagination(10)
const taskStore = useTaskStore()
const notifySocket = useNotifySocket()

const resultModalVisible = ref(false)
const selectedTask = ref<TaskItem | null>(null)

function viewTaskResult(task: TaskItem) {
  selectedTask.value = task
  resultModalVisible.value = true
}

const selectedTaskHtml = computed(() => {
  if (!selectedTask.value?.result) return ''
  return renderMarkdown(selectedTask.value.result)
})

async function copyResultText() {
  if (!selectedTask.value?.result) return
  try {
    await navigator.clipboard.writeText(selectedTask.value.result)
    ElMessage.success('报告内容已成功复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const STATUS_LABELS: Record<string, string> = {
  pending: '排队中',
  running: '执行中',
  success: '已完成',
  failed: '已失败',
  cancelled: '已取消'
}

// 合并 DB 状态与 WS 实时进度（实时优先）
function liveProgress(task: TaskItem): number {
  return taskStore.getProgress(task.id)?.progress ?? task.progress
}
function liveStatus(task: TaskItem): string {
  return taskStore.getProgress(task.id)?.status ?? task.status
}
function liveDetail(task: TaskItem): string {
  return taskStore.getProgress(task.id)?.detail ?? ''
}

const runningCount = computed(
  () => tasks.value.filter((t) => liveStatus(t) === 'running' || liveStatus(t) === 'pending').length
)
const successCount = computed(() => tasks.value.filter((t) => liveStatus(t) === 'success').length)
const failedCount = computed(
  () => tasks.value.filter((t) => liveStatus(t) === 'failed' || liveStatus(t) === 'cancelled').length
)

const subscribedIds = new Set<string>()
function subscribeRunning() {
  const topics: string[] = []
  for (const t of tasks.value) {
    if ((t.status === 'running' || t.status === 'pending') && !subscribedIds.has(t.id)) {
      subscribedIds.add(t.id)
      topics.push(`task:${t.id}`)
    }
  }
  if (topics.length) notifySocket.subscribe(topics)
}

async function loadTasks() {
  loading.value = true
  try {
    const data = await fetchTasks({ page: page.value, size: size.value })
    tasks.value = data.records
    total.value = data.total
    subscribeRunning()
  } catch {
    tasks.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const text = newTaskInput.value.trim()
  if (!text) {
    ElMessage.warning('请输入任务描述内容')
    return
  }
  submitting.value = true
  try {
    await createTask(text)
    ElMessage.success('长任务已提交，后台自治执行中')
    newTaskInput.value = ''
    await loadTasks()
  } catch {
    ElMessage.error('任务提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

let poll: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  void loadTasks()
  poll = setInterval(() => {
    if (tasks.value.some((t) => t.status === 'running' || t.status === 'pending')) void loadTasks()
  }, 6000)
})
onUnmounted(() => {
  if (poll) clearInterval(poll)
  const topics = [...subscribedIds].map((id) => `task:${id}`)
  if (topics.length) notifySocket.unsubscribe(topics)
})

const hasTasks = computed(() => total.value > 0)
</script>

<template>
  <div class="view-page tasks-page">
    <PageHeader title="任务中心" subtitle="发起可后台自治执行的长任务，实时查看进度与产出" />

    <!-- 顶部概览卡片 -->
    <div class="metrics-grid">
      <div class="ao-card metric-card">
        <div class="metric-card__icon icon--indigo">
          <el-icon><Cpu /></el-icon>
        </div>
        <div class="metric-card__content">
          <span class="metric-card__label">总任务数</span>
          <span class="metric-card__val">{{ total }}</span>
        </div>
      </div>

      <div class="ao-card metric-card">
        <div class="metric-card__icon icon--blue" :class="{ 'is-pulsing': runningCount > 0 }">
          <el-icon><VideoPlay /></el-icon>
        </div>
        <div class="metric-card__content">
          <span class="metric-card__label">后台运行中</span>
          <span class="metric-card__val text--blue">{{ runningCount }}</span>
        </div>
      </div>

      <div class="ao-card metric-card">
        <div class="metric-card__icon icon--emerald">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="metric-card__content">
          <span class="metric-card__label">已完成产出</span>
          <span class="metric-card__val text--emerald">{{ successCount }}</span>
        </div>
      </div>

      <div class="ao-card metric-card">
        <div class="metric-card__icon icon--rose">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="metric-card__content">
          <span class="metric-card__label">异常 / 取消</span>
          <span class="metric-card__val text--rose">{{ failedCount }}</span>
        </div>
      </div>
    </div>

    <!-- 任务创建面板 -->
    <div class="ao-card task-composer-card">
      <div class="task-composer__header">
        <div class="task-composer__title">
          <el-icon class="composer-icon"><Document /></el-icon>
          <span>发起长任务</span>
        </div>
        <span class="task-composer__hint">提示: 按 <kbd>Ctrl</kbd> + <kbd>Enter</kbd> 可快捷提交</span>
      </div>

      <div class="task-composer__body">
        <el-input
          v-model="newTaskInput"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="描述一个复合任务，例如：分析上周对话数据并生成一份总结报告，或对指定知识库进行深度结构化清洗..."
          class="task-textarea"
          @keyup.enter.ctrl="handleSubmit"
        />
        <div class="task-composer__footer">
          <button
            type="button"
            class="submit-task-btn"
            :disabled="submitting || !newTaskInput.trim()"
            @click="handleSubmit"
          >
            <el-icon v-if="submitting" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Promotion /></el-icon>
            <span>{{ submitting ? '提交中...' : '提交后台任务' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 任务列表表格卡片 -->
    <div class="ao-card table-card">
      <el-table
        v-loading="loading"
        :data="tasks"
        stripe
        empty-text="暂无后台任务"
        header-cell-class-name="task-table-header"
        row-class-name="task-table-row"
        style="width: 100%"
      >
        <!-- 任务描述 -->
        <el-table-column prop="title" label="任务目标" min-width="260">
          <template #default="{ row }">
            <div class="task-title-cell">
              <span class="task-title-text" :title="row.title">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column label="执行状态" width="130" align="center">
          <template #default="{ row }">
            <div class="status-pill" :class="`status-pill--${liveStatus(row)}`">
              <span class="status-dot" />
              <span>{{ STATUS_LABELS[liveStatus(row)] ?? liveStatus(row) }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 进度 -->
        <el-table-column label="自治进度" width="220" align="center">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="liveProgress(row)"
                :status="liveStatus(row) === 'failed' ? 'exception' : liveStatus(row) === 'success' ? 'success' : undefined"
                :stroke-width="8"
                class="task-progress-bar"
              />
              <div v-if="liveDetail(row)" class="task-detail-text">
                <el-icon class="detail-icon" :class="{ 'is-loading': liveStatus(row) === 'running' }">
                  <Loading v-if="liveStatus(row) === 'running'" />
                  <Clock v-else />
                </el-icon>
                <span>{{ liveDetail(row) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 创建时间 -->
        <el-table-column label="创建时间" width="180" align="center">
          <template #default="{ row }">
            <span class="time-text">{{ formatDateTime(row.createdAt) }}</span>
          </template>
        </el-table-column>

        <!-- 结果 / 错误 -->
        <el-table-column label="执行产出 / 错误" min-width="240" align="center">
          <template #default="{ row }">
            <div
              v-if="row.error"
              class="output-box output-box--error clickable"
              title="点击查看完整异常信息"
              @click="viewTaskResult(row)"
            >
              <span class="output-text">{{ row.error }}</span>
            </div>
            <div
              v-else-if="row.result"
              class="output-box output-box--success clickable"
              title="点击查看完整产出报告"
              @click="viewTaskResult(row)"
            >
              <el-icon class="success-check"><Check /></el-icon>
              <span class="output-text">{{ row.result }}</span>
            </div>
            <span v-else class="muted-text">—</span>
          </template>
        </el-table-column>
      </el-table>

      <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="loadTasks" />

      <EmptyState
        v-if="!loading && !hasTasks"
        title="暂无后台任务"
        description="提交一个长任务，Agent 将在后台自治执行并持续推送产出结果"
      />
    </div>

    <!-- 任务产出报告详情弹窗 -->
    <el-dialog
      v-model="resultModalVisible"
      title="任务产出报告详情"
      width="680px"
      align-center
      destroy-on-close
      class="task-result-dialog"
    >
      <div v-if="selectedTask" class="result-dialog-content">
        <div class="result-dialog-meta">
          <div class="meta-item">
            <span class="meta-label">任务目标：</span>
            <span class="meta-val font-semibold">{{ selectedTask.title }}</span>
          </div>
          <div class="meta-row">
            <span class="status-pill" :class="`status-pill--${liveStatus(selectedTask)}`">
              <span class="status-dot" />
              <span>{{ STATUS_LABELS[liveStatus(selectedTask)] ?? liveStatus(selectedTask) }}</span>
            </span>
            <span class="meta-time">{{ formatDateTime(selectedTask.createdAt || '') }}</span>
          </div>
        </div>

        <div class="result-dialog-body">
          <div v-if="selectedTask.error" class="result-error-box">
            <h4>❌ 执行异常信息</h4>
            <pre>{{ selectedTask.error }}</pre>
          </div>
          <div v-else-if="selectedTaskHtml" class="chat-markdown result-markdown" v-html="selectedTaskHtml" />
          <div v-else class="result-empty">（暂无详细产出内容）</div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button
            v-if="selectedTask?.result"
            type="button"
            class="btn-copy-report"
            @click="copyResultText"
          >
            <el-icon><CopyDocument /></el-icon>
            <span>复制报告</span>
          </button>
          <button
            type="button"
            class="btn-close-dialog"
            @click="resultModalVisible = false"
          >
            关闭
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 40px;
}

/* 顶部指标网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 16px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
  transition: all 0.25s ease;
}
.metric-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.3);
}
.metric-card__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.icon--indigo {
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}
.icon--blue {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}
.icon--emerald {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}
.icon--rose {
  background: rgba(244, 63, 94, 0.15);
  color: #f43f5e;
}
.is-pulsing {
  animation: pulse-glow 2s infinite ease-in-out;
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
}
.metric-card__content {
  display: flex;
  flex-direction: column;
}
.metric-card__label {
  font-size: 12px;
  color: var(--ao-text-muted);
  margin-bottom: 2px;
}
.metric-card__val {
  font-size: 24px;
  font-weight: 800;
  color: var(--ao-text-primary);
  line-height: 1.2;
}
.text--blue { color: #3b82f6; }
.text--emerald { color: #10b981; }
.text--rose { color: #f43f5e; }

/* 任务发布卡片 */
.task-composer-card {
  padding: 20px 24px;
  border-radius: 20px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
}
.task-composer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.task-composer__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--ao-text-primary);
}
.composer-icon {
  font-size: 18px;
  color: var(--theme-primary, #6366f1);
}
.task-composer__hint {
  font-size: 12px;
  color: var(--ao-text-muted);
}
.task-composer__hint kbd {
  background: var(--ao-panel-border, rgba(255, 255, 255, 0.1));
  padding: 2px 6px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 11px;
}
.task-composer__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.task-textarea :deep(.el-textarea__inner) {
  background: var(--ao-composer-bg, rgba(255, 255, 255, 0.03));
  border-color: var(--ao-composer-border, var(--ao-panel-border));
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  color: var(--ao-text-primary);
  transition: all 0.2s ease;
}
.task-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--theme-primary, #6366f1);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}
.task-composer__footer {
  display: flex;
  justify-content: flex-end;
}
.submit-task-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 22px;
  border: none;
  border-radius: 999px;
  background: var(--ao-chat-send-gradient, linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)) !important;
  color: #ffffff !important;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.submit-task-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.48);
}
.submit-task-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 表格卡片 */
.table-card {
  padding: 20px;
  border-radius: 20px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
}
.task-title-cell {
  padding: 4px 0;
}
.task-title-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--ao-text-primary);
  line-height: 1.4;
}

/* 状态 Badge */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-pill--running {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}
.status-pill--running .status-dot {
  background: #3b82f6;
  animation: blink 1.2s infinite ease-in-out;
}
.status-pill--success {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}
.status-pill--success .status-dot {
  background: #10b981;
}
.status-pill--failed {
  background: rgba(244, 63, 94, 0.12);
  color: #f43f5e;
}
.status-pill--failed .status-dot {
  background: #f43f5e;
}
.status-pill--pending, .status-pill--cancelled {
  background: rgba(148, 163, 184, 0.12);
  color: #94a3b8;
}
.status-pill--pending .status-dot, .status-pill--cancelled .status-dot {
  background: #94a3b8;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 进度条 */
.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-progress-bar {
  width: 100%;
}
.task-detail-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  color: var(--ao-text-muted);
}
.detail-icon {
  font-size: 12px;
}

.time-text {
  font-size: 13px;
  color: var(--ao-text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

/* 产出与错误 */
.output-box {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  transition: all 0.2s ease;
}
.output-box.clickable {
  cursor: pointer;
}
.output-box.clickable:hover {
  transform: translateY(-1px);
  filter: brightness(0.96);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}
.output-box--success {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
}
.output-box--error {
  background: rgba(244, 63, 94, 0.08);
  color: #f43f5e;
}
.success-check {
  font-size: 14px;
  flex-shrink: 0;
}
.output-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.muted-text {
  color: var(--ao-text-muted);
}
</style>

<style>
.task-result-dialog .el-dialog {
  border-radius: 20px !important;
  overflow: hidden !important;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.18) !important;
}
.task-result-dialog .el-dialog__header {
  margin-bottom: 0 !important;
  padding-bottom: 10px !important;
}
.task-result-dialog .el-dialog__body {
  padding-top: 6px !important;
  padding-bottom: 10px !important;
}
.result-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-dialog-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px;
  background: var(--ao-bg-subtle, rgba(0, 0, 0, 0.03));
  border-radius: 10px;
}
.meta-item {
  font-size: 13px;
  color: var(--ao-text-primary);
}
.meta-label {
  color: var(--ao-text-muted);
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.meta-time {
  font-size: 11px;
  color: var(--ao-text-muted);
}
.result-dialog-body {
  max-height: min(520px, 62vh);
  overflow-y: auto;
  padding: 16px;
  background: var(--ao-panel-bg, #ffffff);
  border: 1px solid var(--ao-border, rgba(0, 0, 0, 0.08));
  border-radius: 14px;
}
.result-markdown {
  font-size: 14px;
  line-height: 1.6;
  color: var(--ao-text-primary);
}
.result-error-box pre {
  white-space: pre-wrap;
  word-break: break-all;
  background: rgba(244, 63, 94, 0.06);
  color: #f43f5e;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}
.result-empty {
  color: var(--ao-text-muted);
  text-align: center;
  padding: 40px 0;
}
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
.btn-copy-report {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  line-height: 1;
  box-sizing: border-box;
  margin: 0;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1 !important;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-copy-report:hover {
  background: #6366f1;
  color: #ffffff !important;
  border-color: #6366f1;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}
.btn-copy-report .el-icon {
  font-size: 14px;
  color: inherit !important;
}
.btn-close-dialog {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  line-height: 1;
  box-sizing: border-box;
  margin: 0;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid var(--ao-border, rgba(0, 0, 0, 0.12));
  background: var(--ao-panel-bg, #ffffff);
  color: var(--ao-text-secondary, #475569) !important;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-close-dialog:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--ao-text-primary, #0f172a) !important;
}
</style>
