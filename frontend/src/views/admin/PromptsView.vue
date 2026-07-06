<script setup lang="ts">

import { onMounted, ref } from 'vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import { EditPen, Plus } from '@element-plus/icons-vue'

import PageHeader from '@/components/common/PageHeader.vue'

import { confirmAction } from '@/utils/confirm'

import {

  createPrompt,

  fetchPrompts,

  setPromptEnabled,

  updatePrompt,

  fetchPromptHistory,

  rollbackPrompt,

  type PromptItem,

  type PromptHistoryItem

} from '@/api/admin'



const prompts = ref<PromptItem[]>([])

const editVisible = ref(false)

const createOpen = ref(false)

const editing = ref<{ name: string; content: string } | null>(null)

const newPrompt = ref({ name: '', content: '', type: 'custom' })

const loading = ref(false)

const historyList = ref<PromptHistoryItem[]>([])

const loadingHistory = ref(false)



onMounted(load)



async function load() {

  loading.value = true

  try {

    prompts.value = await fetchPrompts()

  } finally {

    loading.value = false

  }

}



async function openEdit(row: PromptItem) {

  editing.value = { name: row.name, content: row.content }

  editVisible.value = true

  historyList.value = []

  loadingHistory.value = true

  try {

    historyList.value = await fetchPromptHistory(row.name)

  } catch {

    // fallback

  } finally {

    loadingHistory.value = false

  }

}



async function handleRollback(ver: number) {

  if (!editing.value) return

  try {

    await ElMessageBox.confirm(`确定要将 "${editing.value.name}" 回滚至版本 v${ver} 吗？`, '版本回滚确认', {

      confirmButtonText: '确定回滚',

      cancelButtonText: '取消',

      type: 'warning'

    })

    const updated = await rollbackPrompt(editing.value.name, ver)

    editing.value.content = updated.content

    ElMessage.success('已回滚至选定版本')

    // Refresh history

    historyList.value = await fetchPromptHistory(editing.value.name)

    await load()

  } catch {

    // cancelled

  }

}



async function save() {

  if (!editing.value) return

  const ok = await confirmAction({

    message: `确定要保存 Prompt「${editing.value.name}」吗？保存后运行时立即生效。`,

    confirmButtonText: '保存'

  })

  if (!ok) return



  await updatePrompt(editing.value.name, editing.value.content)

  ElMessage.success('已保存，运行时立即生效')

  editVisible.value = false

  await load()

}



async function create() {

  if (!newPrompt.value.name || !newPrompt.value.content) {

    ElMessage.warning('请填写完整')

    return

  }

  await createPrompt(newPrompt.value)

  ElMessage.success('已创建')

  createOpen.value = false

  newPrompt.value = { name: '', content: '', type: 'custom' }

  await load()

}



async function toggleEnabled(row: PromptItem) {

  const enabling = !row.enabled

  const action = enabling ? '启用' : '停用'

  const ok = await confirmAction({

    message: `确定要${action} Prompt「${row.name}」吗？`,

    confirmButtonText: action

  })

  if (!ok) return



  await setPromptEnabled(row.name, enabling)

  row.enabled = enabling

  ElMessage.success(row.enabled ? '已启用' : '已停用')

}

</script>



<template>

  <div class="view-page">

    <PageHeader title="Prompt 管理" subtitle="系统 Prompt 模板，保存后对话运行时立即加载">

      <template #action>

        <el-button type="primary" round @click="createOpen = true"><el-icon><Plus /></el-icon> 新建</el-button>

      </template>

    </PageHeader>

    <el-card shadow="hover" class="content-card">

      <el-table

        v-loading="loading"

        :data="prompts"

        stripe

        border

        highlight-current-row

        header-cell-class-name="table-header-style"

      >

        <el-table-column prop="name" label="名称" width="140" align="center" />

        <el-table-column prop="type" label="类型" width="100" align="center" />

        <el-table-column prop="version" label="版本" width="80" align="center" />

        <el-table-column label="状态" width="90" align="center">

          <template #default="{ row }">

            <el-tag :type="row.enabled ? 'success' : 'info'" round size="small">{{ row.enabled ? '启用' : '停用' }}</el-tag>

          </template>

        </el-table-column>

        <el-table-column prop="content" label="内容预览" min-width="200" show-overflow-tooltip align="center" />

        <el-table-column label="操作" width="180" fixed="right" align="center">

          <template #default="{ row }">

            <div class="table-actions">

              <el-button size="small" class="action-btn action-btn--edit" @click="openEdit(row)">编辑</el-button>

              <el-button
                size="small"
                :class="['action-btn', row.enabled ? 'action-btn--danger' : 'action-btn--success']"
                @click="toggleEnabled(row)"
              >
                {{ row.enabled ? '停用' : '启用' }}
              </el-button>

            </div>

          </template>

        </el-table-column>

      </el-table>

    </el-card>



    <el-dialog
      v-model="editVisible"
      width="880px"
      class="ao-detail-dialog prompt-edit-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><EditPen /></el-icon>
          <span class="detail-dialog-header__title">编辑 Prompt{{ editing ? ` · ${editing.name}` : '' }}</span>
        </div>
      </template>

      <div v-if="editing" class="edit-dialog-layout">
        <div class="editor-area">
          <el-input v-model="editing.content" type="textarea" :rows="18" class="prompt-editor" />
        </div>

        <div class="history-area">
          <div class="history-header">版本历史记录</div>
          <div v-loading="loadingHistory" class="history-list">
            <div v-if="!historyList.length" class="history-empty">暂无历史修改版本</div>
            <div v-for="h in historyList" :key="h.id" class="history-item">
              <div class="history-meta">
                <span class="version-badge">v{{ h.version }}</span>
                <span class="time">{{ h.createdAt ? new Date(h.createdAt).toLocaleString('zh-CN') : '' }}</span>
              </div>
              <p class="snippet">{{ h.content.slice(0, 60) + (h.content.length > 60 ? '...' : '') }}</p>
              <div class="history-actions">
                <el-button size="small" class="action-btn action-btn--edit" @click="handleRollback(h.version)">
                  回滚至该版本
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="editVisible = false">取消</el-button>
          <el-button type="primary" class="detail-dialog-footer__submit" @click="save">保存</el-button>
        </div>
      </template>
    </el-dialog>



    <el-dialog
      v-model="createOpen"
      width="560px"
      class="ao-detail-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><Plus /></el-icon>
          <span class="detail-dialog-header__title">新建 Prompt</span>
        </div>
      </template>

      <el-form label-width="80px">

        <el-form-item label="名称"><el-input v-model="newPrompt.name" placeholder="例如 custom_assistant" /></el-form-item>

        <el-form-item label="类型">

          <el-select v-model="newPrompt.type" style="width: 100%">

            <el-option label="自定义" value="custom" />

            <el-option label="System" value="system" />

            <el-option label="Tool" value="tool" />

          </el-select>

        </el-form-item>

        <el-form-item label="内容"><el-input v-model="newPrompt.content" type="textarea" :rows="10" /></el-form-item>

      </el-form>

      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="createOpen = false">取消</el-button>
          <el-button type="primary" class="detail-dialog-footer__submit" @click="create">创建</el-button>
        </div>
      </template>
    </el-dialog>

  </div>

</template>



<style scoped>

.prompt-editor :deep(textarea) {
  font-family: ui-monospace, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ao-text-primary) !important;
}



.edit-dialog-layout {
  display: flex;
  gap: 20px;
  min-height: 420px;
}



.editor-area {

  flex: 7;

  min-width: 0;

}



.history-area {

  flex: 3;

  border-left: 1px solid var(--ao-border);

  padding-left: 20px;

  display: flex;

  flex-direction: column;

  height: 100%;

}



.history-header {

  font-size: 13px;

  font-weight: 700;

  color: var(--ao-text-primary);

  margin-bottom: 12px;

}



.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 380px;
}



.history-empty {

  font-size: 12px;

  color: var(--ao-text-muted);

  text-align: center;

  padding: 24px 0;

}



.history-item {
  padding: 12px;
  background: var(--ao-surface-muted);
  border: 1px solid var(--ao-surface-border);
  border-radius: var(--ao-radius-lg);
  transition: all 0.2s ease;
}

.history-item:hover {
  background: var(--ao-surface);
  box-shadow: var(--ao-shadow-sm);
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.version-badge {
  font-size: 10px;
  font-weight: 700;
  color: var(--theme-primary);
  background: rgba(79, 70, 229, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

.time {
  font-size: 11px;
  color: var(--ao-text-secondary);
}

.snippet {
  font-size: 12px;
  color: var(--ao-text-primary);
  margin: 4px 0 10px;
  line-height: 1.5;
  word-break: break-all;
}

.history-actions {
  display: flex;
  justify-content: flex-end;
}

.history-actions .action-btn {
  min-width: 108px;
  border: 1px solid color-mix(in srgb, var(--theme-primary) 35%, transparent) !important;
  color: var(--theme-primary) !important;
  background: var(--ao-surface) !important;
  font-weight: 600;
}

.history-actions .action-btn:hover {
  background: var(--theme-primary-muted) !important;
  border-color: var(--theme-primary) !important;
  color: var(--theme-primary) !important;
}

</style>


