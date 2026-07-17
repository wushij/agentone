<script setup lang="ts">
import { Delete, Search, Box, FolderOpened } from '@element-plus/icons-vue'
import { useChatView } from '@/composables/useChatView'

const {
  chatStore,
  historyExpanded,
  currentFilter,
  isBatchMode,
  selectedIds,
  displayedConversations,
  visibleConversations,
  hiddenSessionCount,
  isAllSelected,
  toggleBatchMode,
  toggleSelectAll,
  handleBatchDelete,
  handleToggleArchive,
  selectChat,
  handleDelete,
  formatSessionTime
} = useChatView()
</script>

<template>
  <div class="sidebar-body">
    <div class="sidebar-search-wrap">
      <el-icon class="sidebar-search-icon"><Search /></el-icon>
      <input
        v-model="chatStore.searchQuery"
        type="text"
        placeholder="搜索会话…"
        class="sidebar-search-input"
      />
    </div>

    <div class="sidebar-tabs">
      <div class="tabs-left">
        <button
          type="button"
          class="sidebar-tab"
          :class="{ active: currentFilter === 'active' }"
          @click="currentFilter = 'active'"
        >
          活跃
        </button>
        <button
          type="button"
          class="sidebar-tab"
          :class="{ active: currentFilter === 'archived' }"
          @click="currentFilter = 'archived'"
        >
          已归档
        </button>
      </div>
      <button
        type="button"
        class="sidebar-tab-batch-toggle"
        :class="{ active: isBatchMode }"
        @click="toggleBatchMode"
      >
        {{ isBatchMode ? '取消' : '批量' }}
      </button>
    </div>

    <div class="conv-list">
      <div v-if="chatStore.loadingConversations" class="conv-loading">
        <el-skeleton :rows="4" animated />
      </div>
      <template v-else-if="displayedConversations.length">
        <div v-for="conv in visibleConversations" :key="conv.id" class="conv-item-wrap">
          <div
            class="conv-item"
            :class="{ active: chatStore.currentId === conv.id, 'batch-padding': isBatchMode }"
            @click="isBatchMode ? null : selectChat(conv.id)"
          >
            <el-checkbox-group v-if="isBatchMode" v-model="selectedIds" class="batch-checkbox-wrap">
              <el-checkbox :value="conv.id" @click.stop="" />
            </el-checkbox-group>
            <div class="conv-item-main">
              <span class="conv-title">
                {{ conv.title }}
                <span v-if="chatStore.isConversationStreaming(conv.id)" class="conv-streaming-badge">生成中</span>
              </span>
              <span class="conv-sub">{{ formatSessionTime(conv.updatedAt) }}</span>
            </div>
            <div v-if="!isBatchMode" class="conv-actions-overlay">
              <button
                type="button"
                class="conv-action-btn"
                :title="conv.isArchived ? '取消归档' : '归档会话'"
                @click.stop="handleToggleArchive(conv)"
              >
                <el-icon :size="13">
                  <FolderOpened v-if="conv.isArchived" />
                  <Box v-else />
                </el-icon>
              </button>
              <button
                type="button"
                class="conv-action-btn conv-action-btn--delete"
                title="删除会话"
                @click.stop="handleDelete(conv.id, $event)"
              >
                <el-icon :size="13"><Delete /></el-icon>
              </button>
            </div>
          </div>
        </div>
        <button
          v-if="hiddenSessionCount > 0"
          type="button"
          class="history-load-more"
          @click="historyExpanded = !historyExpanded"
        >
          {{ historyExpanded ? '收起' : `更多（${hiddenSessionCount}）` }}
        </button>
      </template>
      <div v-else class="conv-empty">
        <p>暂无会话</p>
        <span>{{ currentFilter === 'archived' ? '无归档的会话记录' : '点击上方按钮开始新对话' }}</span>
      </div>
    </div>

    <div v-if="isBatchMode" class="batch-action-bar">
      <div class="batch-action-left">
        <button
          type="button"
          class="batch-pill-btn"
          :disabled="!displayedConversations.length"
          @click="toggleSelectAll"
        >
          {{ isAllSelected ? '取消全选' : '全选' }}
        </button>
        <span class="batch-selected-count">已选 {{ selectedIds.length }} 个</span>
      </div>
      <button
        type="button"
        class="batch-pill-btn batch-pill-btn--danger"
        :disabled="!selectedIds.length"
        @click="handleBatchDelete"
      >
        删除已选
      </button>
    </div>
  </div>
</template>

<style scoped>
.sidebar-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-search-wrap {
  position: relative;
  padding: 10px 10px 0;
}
.sidebar-search-icon {
  position: absolute;
  left: 22px;
  top: 50%;
  transform: translateY(-20%);
  color: var(--ao-text-muted);
  font-size: 14px;
}
.sidebar-search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 34px;
  border: 1px solid var(--ao-panel-border);
  border-radius: 999px;
  background: var(--ao-panel-input-bg);
  font-size: 13px;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
  color: var(--ao-text-primary);
}
.sidebar-search-input:focus {
  border-color: rgba(79, 70, 229, 0.35);
  background: var(--ao-panel-bg);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08);
}

.sidebar-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 4px;
  gap: 8px;
}
.tabs-left {
  display: flex;
  gap: 6px;
}
.sidebar-tab {
  background: var(--ao-panel-btn-bg);
  border: 1px solid var(--ao-panel-border);
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  cursor: pointer;
  padding: 4px 14px;
  border-radius: 999px;
  transition: all 0.2s ease;
}
.sidebar-tab:hover {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 30%, transparent);
  background: var(--theme-primary-muted);
}
.sidebar-tab.active {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}
.sidebar-tab-batch-toggle {
  background: var(--ao-panel-btn-bg);
  border: 1px solid var(--ao-panel-border);
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-secondary);
  cursor: pointer;
  padding: 4px 14px;
  border-radius: 999px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.sidebar-tab-batch-toggle:hover,
.sidebar-tab-batch-toggle.active {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 10px 10px;
  scrollbar-width: none;
}
.conv-list::-webkit-scrollbar {
  display: none;
}

.conv-loading,
.conv-empty {
  padding: 24px 12px;
  text-align: center;
  color: var(--ao-text-muted);
  font-size: 13px;
}
.conv-empty p {
  margin: 0 0 4px;
  font-weight: 600;
}
.conv-empty span {
  font-size: 11px;
}

.history-load-more {
  width: 100%;
  margin-top: 4px;
  padding: 8px 10px;
  border: 1px dashed var(--ao-panel-border);
  border-radius: 12px;
  background: transparent;
  color: var(--ao-text-muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.history-load-more:hover {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}

.conv-item-wrap {
  margin-bottom: 6px;
}
.conv-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 36px 9px 10px;
  border: 1px solid var(--ao-conv-border);
  border-radius: 14px;
  background: var(--ao-conv-bg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  box-sizing: border-box;
}
.conv-item:hover,
.conv-item.active {
  border-color: rgba(99, 102, 241, 0.35);
  background: var(--ao-conv-active-bg);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.08);
}
.conv-item.batch-padding {
  padding-left: 36px;
}

.batch-checkbox-wrap {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.conv-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.conv-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--ao-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-streaming-badge {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  color: var(--theme-primary);
  background: var(--theme-primary-muted);
  padding: 1px 6px;
  border-radius: 999px;
}
.conv-sub {
  font-size: 11px;
  color: var(--ao-text-muted);
}

.conv-actions-overlay {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  padding-right: 8px;
  padding-left: 20px;
  background: var(--ao-conv-overlay-bg);
  border-top-right-radius: 14px;
  border-bottom-right-radius: 14px;
  opacity: 0;
  transition: opacity 0.18s ease;
}
.conv-item:hover .conv-actions-overlay,
.conv-item.active .conv-actions-overlay {
  opacity: 1;
}

.conv-action-btn {
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 999px;
  background: var(--ao-conv-action-bg);
  color: var(--ao-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.18s ease;
}
.conv-action-btn:hover {
  color: var(--theme-primary);
  background: var(--ao-panel-bg);
}
.conv-action-btn--delete:hover {
  color: #ef4444;
}

.batch-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-top: 1px solid var(--ao-panel-border);
  flex-shrink: 0;
}
.batch-action-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.batch-pill-btn {
  height: 28px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-btn-bg);
  color: var(--ao-text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.batch-pill-btn:hover:not(:disabled) {
  color: var(--theme-primary);
  border-color: color-mix(in srgb, var(--theme-primary) 35%, transparent);
  background: var(--theme-primary-muted);
}
.batch-pill-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.batch-pill-btn--danger {
  border-color: rgba(239, 68, 68, 0.35);
  color: #ef4444;
  background: rgba(239, 68, 68, 0.06);
}
.batch-pill-btn--danger:hover:not(:disabled) {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}
.batch-selected-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--ao-text-muted);
}
</style>
