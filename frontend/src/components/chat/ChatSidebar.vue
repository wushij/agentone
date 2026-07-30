<script setup lang="ts">
import { Fold, Memo, Plus } from '@element-plus/icons-vue'
import ChatConversationList from '@/components/chat/ChatConversationList.vue'
import { useChatView } from '@/composables/useChatView'

const { chatStore, historyCollapsed, toggleHistoryCollapsed, handleNewChat } = useChatView()
</script>

<template>
  <aside class="chat-sidebar" :class="{ 'chat-sidebar--collapsed': historyCollapsed }">
    <div class="sidebar-surface">
      <!-- 展开模式：固定内布局宽度 258px，配合延迟淡入，绝无文字挤压卡顿 -->
      <div class="sidebar-expanded-content" :class="{ 'is-hidden': historyCollapsed }">
        <header class="sidebar-header">
          <div class="sidebar-heading">对话历史</div>
          <div class="sidebar-header-actions">
            <button
              type="button"
              class="sidebar-fold-btn"
              title="收起历史"
              @click="toggleHistoryCollapsed(true)"
            >
              <el-icon><Fold /></el-icon>
            </button>
            <button
              type="button"
              class="sidebar-new-btn"
              title="新建对话"
              :disabled="chatStore.creatingConversation"
              @click="handleNewChat"
            >
              <el-icon><Plus /></el-icon>
              <span>新对话</span>
            </button>
          </div>
        </header>

        <ChatConversationList />
      </div>

      <!-- 收起模式：折叠侧边栏窄条按钮 -->
      <div class="sidebar-rail" :class="{ 'is-hidden': !historyCollapsed }">
        <button
          type="button"
          class="sidebar-rail-new-btn"
          title="新建对话"
          :disabled="chatStore.creatingConversation"
          @click="handleNewChat"
        >
          <el-icon><Plus /></el-icon>
        </button>
        <button
          type="button"
          class="sidebar-rail-btn"
          title="展开历史"
          @click="toggleHistoryCollapsed(false)"
        >
          <el-icon><Memo /></el-icon>
        </button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.chat-sidebar {
  flex: 0 0 260px;
  width: 260px;
  min-width: 0;
  transition: flex-basis 0.32s cubic-bezier(0.16, 1, 0.3, 1), width 0.32s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
}
.chat-sidebar--collapsed {
  flex-basis: 62px;
  width: 62px;
}

.sidebar-surface {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  border: 1px solid var(--ao-panel-border);
  background: var(--ao-panel-bg);
  box-shadow: 0 16px 40px var(--ao-panel-shadow);
  overflow: hidden;
}

.sidebar-expanded-content {
  width: 258px;
  height: 100%;
  display: flex;
  flex-direction: column;
  opacity: 1;
  transform: translateX(0);
  transition: opacity 0.24s cubic-bezier(0.16, 1, 0.3, 1) 0.06s, transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}
.sidebar-expanded-content.is-hidden {
  opacity: 0;
  transform: translateX(-12px);
  pointer-events: none;
  visibility: hidden;
  transition: opacity 0.14s ease, transform 0.14s ease, visibility 0s 0.14s;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 12px 10px;
  border-bottom: 1px solid var(--ao-panel-border);
  flex-shrink: 0;
}

.sidebar-heading {
  font-weight: 700;
  font-size: 14px;
  color: var(--ao-text-primary);
  white-space: nowrap;
}

.sidebar-header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.sidebar-fold-btn {
  width: 34px;
  height: 34px;
  border: 1px solid var(--ao-panel-border-strong);
  border-radius: 10px;
  background: var(--ao-panel-btn-bg);
  color: var(--ao-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sidebar-fold-btn:hover {
  color: var(--theme-primary);
  border-color: rgba(99, 102, 241, 0.3);
  background: var(--theme-primary-muted);
}

.sidebar-new-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  border-radius: 999px;
  padding: 7px 14px;
  background: var(--theme-primary-gradient);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.sidebar-new-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.24);
}
.sidebar-new-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.sidebar-rail {
  position: absolute;
  top: 0;
  left: 0;
  width: 60px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 14px 10px 16px;
  box-sizing: border-box;
  opacity: 1;
  transform: translateX(0);
  transition: opacity 0.24s cubic-bezier(0.16, 1, 0.3, 1) 0.06s, transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}
.sidebar-rail.is-hidden {
  opacity: 0;
  transform: translateX(-10px);
  pointer-events: none;
  visibility: hidden;
  transition: opacity 0.14s ease, transform 0.14s ease, visibility 0s 0.14s;
}

.sidebar-rail-new-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 12px;
  background: var(--theme-primary-gradient);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}
.sidebar-rail-new-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3);
}
.sidebar-rail-new-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.sidebar-rail-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--ao-panel-border-strong);
  border-radius: 12px;
  background: var(--ao-panel-btn-bg);
  color: var(--theme-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.sidebar-rail-btn:hover {
  border-color: rgba(99, 102, 241, 0.32);
  background: var(--theme-primary-muted);
}

@media (max-width: 860px) {
  .chat-sidebar,
  .chat-sidebar--collapsed {
    flex-basis: auto;
    width: 100%;
  }
}
</style>
