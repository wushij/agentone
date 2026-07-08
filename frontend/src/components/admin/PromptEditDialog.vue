<script setup lang="ts">
import { EditPen } from '@element-plus/icons-vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePromptsAdmin } from '@/composables/usePromptsAdmin'

const {
  editVisible,
  editing,
  historyList,
  loadingHistory,
  historyPage,
  historySize,
  historyTotal,
  loadHistory,
  handleRollback,
  save
} = usePromptsAdmin()
</script>

<template>
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
        <TablePagination
          v-if="historyTotal > 0"
          v-model:page="historyPage"
          v-model:size="historySize"
          :total="historyTotal"
          @change="loadHistory"
        />
      </div>
    </div>

    <template #footer>
      <div class="detail-dialog-footer">
        <el-button class="detail-dialog-footer__cancel" @click="editVisible = false">取消</el-button>
        <el-button type="primary" class="detail-dialog-footer__submit" @click="save">保存</el-button>
      </div>
    </template>
  </el-dialog>
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
