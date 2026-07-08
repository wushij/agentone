<script setup lang="ts">
import { useDashboard } from '@/composables/useDashboard'

const { notifyStore, recentActivity } = useDashboard()
</script>

<template>
  <section v-if="recentActivity.length" class="panel ao-card activity-panel">
    <div class="panel-header">
      <h2>最近通知</h2>
      <span class="panel-hint">{{ notifyStore.unreadCount }} 条未读</span>
    </div>

    <div class="notify-list">
      <div
        v-for="item in recentActivity"
        :key="item.id"
        class="notify-item"
        :class="{ unread: !item.read }"
        @click="notifyStore.markRead(item.id)"
      >
        <span class="notify-dot" />
        <div class="notify-body">
          <span class="notify-title">{{ item.title }}</span>
          <p class="notify-text">{{ item.body }}</p>
        </div>
        <span class="notify-time">
          {{ new Date(item.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.activity-panel {
  margin-bottom: 24px;
}

.panel {
  padding: 22px 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ao-text-primary);
}

.panel-hint {
  font-size: 12px;
  color: var(--ao-text-muted);
  font-weight: 600;
}

.notify-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.notify-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--ao-radius-lg);
  cursor: pointer;
  transition: background 0.2s ease;
}

.notify-item:hover {
  background: rgba(79, 70, 229, 0.04);
}

.notify-item.unread {
  background: rgba(79, 70, 229, 0.06);
}

.notify-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ao-text-muted);
  flex-shrink: 0;
}

.notify-item.unread .notify-dot {
  background: var(--theme-primary);
}

.notify-body {
  flex: 1;
  min-width: 0;
}

.notify-title {
  font-size: 13px;
  font-weight: 700;
}

.notify-text {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--ao-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notify-time {
  font-size: 11px;
  color: var(--ao-text-muted);
  flex-shrink: 0;
}
</style>
